#!MediaManagerEnv/bin/python
import sys
import argparse

from app import models
from app import app, tmdb, lib
from app.forms import SearchForm, TVSettingsForm, MovieSettingsForm, QualityForm, SettingsForm
from app.models import Movie, TV, TVSeason, TVEpisode, TVEpisodeFile, MovieFile, Settings, Log
from app.library import Library
from app.decorators import async

# Disable async calls as we want to do everything inl real time
app.config['ASYNC_ENABLED'] = False
app.config['CLI_MODE'] = True

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbosity', action='count', default=0)
subparsers = parser.add_subparsers(dest='action')

refresh_parser = subparsers.add_parser('refresh', help='Refresh library items')
refresh_parser.add_argument('type', help='Refresh item type (tv, movies, all)', default='all', nargs='?')
refresh_parser.add_argument('-a', '--all', help='Refresh all metadata, including discovery of local files (default)', action='store_true')
refresh_parser.add_argument('-l', '--local', help='Discover local files only, adding any to the library but not updating existing items', action='store_true')
refresh_parser.add_argument('-u', '--update', help='Update existing items in the library only, refreshing metadata but ignoring new files', action='store_true')
refresh_parser.add_argument('-i', '--id', help='The ID of the library element to update')

args = parser.parse_args()

if args.action == 'refresh':
    if args.all or args.update:
        if args.type == 'all':
            lib.refresh_all()
        elif args.type == 'tv':
            lib.refresh_tv_all()
        elif args.type == 'movies':
            lib.refresh_movie_all()
    if args.all or args.local:
        if args.type == 'all' or args.type == 'tv':
            lib.refresh_tv_local()
        if args.type == 'all' or args.type == 'movies':
            lib.refresh_movie_local()
