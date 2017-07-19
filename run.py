#!MediaManagerEnv/bin/python
from app import app, models

# Initialise the default settings
for setting in app.config.get('DEFAULT_SETTINGS'):
    s = models.Settings.factory(key=setting['key'])
    if s is None:
        s = models.Settings()
        for key in setting:
            s.__dict__[key] = setting[key]
        s.save()

app.run(debug=True, port=5000)
