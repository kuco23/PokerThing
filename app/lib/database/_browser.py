from ._enums import DbTable
from ._tables import *

from sanic.log import logger

class DbBrowser:
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def readTable(self, table):
        cols = table_read_columns[table]._fields
        self.cursor.execute(
            f"SELECT {','.join(cols)} FROM {table.value}"
        )
        return cols, self.cursor.fetchall()
    
    def getAccount(self, account_id):
        cols = table_read_columns[DbTable.ACCOUNTS]._fields
        self.cursor.execute(
            f""""
            SELECT {','.join(cols)} FROM {DbTable.ACCOUNTS.value}
            WHERE id = {account_id}
            """
        )
        return cols, self.cursor.fetchall()