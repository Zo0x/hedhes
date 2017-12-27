from flask import render_template, flash, url_for, redirect, send_from_directory, jsonify, request
from app import app, tmdb, lib
from app.forms import SearchForm, TVSettingsForm, MovieSettingsForm, QualityForm, SettingsForm
from app.models import Movie, TV, TVSeason, TVEpisode, TVEpisodeFile, MovieFile, Settings, Log
from app.library import Library
import urllib

@app.route('/movies')
def movies():
    return render_template("movies/index.html", title='Movies', heading='Movies', search_form=SearchForm(),
                           movies=Movie.query.filter_by(in_library=True).all(),
                           is_grid=request.cookies.get('mm_movies_sort') == 'grid',
                           refreshing=Library.refreshing_movie())


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


@app.route('/movie/refresh', methods=['GET', 'POST'])
def refresh_library_movie_all():
    lib.refresh_movie_all()
    return jsonify({'result': True, 'data': 'Movie library refresh scheduled'})


@app.route('/movie/refresh_status/<tmdb_id>', methods=['GET', 'POST'])
def refresh_movie_status(tmdb_id):
    return jsonify({'result': Library.refreshing_movie(tmdb_id), 'data': 'Movie refresh status'})


@app.route('/movie/refresh_status', methods=['GET', 'POST'])
def refresh_movie_status_all(tmdb_id):
    return jsonify({'result': Library.refreshing_movie(), 'data': 'Movie refresh status'})


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
