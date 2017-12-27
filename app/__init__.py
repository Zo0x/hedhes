from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# We have to have rather messy imports here due to cyclic import problems
from app.lib.tmdb import TMDB
tmdb = TMDB(app.config.get('TMDB_API_KEY'))

import app.lib.filemedia as filemedia

from .library import Library
lib = Library()

from app import views, models

# Initialise the default settings
for setting in app.config.get('DEFAULT_SETTINGS'):
    s = models.Settings.factory(key=setting['key'])
    if s is None:
        s = models.Settings()
        for key in setting:
            s.__dict__[key] = setting[key]
        s.save()
