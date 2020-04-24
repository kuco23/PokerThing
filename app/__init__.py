import sqlite3
from sanic import Sanic
from . import config
from .lib import (
    SqLite, ServerGame, ServerTable, ServerPlayerGroup,
    GameDb
)

app = Sanic(__name__)
conn = sqlite3.connect(config.DATABASE_PATH)
dbase = SqLite(conn)
gamedb = GameDb(conn)
game = ServerGame(gamedb)
game += ServerTable(0, gamedb, ServerPlayerGroup([]), 1000, 10, 20)

from . import routes
