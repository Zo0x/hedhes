from app import db, tmdb
from datetime import datetime, timedelta
import sqlalchemy.types as types
import errno
import json
import os


class JsonType(types.TypeDecorator):
    impl = types.String

    def process_literal_param(self, value, dialect):
        return json.dumps(value)

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)

    def copy(self, **kw):
        return JsonType(self.impl.length)


class CRUD:
    def save(self):
        if self.id is None:
            db.session.add(self)
        return db.session.commit()

    def destroy(self):
        db.session.delete(self)
        return db.session.commit()

    @classmethod
    def factory(cls, **kwargs):
        return db.session.query(cls).filter_by(**kwargs).first()

    @classmethod
    def collection(cls, **kwargs):
        return db.session.query(cls).filter_by(**kwargs).all()


class Settings(db.Model, CRUD):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, index=True)
    str_value = db.Column(db.String(255), index=True)
    value = None
    name = db.Column(db.String(255), index=True)
    type = db.Column(db.String(255), index=True, default='string')
    html_type = db.Column(db.String(255), index=True, default='text')
    html_class = db.Column(db.String(255), index=True, default='form-control')
    html_placeholder = db.Column(db.String(255), index=True, default='')

    @staticmethod
    def get(key):
        setting = Settings.factory(key=key)
        if setting is None:
            return ''
        return setting.value

    def save(self):
        if isinstance(self.value, str):
            self.str_value = self.value
            super().save()
            return
        self.str_value = 'json://' + json.dumps(self.value)
        super().save()

    @classmethod
    def factory(cls, **kwargs):
        if 'value' in kwargs.keys():
            kwargs['str_value'] = kwargs['value']
            del(kwargs['value'])
        clsmodel = db.session.query(cls).filter_by(**kwargs).first()
        if clsmodel is None:
            return clsmodel
        if clsmodel.str_value.startswith('json://'):
            clsmodel.value = json.loads(clsmodel.str_value[7:])
        else:
            clsmodel.value = clsmodel.str_value
        return clsmodel

    @classmethod
    def collection(cls, **kwargs):
        if 'value' in kwargs.keys():
            kwargs['str_value'] = kwargs['value']
            del(kwargs['value'])
        collection = []
        for item in db.session.query(cls).filter_by(**kwargs).all():
            if item.str_value.startswith('json://'):
                item.value = json.loads(item.str_value[7:])
            else:
                item.value = item.str_value
            collection.append(item)
        return collection

    def __repr__(self):
        return '<Setting %i>: %s (%s) -> %s [%s]' % (self.id, self.name, self.key, self.str_value, self.type)


class Job(db.Model, CRUD):
    __tablename__ = 'job_queue'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), index=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(1000))
    status = db.Column(db.String(1000), index=True, default='Scheduled')
    start_date = db.Column(db.DateTime, index=True)
    stop_date = db.Column(db.DateTime, index=True)
    lock_file = db.Column(db.String(255), index=True)
    lock_data = db.Column(db.String(255), index=True)
    running = db.Column(db.Boolean, index=True, default=False)
    errors = db.Column(db.Boolean, index=True, default=False)

    def start(self):
        self.status = 'Started'
        self.create_lock_file()
        self.start_date = datetime.utcnow()
        Log.info('Job started: %s (%i)' % (self.name, self.id))
        self.save()

    def stop(self):
        self.status = 'Finished'
        self.remove_lock_file()
        self.stop_date = datetime.utcnow()
        Log.info('Job completed: %s (%i)' % (self.name, self.id))
        self.save()

    def abort(self, reason=''):
        self.status = 'Aborted'
        self.remove_lock_file()
        self.stop_date = datetime.utcnow()
        Log.warning('Job aborted: %s (%i)' % (self.name, self.id), reason)
        self.save()

    def log_error(self, status, error):
        self.errors = True
        self.status = 'An error occurred: %s' % status
        Log.error(status, error, 'jobs')

    def create_lock_file(self, data=datetime.now().strftime('%c')):
        if not os.path.exists(os.path.dirname(self.lock_file)):
            try:
                os.makedirs(os.path.dirname(self.lock_file))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    self.log_error('Unable to create lock file for job %s (%i)' % (self.name, self.id),
                                   'Unable to create directory structure (%s)' % self.lock_file)
                    return False

        if os.path.exists(self.lock_file):
            self.log_error('Unable to create lock file for job %s (%i)' % (self.name, self.id),
                           'The lock file already exists (%s)' % self.lock_file)
            return False

        try:
            with open(self.lock_file, 'w') as f:
                f.write(data)
        except Exception as exc:
            self.log_error('Unable to create lock file for job %s (%i)' % (self.name, self.id),
                           'Unable to write to file (%s) [%s]' % (self.lock_file, exc))
            return False
        self.lock_data = data
        return True

    def remove_lock_file(self):
        if not os.path.exists(self.lock_file):
            Log.warn('Unable to remove lock file for job %s (%i)' % (self.name, self.id), 'Log file does not exist')
            return True

        try:
            with open(self.lock_file, 'r') as f:
                data = f.read()
        except Exception as exc:
            self.log_error('Unable to remove lock file for job %s (%i)' % (self.name, self.id),
                           'Unable to read from file (%s) [%s]' % (self.lock_file, exc))
            return False

        if data != self.lock_data:
            self.log_error('Unable to remove lock file for job %s (%i)' % (self.name, self.id),
                           'The lock file belongs to another job (%s) [%s]' % (self.lock_file, data))
            return False

        try:
            os.remove(self.lock_file)
        except Exception as exc:
            self.log_error('Unable to remove lock file for job %s (%i)' % (self.name, self.id),
                           'Unable to remove file (%s) [%s]' % (self.lock_file, exc))
            return False

        Log.info('Removed lock file for job %s (%i)' % (self.name, self.id), 'Log file removed with data: %s' % data)
        return True


class Log(db.Model, CRUD):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, index=True)
    category = db.Column(db.String(255), index=True)
    name = db.Column(db.String(255), index=True)
    description = db.Column(db.Text)
    severity = db.Column(db.Integer, index=True, default=0)  # 0 Debug, 1 Info, 2 Warning, 3 Error, 4 Critical, 5 Fatal

    SEVERITY_DEBUG = 0
    SEVERITY_INFO = 1
    SEVERITY_WARN = 2
    SEVERITY_ERROR = 3
    SEVERITY_CRITICAL = 4
    SEVERITY_FATAL = 5

    @property
    def severity_str(self):
        if self.severity == 1:
            return 'Info'
        if self.severity == 2:
            return 'Warning'
        if self.severity == 3:
            return 'Error'
        if self.severity == 4:
            return 'Critical'
        if self.severity == 5:
            return 'Fatal'
        return 'Debug'


    @classmethod
    def add(cls, name, description='', category='default', severity=0):
        cls(date=datetime.utcnow(), category=category, name=name, description=description, severity=severity).save()

    @classmethod
    def debug(cls, name, description='', category='default'):
        cls.add(name, description, category, cls.SEVERITY_DEBUG)

    @classmethod
    def info(cls, name, description='', category='default'):
        cls.add(name, description, category, cls.SEVERITY_INFO)

    @classmethod
    def warning(cls, name, description='', category='default'):
        cls.add(name, description, category, cls.SEVERITY_WARN)

    @classmethod
    def error(cls, name, description='', category='default'):
        cls.add(name, description, category, cls.SEVERITY_ERROR)

    @classmethod
    def critical(cls, name, description='', category='default'):
        cls.add(name, description, category, cls.SEVERITY_CRITICAL)

    @classmethod
    def fatal(cls, name, description='', category='default'):
        cls.add(name, description, category, cls.SEVERITY_FATAL)


class Media:
    @property
    def get_runtime(self):
        hours = self.runtime // 60
        minutes = self.runtime % 60

        if hours > 0 and minutes > 0:
            return '%i hour%s and %i minutes' % (hours, 's' if hours > 1 else '', minutes)
        if hours > 0:
            return '%i hours' % hours
        if minutes > 0:
            return '%i minutes' % minutes
        return ''

    @property
    def get_small_backdrop_url(self):
        return self.get_backdrop_url('w300')

    @property
    def get_medium_backdrop_url(self):
        return self.get_backdrop_url('w780')

    @property
    def get_large_backdrop_url(self):
        return self.get_backdrop_url('w1280')

    @property
    def get_small_poster_url(self):
        return self.get_poster_url('w92')

    @property
    def get_medium_poster_url(self):
        return self.get_poster_url('w154')

    @property
    def get_large_poster_url(self):
        return self.get_poster_url('w342')

    @property
    def get_xl_poster_url(self):
        return self.get_poster_url('w185')

    def get_poster_url(self, size='original'):
        if self.poster == '':
            return '/static/icon.svg'
        return self.get_image_url(self.poster, size)

    def get_backdrop_url(self, size='original'):
        if self.backdrop == '':
            return ''
        return self.get_image_url(self.backdrop, size)

    @staticmethod
    def get_image_url(path, size='original'):
        return tmdb.get_config()['images']['secure_base_url'] + size + path

    # Mark this as offline as we are now saving it to the DB
    def save(self):
        self.offline = True
        super().save()


class Movie(db.Model, Media, CRUD):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, index=True, unique=True)
    imdb_id = db.Column(db.String(25), index=True, unique=True)
    title = db.Column(db.String(255), index=True)
    original_title = db.Column(db.String(255), index=True)
    tagline = db.Column(db.String(255), index=True)
    description = db.Column(db.String(2048), index=True)
    genres = db.Column(db.String(1000), index=True)
    production_companies = db.Column(db.String(25), index=True)
    release_date = db.Column(db.DateTime, index=True)
    runtime = db.Column(db.Integer, index=True)
    status = db.Column(db.String(25), index=True)
    rating = db.Column(db.Integer, index=True)
    rating_count = db.Column(db.Integer, index=True)
    language = db.Column(db.String(25), index=True)
    backdrop = db.Column(db.String(255))
    poster = db.Column(db.String(255))
    offline = db.Column(db.Boolean)
    watching = db.Column(db.Boolean)
    in_library = db.Column(db.Boolean)
    has_files = db.Column(db.Boolean)
    added = db.Column(db.DateTime, index=True)
    search_quality = db.Column(JsonType(255), index=True)

    files = db.relationship('MovieFile', backref='media', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, data=None):
        if data is not None:
            self.populate(data)

    def __repr__(self):
        return '<Movie %r>' % self.title

    def populate(self, data):
        self.tmdb_id = data['id']
        self.imdb_id = data['imdb_id']
        self.title = data['title']
        self.original_title = data['original_title']
        self.tagline = data['tagline']
        self.description = data['overview']
        self.genres = ', '.join([g['name'] for g in data['genres']])
        self.production_companies = ', '.join([g['name'] for g in data['production_companies']])
        self.runtime = data['runtime']
        self.status = data['status'] or 'Unknown'
        self.rating = float(data['vote_average']) / 2.0  # We divide by 2 because our ratings are out of 5
        self.rating_count = data['vote_count']
        self.language = data['original_language']
        self.offline = False
        self.watching = False
        self.in_library = False
        self.has_files = False
        self.search_quality = Settings.get('default_search_quality')

        if data['release_date'] != '':
            self.release_date = datetime.strptime(data['release_date'], "%Y-%m-%d")

        if data['backdrop_path'] == '':
            self.backdrop = ''
        else:
            self.backdrop = data['backdrop_path']

        if data['poster_path'] == '':
            self.poster = ''
        else:
            self.poster = data['poster_path']

    @property
    def recent(self):
        return self.recent_files(days=30)

    def recent_files(self, days=0, weeks=0):
        difference = datetime.utcnow() - timedelta(days=days, weeks=weeks)
        return MovieFile.query.filter(MovieFile.added > difference).filter_by(media_id=self.id).all()

    @staticmethod
    def recent_movies(days=30, weeks=0):
        difference = datetime.utcnow() - timedelta(days=days, weeks=weeks)
        file_ids = db.session.query(MovieFile.media_id).filter(MovieFile.added > difference)
        return Movie.query.filter(Movie.id.in_(file_ids)).all()


class TV(db.Model, CRUD, Media):
    __tablename__ = 'tv'
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, index=True, unique=True)
    imdb_id = db.Column(db.String(25), index=True, unique=True)
    title = db.Column(db.String(255), index=True)
    original_title = db.Column(db.String(255), index=True)
    tagline = db.Column(db.String(255), index=True)
    description = db.Column(db.String(2048), index=True)
    genres = db.Column(db.String(1000), index=True)
    production_companies = db.Column(db.String(25), index=True)
    first_air_date = db.Column(db.DateTime, index=True)
    last_air_date = db.Column(db.DateTime, index=True)
    runtime = db.Column(db.Integer, index=True)
    status = db.Column(db.String(25), index=True)
    rating = db.Column(db.Integer, index=True)
    rating_count = db.Column(db.Integer, index=True)
    language = db.Column(db.String(25), index=True)
    backdrop = db.Column(db.String(255))
    poster = db.Column(db.String(255))
    episode_count = db.Column(db.Integer, index=True)
    season_count = db.Column(db.Integer, index=True)
    available_episodes = db.Column(db.Integer, index=True)
    in_production = db.Column(db.Boolean)
    offline = db.Column(db.Boolean)
    watching = db.Column(db.Boolean)
    in_library = db.Column(db.Boolean)
    has_files = db.Column(db.Boolean)
    added = db.Column(db.DateTime, index=True)
    search_quality = db.Column(JsonType(255), index=True)

    seasons = db.relationship('TVSeason', backref='media', lazy='dynamic', cascade="all, delete-orphan")
    episodes = db.relationship('TVEpisode', backref='media', lazy='dynamic', cascade="all, delete-orphan")
    files = db.relationship('TVEpisodeFile', backref='media', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, data=None):
        if data is not None:
            self.populate(data)

    def __repr__(self):
        return '<TV %r>' % self.title

    def populate(self, data):
        self.tmdb_id = data['id']
        self.imdb_id = tmdb.get_external_tv_ids(self.tmdb_id)['imdb_id']
        self.title = data['name']
        self.original_title = data['original_name']
        self.tagline = data['tagline']
        self.description = data['overview']
        self.genres = ', '.join([g['name'] for g in data['genres']])
        self.production_companies = ', '.join([g['name'] for g in data['production_companies']])
        self.runtime = data['runtime']
        self.status = data['status'] or 'Unknown'
        self.rating = float(data['vote_average']) / 2.0  # We divide by 2 because our ratings are out of 5
        self.rating_count = data['vote_count']
        self.language = data['original_language']
        self.runtime = data['episode_run_time']
        self.season_count = data['number_of_seasons']
        self.available_episodes = data['number_of_episodes']
        self.in_production = data['in_production']
        self.episode_count = 0
        self.offline = False
        self.in_library = False
        self.has_files = False
        self.search_quality = Settings.get('default_search_quality')

        if data['first_air_date'] != '':
            self.first_air_date = datetime.strptime(data['first_air_date'], "%Y-%m-%d")

        if data['last_air_date'] != '':
            self.last_air_date = datetime.strptime(data['last_air_date'], "%Y-%m-%d")

        if data['backdrop_path'] == '':
            self.backdrop = ''
        else:
            self.backdrop = data['backdrop_path']

        if data['poster_path'] == '':
            self.poster = ''
        else:
            self.poster = data['poster_path']

    # @property
    # def seasons(self):
    #     return TVSeason.query.filter_by(media_id=self.id).all()
    #
    # @property
    # def episodes(self):
    #     return TVEpisode.query.filter_by(media_id=self.id).all()

    @property
    def recent(self):
        return self.recent_files(days=30)

    def recent_files(self, days=0, weeks=0):
        difference = datetime.utcnow() - timedelta(days=days, weeks=weeks)
        return TVEpisodeFile.query.filter(TVEpisodeFile.added > difference).filter_by(media_id=self.id)

    @staticmethod
    def recent_tv(days=30, weeks=0):
        difference = datetime.utcnow() - timedelta(days=days, weeks=weeks)
        file_ids = db.session.query(TVEpisodeFile.media_id).filter(TVEpisodeFile.added > difference)
        return TV.query.filter(TV.id.in_(file_ids)).all()


class TVSeason(db.Model, CRUD):
    __tablename__ = 'tv_seasons'
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('tv.id'), index=True)
    season_number = db.Column(db.Integer, index=True)
    air_date = db.Column(db.DateTime, index=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(2048), index=True)
    poster = db.Column(db.String(255))

    episodes = db.relationship('TVEpisode', backref='season', lazy='dynamic', cascade="all, delete-orphan")
    files = db.relationship('TVEpisodeFile', backref='season', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, media_id, season_number=0):
        self.media_id = media_id
        self.season_number = season_number

    def __repr__(self):
        return '<TV Season %r>' % self.title

    def populate(self, data):
        self.season_number = data['season_number']
        self.title = data['name']
        self.description = data['overview']

        if data['air_date'] != '':
            self.air_date = datetime.strptime(data['air_date'], "%Y-%m-%d")

        if data['poster_path'] == '':
            self.poster = '/static/icon.svg'
        else:
            self.poster = data['poster_path']

    # @property
    # def media(self):
    #     return TV.query.filter_by(id=self.media_id).first()
    #
    # @property
    # def episodes(self):
    #     return TVEpisode.query.filter_by(season_id=self.id).all()


class TVEpisode(db.Model, CRUD):
    __tablename__ = 'tv_episodes'
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('tv.id'), index=True)
    season_id = db.Column(db.Integer, db.ForeignKey('tv_seasons.id'), index=True)
    season_number = db.Column(db.Integer, index=True)
    episode_number = db.Column(db.Integer, index=True)
    air_date = db.Column(db.DateTime, index=True)
    title = db.Column(db.String(255))
    status = db.Column(db.String(255))
    description = db.Column(db.String(2048), index=True)
    poster = db.Column(db.String(255))
    rating = db.Column(db.Integer, index=True)
    rating_count = db.Column(db.Integer, index=True)

    files = db.relationship('TVEpisodeFile', backref='episode', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, media_id, season_id, season_number=0, episode_number=0):
        self.media_id = media_id
        self.season_id = season_id
        self.season_number = season_number
        self.episode_number = episode_number

    def __repr__(self):
        return '<TV Episode %r>' % self.title

    def populate(self, data):
        self.season_number = data['season_number']
        self.episode_number = data['episode_number']
        self.title = data['name']
        self.description = data['overview']
        self.rating = float(data['vote_average']) / 2.0  # We divide by 2 because our ratings are out of 5
        self.rating_count = data['vote_count']

        if data['air_date'] != '':
            self.air_date = datetime.strptime(data['air_date'], "%Y-%m-%d")
            if self.air_date > datetime.utcnow():
                self.status = 'Unaired'
            else:
                self.status = 'Aired'
        else:
            self.status = 'Unknown'

        if data['still_path'] == '':
            self.poster = '/static/icon.svg'
        else:
            self.poster = data['still_path']

    # @property
    # def media(self):
    #     return TV.query.filter_by(id=self.media_id).first()
    #
    # @property
    # def season(self):
    #     return TVSeason.query.filter_by(id=self.season_id).first()


class TVEpisodeFile(db.Model, CRUD):
    __tablename__ = 'tv_episode_files'
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('tv.id'))
    season_id = db.Column(db.Integer, db.ForeignKey('tv_seasons.id'))
    episode_id = db.Column(db.Integer, db.ForeignKey('tv_episodes.id'))
    path = db.Column(db.String(4096))
    added = db.Column(db.DateTime, index=True)

    def __init__(self, media_id, season_id, episode_id, path):
        self.media_id = media_id
        self.season_id = season_id
        self.episode_id = episode_id
        self.path = path
        self.added = datetime.utcnow()

    def __repr__(self):
        return '<TV %r, added on %s>' % (self.path, str(self.added))

    # @property
    # def media(self):
    #     return TV.query.filter_by(id=self.media_id).first()
    #
    # @property
    # def season(self):
    #     return TVSeason.query.filter_by(id=self.season_id).first()
    #
    # @property
    # def episode(self):
    #     return TVEpisode.query.filter_by(id=self.episode_id).first()


class MovieFile(db.Model, CRUD):
    __tablename__ = 'movie_files'
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('movies.id'))
    path = db.Column(db.String(4096))
    added = db.Column(db.DateTime, index=True)

    def __init__(self, media_id, path):
        self.media_id = media_id
        self.path = path
        self.added = datetime.utcnow()

    def __repr__(self):
        return '<Movie %r, added on %s>' % (self.path, str(self.added))

    @property
    def media(self):
        return Movie.query.filter_by(id=self.media_id).first()
