import requests
import datetime


class TMDB:
    def __init__(self, api_key):
        self._api_key = api_key
        self._url = 'https://api.themoviedb.org/3'
        self.base_data = {
            'movie': {
                'id': 0, 'imdb_id': '', 'title': '', 'original_title': '', 'tagline': '', 'overview': '', 'genres': [],
                'production_companies': [], 'runtime': 0, 'status': '', 'vote_average': 0, 'vote_count': 0,
                'original_language': 'en', 'release_date': '', 'backdrop_path': '', 'poster_path': ''
            },
            'tv': {
                'id': 0, 'imdb_id': '', 'name': '', 'original_name': '', 'tagline': '', 'overview': '', 'genres': [],
                'production_companies': [], 'runtime': 0, 'status': '', 'vote_average': 0, 'vote_count': 0,
                'original_language': 'en', 'first_air_date': '', 'last_air_date': '', 'backdrop_path': '',
                'poster_path': '', 'episode_run_time': 0, 'in_production': True, 'number_of_seasons': 0,
                'number_of_episodes': 0
            },
            'season': {
                'season_number': 0, 'air_date': '', 'name': '', 'overview': '', 'poster_path': '', 'episodes': []
            },
            'episode': {
                'season_number': 0, 'episode_number': 0, 'air_date': '', 'name': '',
                'overview': '', 'vote_average': 0, 'vote_count': 0, 'still_path': ''
            },
            'external_ids': {
                'imdb_id': '', 'freebase_mid': '', 'freebase_id': '', 'tvrage_id': 0, 'id': 0, 'tvdb_id': 0
            },
            'images': {'id': 0, 'backdrops': [], 'posters': []}
        }
        self._config = None

    def get_config(self):
        if self._config is None:
            self._config = requests.get(self._url + '/configuration', params={'api_key': self._api_key}).json()
        return self._config

    def search_movie(self, query):
        r = requests.get(self._url + '/search/movie',  params={'api_key': self._api_key, 'query': query})
        if r.status_code != 200:
            return []
        movies = []

        for result in r.json()['results']:
            # Extend our base results whilst also removing blank values to keep the defaults
            data = self.base_data['movie'].copy()
            data.update({k: v for k, v in result.items() if v})
            movies.append(data)

        return movies

    def get_movie(self, tmdb_id):
        r = requests.get(self._url + '/movie/{}'.format(tmdb_id), params={'api_key': self._api_key})
        if r.status_code != 200:
            return False
        data = self.base_data['movie'].copy()
        data.update({k: v for k, v in r.json().items() if v})
        poster = self.get_best_movie_poster(tmdb_id)  # Update the poster to a decent one
        if poster != '':
            data['poster_path'] = poster
        return data

    def search_tv(self, query):
        r = requests.get(self._url + '/search/tv', params={'api_key': self._api_key, 'query': query})
        if r.status_code != 200:
            return []
        tvs = []

        for result in r.json()['results']:
            # Extend our base results whilst also removing blank values to keep the defaults
            data = self.base_data['tv'].copy()
            data.update({k: v for k, v in result.items() if v})
            tvs.append(data)

        return tvs

    def get_tv(self, tmdb_id):
        r = requests.get(self._url + '/tv/{}'.format(tmdb_id), params={'api_key': self._api_key})
        if r.status_code != 200:
            return False
        results = r.json()
        # Get the most common runtime value, we don't care about any "special" episodes
        results['episode_run_time'] = max(set(results['episode_run_time']), key=results['episode_run_time'].count)
        data = self.base_data['tv'].copy()
        data.update({k: v for k, v in results.items() if v})
        poster = self.get_best_tv_poster(tmdb_id)  # Update the poster to a decent one
        if poster != '':
            data['poster_path'] = poster
        return data

    def get_tv_season(self, tv_id, season_number):
        r = requests.get(self._url + '/tv/{}/season/{}'.format(tv_id, season_number), params={'api_key': self._api_key})
        if r.status_code != 200:
            return False
        data = self.base_data['season'].copy()
        data.update({k: v for k, v in r.json().items() if v})

        # Fix for potential missing keys, just use some default values
        for x in range(0, len(data['episodes'])-1):
            episode = self.base_data['episode'].copy()
            episode.update({k: v for k, v in data['episodes'][x].items() if v})
            data['episodes'][x] = episode

        return data

    def get_external_tv_ids(self, tv_id):
        r = requests.get(self._url + '/tv/{}/external_ids'.format(tv_id), params={'api_key': self._api_key})
        if r.status_code != 200:
            return False
        data = self.base_data['external_ids'].copy()
        data.update({k: v for k, v in r.json().items() if v})
        return data

    def get_images(self, tmdb_id, media_type):
        r = requests.get(
            self._url + '/{}/{}/images'.format(media_type, tmdb_id),
            params={'api_key': self._api_key, 'language': 'en'}
        )
        if r.status_code != 200:
            return False
        data = self.base_data['images'].copy()
        data.update({k: v for k, v in r.json().items() if v})
        return data

    def get_best_poster(self, tmdb_id, media_type):
        images = self.get_images(tmdb_id, media_type)
        if len(images['posters']) < 1:
            return ''
        if len(images['posters']) == 1:
            return images['posters'][0]['file_path']
        # Sort the list by the vote average to get the favourite images first
        posters = sorted(images['posters'], key=lambda x: (x['vote_average'], x['aspect_ratio']))[::-1]
        target = (1/3)*2  # Get our 0.666 recurring float value
        # Then select the first poster which matches our desired aspect ratio the most, keeping the highest rated first
        return min(posters, key=lambda y: abs(float(y['aspect_ratio'])-target))['file_path']


    def get_best_movie_poster(self, tmdb_id):
        return self.get_best_poster(tmdb_id, 'movie')

    def get_best_tv_poster(self, tmdb_id):
        return self.get_best_poster(tmdb_id, 'tv')

    def get_movie_images(self, tmdb_id):
        return self.get_images(tmdb_id, 'movie')

    def get_tv_images(self, tmdb_id):
        return self.get_images(tmdb_id, 'tv')
