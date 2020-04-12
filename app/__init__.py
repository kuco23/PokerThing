import sqlite3
from sanic import Sanic
from . import config
from .lib import *

app = Sanic(__name__)
con = sqlite3.connect(config.DATABASE_PATH)
for table in DbTable: sqlsup.createTable(con, table)

from . import routes
