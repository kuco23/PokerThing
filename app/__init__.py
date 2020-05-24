import sqlite3
from sanic import Sanic

from . import config
from .lib import *

app = Sanic(__name__)
conn = sqlite3.connect(config.DATABASE_PATH)
dbase = SqLite(conn)

PokerGameDatabase = DbGame(conn)
DatabaseBrowser = DbBrowser(conn)
PokerGame = ServerGame()

for (table_id, table_name), seats, buyin, minbuyin, sb, bb in zip(
    enumerate(config.TABLE_NAMES), 
    config.TABLE_SEATS,
    config.TABLE_BUYIN,
    config.TABLE_MINBUYIN,
    config.TABLE_SMALLBLIND,
    config.TABLE_BIGBLIND
):
    PokerGame += ServerTable(
        PokerGameDatabase, table_id, table_name,
        seats, buyin, minbuyin, sb, bb
    )

from . import routes
