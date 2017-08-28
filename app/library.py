from .decorators import async
from app import app
from .models import Movie, TV, Job
import datetime
import os
import errno
import time


class Library:
    BASE_LOCK_PATH = os.path.join(app.instance_path, 'library')
    REFRESH_ALL_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all.lck')
    REFRESH_ALL_TV_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_tv.lck')
    REFRESH_TV_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_tv', '{{tmdb_id.lck}}')
    REFRESH_ALL_MOVIE_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_movie.lck')
    REFRESH_MOVIE_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_movie', '{{tmdb_id.lck}}')

    @property
    def refreshing_all(self):
        return True

    @async
    def refresh_all(self):
        if os.path.exists(self.REFRESH_ALL_LOCK_PATH):
            if len(Job.collection(key='refresh_all', running=True)) > 0:
                return
            os.remove(self.REFRESH_ALL_LOCK_PATH)
        job = Job(
            key='refresh_all', name='Refresh all library items', lock_file=self.REFRESH_ALL_LOCK_PATH,
            description='Refreshes all local library information, scanning for local file updates and ' +
                        'downloading any missing or updated metadata for the relevant items in the library')
        job.start()

        time.sleep(60)

        job.stop()

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

