from .decorators import async
from app import app
from .models import Movie, TV, Job
import os
import time


class Library:
    BASE_LOCK_PATH = os.path.join(app.instance_path, 'library')
    REFRESH_ALL_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all.lck')
    REFRESH_ALL_TV_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_tv.lck')
    REFRESH_TV_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_tv', '{{tmdb_id.lck}}')
    REFRESH_ALL_MOVIE_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_all_movie.lck')
    REFRESH_MOVIE_ITEM_LOCK_PATH = os.path.join(BASE_LOCK_PATH, 'refresh_movie', '{{tmdb_id.lck}}')

    @staticmethod
    def refreshing_all():
        return len(Job.collection(key='refresh_all', running=True)) > 0

    @staticmethod
    def refreshing_tv(tmdb_id=None):
        if tmdb_id is None:
            return len(Job.collection(key='refresh_tv', running=True)) > 0
        return len(Job.collection(key='refresh_tv:%i' % tmdb_id, running=True)) > 0

    @staticmethod
    def refreshing_movie(tmdb_id=None):
        if tmdb_id is None:
            return len(Job.collection(key='refresh_movie', running=True)) > 0
        return len(Job.collection(key='refresh_movie:%i' % tmdb_id, running=True)) > 0

    @async
    def refresh_all(self):
        if os.path.exists(self.REFRESH_ALL_LOCK_PATH):
            if self.refreshing_all:
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

    @async
    def refresh_tv_all(self):
        if os.path.exists(self.REFRESH_ALL_TV_LOCK_PATH):
            return

    @async
    def refresh_movie_item(self, item: Movie):
        path = self.REFRESH_MOVIE_ITEM_LOCK_PATH.replace('{{tmdb_id.lck}}', item.tmdb_id)
        if os.path.exists(path):
            return

    @async
    def refresh_movie_all(self):
        if os.path.exists(self.REFRESH_ALL_MOVIE_LOCK_PATH):
            return

