#!/usr/bin/env bash
. /etc/profile.d/python3.bash
virtualenv -p python3 MediaManagerEnv
source MediaManagerEnv/bin/activate
pip install flask
pip install flask-wtf
pip install flask-sqlalchemy
pip install sqlalchemy-migrate
pip install requests
