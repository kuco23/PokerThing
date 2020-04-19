import sqlite3
from sanic import Sanic
from . import config
from .lib import SqLite, ServerGame, ServerTable, ServerPlayerGroup

app = Sanic(__name__)
dbase = SqLite(sqlite3.connect(config.DATABASE_PATH))
game = ServerGame()
game += ServerTable(0, ServerPlayerGroup([]), 10, 20)

from . import routes
