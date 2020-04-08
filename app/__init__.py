import sqlite3
from flask import Flask
from .lib import *
from . import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'NotImplemented'
con = sqlite3.connect(config.DATABASE_PATH)
for table in DbTable: sqlsup.createTable(con, table)

from . import routes
