from flask import render_template, flash, url_for, redirect, send_from_directory, jsonify, request
from app import app, tmdb, lib
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