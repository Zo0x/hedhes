import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

WTF_CSRF_ENABLED = True
SECRET_KEY = os.urandom(24)

# Borrowed this from sickrage - thanks clinton!
TMDB_API_KEY = 'edc5f123313769de83a71e157758030b'

AVAILABLE_QUALITIES = [
    ('brdisk', 'BR-Disk'), ('1080p', '1080p'), ('720p', '720p'), ('brrip', 'BR-Rip'), ('dvdr', 'DVD-R'),
    ('dvdrip', 'DVD-Rip'), ('screener', 'Screener'), ('r5', 'R5'), ('tc', 'TeleCine'), ('ts', 'TeleSync'),
    ('cam', 'Cam'), ('any', 'Any')
]

DEFAULT_SETTINGS = [
    {
        'key': 'default_search_quality',
        'value': ['1080p', '720p'],
        'name': 'Default Search Quality',
        'type': 'list',
        'choices': AVAILABLE_QUALITIES
    },
    {
        'key': 'search_frequency',
        'value': '24',
        'name': 'Search Frequency (hours)',
        'type': 'float'
    },
    {
        'key': 'enable_search',
        'value': True,
        'name': 'Enable Search',
        'type': 'bool'
    }
]
