#!MediaManagerEnv/bin/python
import sys
from app import app, models

app.run(debug=True, port=int(sys.argv[1]) if len(sys.argv) > 1 else 5000)
