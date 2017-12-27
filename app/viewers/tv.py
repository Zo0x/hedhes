from flask import render_template, flash, url_for, redirect, send_from_directory, jsonify, request
from app import app, tmdb, lib
from app.forms import SearchForm, TVSettingsForm, MovieSettingsForm, QualityForm, SettingsForm
from app.models import Movie, TV, TVSeason, TVEpisode, TVEpisodeFile, MovieFile, Settings, Log
from app.library import Library
from datetime import datetime
import urllib


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


@app.route('/tv/refresh', methods=['GET', 'POST'])
def refresh_library_tv_all():
    lib.refresh_tv_all()
    return jsonify({'result': True, 'data': 'TV library refresh scheduled'})


@app.route('/tv/refresh_status/<tmdb_id>', methods=['GET', 'POST'])
def refresh_tv_status(tmdb_id):
    return jsonify({'result': Library.refreshing_tv(tmdb_id), 'data': 'TV refresh status'})


@app.route('/tv/refresh_status', methods=['GET', 'POST'])
def refresh_tv_status_all(tmdb_id):
    return jsonify({'result': Library.refreshing_tv(), 'data': 'TV refresh status'})


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
