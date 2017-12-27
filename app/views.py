from flask import render_template, flash, url_for, redirect, send_from_directory, jsonify, request
from wtforms import StringField

from . import app, tmdb, lib
from .forms import SearchForm, TVSettingsForm, MovieSettingsForm, QualityForm, SettingsForm
from .models import Movie, TV, TVSeason, TVEpisode, TVEpisodeFile, MovieFile, Settings, Log
from .library import Library
from .decorators import async
from .viewers import *


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    settings_form = SettingsForm.factory(Settings.collection())
    if settings_form.validate_on_submit():
        for setting in settings_form:
            if setting.name == 'csrf_token':
                continue
            setcls = Settings.factory(key=setting.name)
            if setcls is None:
                print('Unable to save setting: ' + setting.name)
                continue
            setcls.value = setting.data
            setcls.save()
    return render_template("settings.html", title='Settings', heading='Settings',
                           search_form=SearchForm(), settings_form=settings_form)


@app.route('/logs')
def logs():
    return render_template("logs.html", title='Logs', heading='Logs', search_form=SearchForm(), logs=Log().collection())


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    mov = []
    tv = []
    if form.validate_on_submit():
        mov = [Movie(m) for m in tmdb.search_movie(form.query.data)]
        tv = [TV(t) for t in tmdb.search_tv(form.query.data)]
    return render_template('search.html', title='Search', heading='Search Results', search_form=form, movies=mov, tv=tv)
