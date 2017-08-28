from flask import render_template, flash, url_for, redirect, send_from_directory, jsonify, request
from wtforms import StringField

from app import app, tmdb
from .forms import SearchForm, TVSettingsForm, MovieSettingsForm, QualityForm, SettingsForm
from .models import Movie, TV, TVSeason, TVEpisode, TVEpisodeFile, MovieFile, Settings, Log
from .library import Library
from datetime import datetime
from .decorators import async
import urllib
import os


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/browserconfig.xml')
def browserconfig():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'browserconfig.xml', mimetype='text/xml')


@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json', mimetype='application/json')


@app.route('/')
def index():
    return render_template("overview.html", title='Overview', heading='Overview', search_form=SearchForm(),
                           recent_movies=Movie.recent_movies(), recent_tv=TV.recent_tv(),
                           refreshing=Library.refreshing_all())


@app.route('/refresh', methods=['GET', 'POST'])
def refresh_library():
    library = Library()
    library.refresh_all()
    return jsonify({'result': True, 'data': 'Library refresh scheduled'})


@app.route('/refresh/status/', methods=['GET', 'POST'])
def refresh_library_status():
    return jsonify({'result': Library.refreshing_all(), 'data': 'Library refresh status'})


@app.route('/movies')
def movies():
    return render_template("movies/index.html", title='Movies', heading='Movies', search_form=SearchForm(),
                           movies=Movie.query.filter_by(in_library=True).all(),
                           is_grid=request.cookies.get('mm_movies_sort') == 'grid')


@app.route('/movies/<tmdb_id>')
def movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        data = tmdb.get_movie(tmdb_id)
        if not data:
            flash('Movie %s not found.' % tmdb_id)
            return redirect('/')
        mov = Movie(data)
    imdb = 'http://www.dereferer.org/?' + urllib.parse.quote_plus('http://www.imdb.com/title/' + mov.imdb_id)
    settings_form = QualityForm()
    settings_form.quality.data = mov.search_quality
    return render_template('movies/view.html',  title=mov.title,
                           heading=mov.title, media=mov, search_form=SearchForm(),
                           settings_form=settings_form, imdb_link=imdb, refreshing=Library.refreshing_movie(tmdb_id))


@app.route('/movies/watch/<tmdb_id>', methods=['GET', 'POST'])
def watch_movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        data = tmdb.get_movie(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'Movie not found'})
        mov = Movie(data)
    mov.watching = True
    mov.save()
    return jsonify({'result': True, 'data': 'Movie updated'})


@app.route('/movies/unwatch/<tmdb_id>', methods=['GET', 'POST'])
def unwatch_movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        data = tmdb.get_movie(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'Movie not found'})
        mov = Movie(data)
    mov.watching = False
    mov.save()
    return jsonify({'result': True, 'data': 'Movie updated'})


# TODO: Implement the Movie manual search functionality
@app.route('/movie/search/<tmdb_id>', methods=['GET', 'POST'])
def research_movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        data = tmdb.get_movie(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'Movie not found'})
        mov = Movie(data)
    return jsonify({'result': True, 'data': 'Movie manual search scheduled'})


# TODO: Implement the Movie refresh functionality
@app.route('/movie/refresh/<tmdb_id>', methods=['GET', 'POST'])
def refresh_movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        data = tmdb.get_movie(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'Movie not found'})
        mov = Movie(data)
    Library.refresh_movie_item(mov)
    return jsonify({'result': True, 'data': 'Movie refresh scheduled'})


@app.route('/movie/refresh_status/<tmdb_id>', methods=['GET', 'POST'])
def refresh_movie_status(tmdb_id):
    return jsonify({'result': Library.refreshing_movie(tmdb_id), 'data': 'Movie refresh status'})


@app.route('/movies/add/<tmdb_id>', methods=['GET', 'POST'])
def add_movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        data = tmdb.get_movie(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'Movie not found'})
        mov = Movie(data)
    mov.in_library = True
    mov.save()
    return jsonify({'result': True, 'data': 'Movie updated'})


@app.route('/movies/remove/<tmdb_id>', methods=['GET', 'POST'])
def remove_movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        return jsonify({'result': False, 'data': 'Movie not found in library'})
    mov.destroy()
    return jsonify({'result': True, 'data': 'Movie removed from library'})


@app.route('/movies/save/<tmdb_id>', methods=['GET', 'POST'])
def save_movie(tmdb_id):
    mov = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if mov is None:
        flash('Movie not found')
        return redirect('/')
    form = MovieSettingsForm()
    if form.validate_on_submit():
        mov.search_quality = form.quality.data
        mov.save()
        flash('Movie data saved')
    return redirect('/movies/' + tmdb_id)


@app.route('/tv')
def tvm():
    return render_template("tv/index.html", title='TV', heading='TV', search_form=SearchForm(),
                           tv_shows=TV.query.filter_by(in_library=True).all(),
                           is_grid=request.cookies.get('mm_tv_sort') == 'grid')


@app.route('/tv/<tmdb_id>')
def tvp(tmdb_id):
    tv = TV.query.filter_by(tmdb_id=tmdb_id).first()
    if tv is None:
        data = tmdb.get_tv(tmdb_id)
        if not data:
            flash('TV show %s not found.' % tmdb_id)
            return redirect('/')
        tv = TV(data)
    imdb = 'http://www.dereferer.org/?' + urllib.parse.quote_plus('http://www.imdb.com/title/' + tv.imdb_id)
    settings_form = TVSettingsForm()
    settings_form.quality.data = tv.search_quality
    return render_template('tv/view.html',  title=tv.title,
                           heading=tv.title, media=tv, search_form=SearchForm(),
                           settings_form=settings_form, imdb_link=imdb, refreshing=Library.refreshing_tv(tmdb_id))


@app.route('/tv/watch/<tmdb_id>', methods=['GET', 'POST'])
def watch_tv(tmdb_id):
    tv = TV.query.filter_by(tmdb_id=tmdb_id).first()
    if tv is None:
        data = tmdb.get_tv(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'TV show not found'})
        tv = TV(data)
    tv.watching = True
    tv.save()
    return jsonify({'result': True, 'data': 'TV show updated: now watching'})


@app.route('/tv/unwatch/<tmdb_id>', methods=['GET', 'POST'])
def unwatch_tv(tmdb_id):
    tv = TV.query.filter_by(tmdb_id=tmdb_id).first()
    if tv is None:
        data = tmdb.get_tv(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'TV show not found'})
        tv = TV(data)
    tv.watching = False
    tv.save()
    return jsonify({'result': True, 'data': 'TV show updated: not watching'})


# TODO: Implement the TV manual search functionality
@app.route('/tv/search/<tmdb_id>', methods=['GET', 'POST'])
def research_tv(tmdb_id):
    tv = TV.query.filter_by(tmdb_id=tmdb_id).first()
    if tv is None:
        data = tmdb.get_tv(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'TV show manual search scheduled'})
        tv = TV(data)
    return jsonify({'result': True, 'data': 'TV show updated'})


# TODO: Implement the TV refresh functionality
@app.route('/tv/refresh/<tmdb_id>', methods=['GET', 'POST'])
def refresh_tv(tmdb_id):
    tv = TV.query.filter_by(tmdb_id=tmdb_id).first()
    if tv is None:
        data = tmdb.get_tv(tmdb_id)
        if not data:
            return jsonify({'result': False, 'data': 'TV show not found'})
        tv = TV(data)
    Library.refresh_tv_item(tv)
    return jsonify({'result': True, 'data': 'TV show refresh scheduled'})


@app.route('/tv/refresh_status/<tmdb_id>', methods=['GET', 'POST'])
def refresh_tv_status(tmdb_id):
    return jsonify({'result': Library.refreshing_tv(tmdb_id), 'data': 'TV refresh status'})


@app.route('/tv/add/<tmdb_id>', methods=['GET', 'POST'])
def add_tv(tmdb_id):
    data = tmdb.get_tv(tmdb_id)
    if not data:
        return jsonify({'result': False, 'data': 'TV show not found'})
    tv = TV.query.filter_by(tmdb_id=tmdb_id).first()
    if tv is None:
        tv = TV(data)
    tv.in_library = True
    tv.offline = True
    tv.added = datetime.now()
    tv.save()
    for season in data['seasons']:
        s = tmdb.get_tv_season(tmdb_id, season['season_number'])
        if s is not None:
            tvs = TVSeason(tv.id, s['season_number'])
            tvs.populate(s)
            tvs.save()
            for episode in s['episodes']:
                eps = TVEpisode(tv.id, tvs.id)
                eps.populate(episode)
                eps.save()
    return jsonify({'result': True, 'data': 'TV show added to library'})


@app.route('/tv/save/<tmdb_id>', methods=['GET', 'POST'])
def save_tv(tmdb_id):
    tv = TV.factory(tmdb_id=tmdb_id)
    if tv is None:
        flash('TV show not found')
        return redirect('/')
    form = TVSettingsForm()
    if form.validate_on_submit():
        tv.search_quality = form.quality.data
        tv.save()
        flash('TV show data saved')
    return redirect('/tv/' + tmdb_id)


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
