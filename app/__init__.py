import sqlite3
from sanic import Sanic

from . import config
from .lib import (
    SqLite, ServerGame, ServerTable, ServerPlayerGroup,
    DbTable, DbBrowser, DbGame
)

app = Sanic(__name__)
conn = sqlite3.connect(config.DATABASE_PATH)
dbase = SqLite(conn)
dbgame = DbGame(conn)
dbbrowser = DbBrowser(conn)
game = ServerGame()
game += ServerTable(dbgame, 0, 9, 1000, 200, 10, 20)

from . import routes
