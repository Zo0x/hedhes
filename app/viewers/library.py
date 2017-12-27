from flask import render_template, flash, url_for, redirect, send_from_directory, jsonify, request
from app import app, tmdb, lib
from app.forms import SearchForm, TVSettingsForm, MovieSettingsForm, QualityForm, SettingsForm
from app.models import Movie, TV, TVSeason, TVEpisode, TVEpisodeFile, MovieFile, Settings, Log
from app.library import Library


@app.route('/')
def index():
    return render_template("overview.html", title='Overview', heading='Overview', search_form=SearchForm(),
                           recent_movies=Movie.recent_movies(), recent_tv=TV.recent_tv(),
                           refreshing=Library.refreshing_all())


@app.route('/refresh', methods=['GET', 'POST'])
def refresh_library():
    lib.refresh_all()
    return jsonify({'result': True, 'data': 'Library refresh scheduled'})


@app.route('/refresh/status', methods=['GET', 'POST'])
def refresh_library_status():
    return jsonify({'result': Library.refreshing_all(), 'data': 'Library refresh status'})

