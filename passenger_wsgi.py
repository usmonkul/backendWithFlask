import sys
import os

INTERP = "/home/host7637/virtualenv/flask.backend/3.11/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from app import application
