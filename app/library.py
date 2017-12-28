from itertools import chain

import sys

from .decorators import async, asyncp
from app import app, tmdb
import app.lib.filemedia as filemedia
from .models import Movie, TV, Job, Settings, Log
from pathlib import Path
import os
import time


class Library:
    BASE_LOCK_PATH = os.path.join(app.instance_path, 'library')
    REFRESH_ALL_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all.lck')
    REFRESH_ALL_TV_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_tv.lck')
    REFRESH_ALL_TV_LOCAL_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_tv_local.lck')
    REFRESH_TV_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_tv', '{{tmdb_id.lck}}')
    REFRESH_ALL_MOVIE_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_movie.lck')
    REFRESH_ALL_MOVIE_LOCAL_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_movie_local.lck')
    REFRESH_MOVIE_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_movie', '{{tmdb_id.lck}}')
    SETTINGS_MOVIE_MEDIA_PATH = 'movie_media_path'
    SETTINGS_TV_MEDIA_PATH = 'tv_media_path'
    SETTINGS_MOVIE_DOWNLOAD_PATH = 'movie_download_path'
    SETTINGS_TV_DOWNLOAD_PATH = 'tv_download_path'

    @staticmethod
    def refreshing_all():
        return len(Job.collection(key='refresh_all', running=True)) > 0

    @staticmethod
    def refreshing_tv(tmdb_id=None):
        if tmdb_id is None:
            return len(Job.collection(key='refresh_tv', running=True)) > 0
        return len(Job.collection(key='refresh_tv:%s' % tmdb_id, running=True)) > 0

    @staticmethod
    def refreshing_tv_local():
        return len(Job.collection(key='refresh_tv_local', running=True)) > 0

    @staticmethod
    def refreshing_movie(tmdb_id=None):
        if tmdb_id is None:
            return len(Job.collection(key='refresh_movie', running=True)) > 0
        return len(Job.collection(key='refresh_movie:%s' % tmdb_id, running=True)) > 0

    @staticmethod
    def refreshing_movie_local():
        return len(Job.collection(key='refresh_movie_local', running=True)) > 0

    @async
    def refresh_all(self):
        if os.path.exists(self.REFRESH_ALL_LOCK_PATH):
            if self.refreshing_all():
                return
            os.remove(self.REFRESH_ALL_LOCK_PATH)
        job = Job(
            key='refresh_all', name='Refresh all library items', lock_file=self.REFRESH_ALL_LOCK_PATH,
            description='Refreshes all local library information, scanning for local file updates and ' +
                        'downloading any missing or updated metadata for the relevant items in the library')
        job.start()
        job.execute(self.__refresh_all)
        job.stop()

    def __refresh_all(self):
        self.__refresh_movie_all()
        self.__refresh_tv_all()

    @async
    def refresh_tv_item(self, item: TV):
        path = self.REFRESH_TV_ITEM_LOCK_PATH.replace('{{tmdb_id.lck}}', item.tmdb_id)
        if os.path.exists(path):
            if self.refreshing_tv(item.tmdb_id):
                return
            os.remove(path)
        job = Job(
            key='refresh_tv:%s' % item.tmdb_id, name='Refresh TV library item', lock_file=path,
            description='Refreshes all local library information for the relevant title, scanning for local file ' +
                        'updates and downloading any missing or updated metadata for the item in the library' +
                        (', library item: %s' % item.title))
        job.start()
        job.execute(self.__refresh_tv_item, kwargs={item: item})
        job.stop()

    def __refresh_tv_item(self, item: TV):
        pass

    @async
    def refresh_tv_all(self):
        if os.path.exists(self.REFRESH_ALL_TV_LOCK_PATH):
            if self.refreshing_tv():
                return
            os.remove(self.REFRESH_ALL_TV_LOCK_PATH)
        job = Job(
            key='refresh_tv', name='Refresh all TV library items', lock_file=self.REFRESH_ALL_TV_LOCK_PATH,
            description='Refreshes all local TV library information, scanning for local file updates and ' +
                        'downloading any missing or updated metadata for the relevant items in the library')
        job.start()
        job.execute(self.__refresh_tv_all)
        job.stop()

    def __refresh_tv_all(self):
        pass

    @async
    def refresh_tv_local(self):
        if os.path.exists(self.REFRESH_ALL_TV_LOCAL_LOCK_PATH):
            if self.refreshing_tv_local():
                return
            os.remove(self.REFRESH_ALL_TV_LOCAL_LOCK_PATH)
        job = Job(
            key='refresh_tv_local', name='Refresh all local TV library item data', lock_file=self.REFRESH_ALL_TV_LOCAL_LOCK_PATH,
            description='Refreshes all local TV library information, scanning for local file updates and ' +
                        'downloading any missing or updated metadata for the relevant items in the library')
        job.start()
        job.execute(self.__refresh_tv_local)
        job.stop()

    def __refresh_tv_local(self):
        pass

    @async
    def refresh_movie_item(self, item: Movie):
        path = self.REFRESH_MOVIE_ITEM_LOCK_PATH.replace('{{tmdb_id.lck}}', item.tmdb_id)
        if os.path.exists(path):
            if self.refreshing_movie(item.tmdb_id):
                return
            os.remove(path)
        job = Job(
            key='refresh_movie:%s' % item.tmdb_id, name='Refresh movie library item', lock_file=path,
            description='Refreshes all local library information for the relevant title, scanning for local file ' +
                        'updates and downloading any missing or updated metadata for the item in the library' +
                        (', library item: %s' % item.title))
        job.start()
        job.execute(self.__refresh_movie_item, kwargs={item: item})
        job.stop()

    def __refresh_movie_item(self, item: Movie):
        pass

    @async
    def refresh_movie_local(self):
        if os.path.exists(self.REFRESH_ALL_MOVIE_LOCAL_LOCK_PATH):
            if self.refreshing_movie():
                return
            os.remove(self.REFRESH_ALL_MOVIE_LOCAL_LOCK_PATH)
        job = Job(
            key='refresh_movie_local', name='Refresh all local movie library item data', lock_file=self.REFRESH_ALL_MOVIE_LOCAL_LOCK_PATH,
            description='Refreshes all local movie library information, scanning for local file updates and ' +
                        'downloading any missing or updated metadata for the relevant items in the library')
        job.start()
        job.execute(self.__refresh_movie_local)
        job.stop()

    def __refresh_movie_local(self):
        dpath = Settings.get(self.SETTINGS_MOVIE_DOWNLOAD_PATH)
        mpath = Settings.get(self.SETTINGS_MOVIE_MEDIA_PATH)
        ptn = filemedia.PTN()

        downloads = Path(dpath)
        media_files = chain.from_iterable(downloads.rglob(os.path.join('**', '*' + p)) for p in filemedia.video_file_extensions)

        for path in media_files:
            ptn_data = ptn.parse(path.name)
            newfile = self.__generate_movie_file_from_ptn(ptn_data) + path.suffix
            newdir = os.path.join(mpath, self.__generate_movie_folder_from_ptn(ptn_data))
            newpath = os.path.join(newdir, newfile)
            oldpath = str(path)

            if 'year' in ptn_data:
                movies = tmdb.search_movie(ptn_data['title'], ptn_data['year'])
            else:
                movies = tmdb.search_movie(ptn_data['title'])

            if len(movies) < 1 or 'id' not in movies[0]:
                continue

            movie = Movie.query.filter_by(tmdb_id=movies[0]['id']).first()
            if movie is None:
                data = tmdb.get_movie(movies[0]['id'])
                if not data:
                    Log.error('Movie %s not found.' % movies[0]['id'])
                    return False
                movie = Movie(data)

            if movie.has_files:
                Log.error('Movie %s already has files in the library' % movies[0]['id'],
                          'Ignoring download file: %s' % oldpath)
            elif os.path.isfile(newpath):
                Log.warning('Destination file for movie %s already exists' % movies[0]['id'],
                            'Ignoring download file: %s\nAdding media file:%s' % (oldpath, newpath))
                movie.add_file(newpath)
            else:
                # TODO: Move the file to the newpath first then add this
                Log.info('Creating directory', newdir)
                os.makedirs(newdir, exist_ok=True)
                Log.info('Moving media file', 'Src: %s\nDst: %s' % (oldpath, newpath))
                os.rename(oldpath, newpath)
                if app.config['symlink_files']:
                    try:
                        os.symlink(newpath, oldpath)
                    except OSError as e:
                        Log.error('Error creating symlink', 'Src: %s\nDst: %s\n%s' % (oldpath, newpath, e.strerror))
                elif app.config['hardlink_files']:
                    try:
                        os.link(newpath, oldpath)
                    except OSError as e:
                        Log.error('Error creating hardlink', 'Src: %s\nDst: %s\n%s' % (oldpath, newpath, e.strerror))
                        try:
                            os.symlink(newpath, oldpath)
                        except OSError as e:
                            Log.error('Error creating symlink', 'Src: %s\nDst: %s\n%s' % (oldpath, newpath, e.strerror))
                movie.add_file(newpath)
        pass

    @staticmethod
    def __generate_movie_folder_from_ptn(ptn_data):
        outstr = ptn_data['title'].strip().strip('.,')
        if 'year' in ptn_data:
            outstr += ' (%i)' % ptn_data['year']
        return outstr

    @staticmethod
    def __generate_movie_file_from_ptn(ptn_data):
        outstr = ptn_data['title'].strip().strip('..')
        if 'year' in ptn_data:
            outstr += ' (%i)' % ptn_data['year']
        if 'resolution' in ptn_data:
            outstr += ' [%s]' % ptn_data['resolution']
        return outstr

    @async
    def refresh_movie_all(self):
        if os.path.exists(self.REFRESH_ALL_MOVIE_LOCK_PATH):
            if self.refreshing_movie():
                return
            os.remove(self.REFRESH_ALL_MOVIE_LOCK_PATH)
        job = Job(
            key='refresh_movie', name='Refresh all movie library items', lock_file=self.REFRESH_ALL_MOVIE_LOCK_PATH,
            description='Refreshes all local movie library information, scanning for local file updates and ' +
                        'downloading any missing or updated metadata for the relevant items in the library')
        job.start()
        job.execute(self.__refresh_movie_all)
        job.stop()

    def __refresh_movie_all(self):
        pass
