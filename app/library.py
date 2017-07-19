from .decorators import async
from app import app
from .models import Movie, TV
import datetime
import os
import errno


class Library:
    BASE_LOCK_PATH = os.path.join(app.instance_path, 'library')
    REFRESH_ALL_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all.lck')
    REFRESH_ALL_TV_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_tv.lck')
    REFRESH_TV_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_tv', '{{tmdb_id.lck}}')
    REFRESH_ALL_MOVIE_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_movie.lck')
    REFRESH_MOVIE_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_movie', '{{tmdb_id.lck}}')

    @staticmethod
    def create_lock_file(path, data=datetime.datetime.now().strftime('%c')):
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(path, 'w') as f:
            f.write(data)

    @async
    def refresh_all(self):
        if os.path.exists(self.REFRESH_ALL_LOCK_PATH):
            return
        self.create_lock_file(self.REFRESH_ALL_LOCK_PATH)

    @async
    def refresh_tv_item(self, item: TV):
        path = self.REFRESH_TV_ITEM_LOCK_PATH.replace('{{tmdb_id.lck}}', item.tmdb_id)
        if os.path.exists(path):
            return
        self.create_lock_file(path)



    @async
    def refresh_tv(self):
        if os.path.exists(self.REFRESH_ALL_TV_LOCK_PATH):
            return
        self.create_lock_file(self.REFRESH_ALL_TV_LOCK_PATH)

    @async
    def refresh_movie_item(self, item: Movie):
        path = self.REFRESH_MOVIE_ITEM_LOCK_PATH.replace('{{tmdb_id.lck}}', item.tmdb_id)
        if os.path.exists(path):
            return
        self.create_lock_file(path)

    @async
    def refresh_movie(self):
        if os.path.exists(self.REFRESH_ALL_MOVIE_LOCK_PATH):
            return
        self.create_lock_file(self.REFRESH_ALL_MOVIE_LOCK_PATH)

