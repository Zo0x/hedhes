from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

# We have to have rather messy imports here due to cyclic import problems
from .tmdb import TMDB
tmdb = TMDB(app.config.get('TMDB_API_KEY'))

from app import views, models
