from collections import namedtuple
import sqlite3
from ._enums import DbTable

make_accounts_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.ACCOUNTS.name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL CHECK(length(password_hash) = 64),
    email TEXT NOT NULL,
    money INTEGER NOT NULL
) 
"""
make_pokertables_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.POKERTABLES.name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    blind INTEGER NOT NULL
)
"""
make_players_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.PLAYERS.name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    pokertable_id INTEGER,
    money INTEGER,
    FOREIGN KEY (account_id) 
        REFERENCES {DbTable.ACCOUNTS.name}(id),
    FOREIGN KEY (pokertable_id) 
        REFERENCES {DbTable.POKERTABLES.name}(id)
)
"""
make_actions_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.ACTIONS.name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    turn_id INTEGER NOT NULL,
    action_id INTEGER NOT NULL,
    round_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    FOREIGN KEY (player_id) 
        REFERENCES {DbTable.PLAYERS.name}(id)
)
"""

dbtables = dict(zip(
    DbTable, [
        make_accounts_table,
        make_pokertables_table,
        make_players_table,
        make_actions_table
    ]
))

table_columns = dict(zip(DbTable, map(
    namedtuple, [table.name for table in DbTable], [
        ['id', 'username', 'password_hash', 'email', 'money'],
        ['id', 'blind'], 
        ['id', 'account_id', 'pokertable_id', 'money'],
        ['id', 'timestamp', 'turn_id', 'round_id', 'player_id']
    ]
)))

class SqLite:

    def __init__(self, con):
        self.connection = con
        self.cursor = con.cursor()
        for table in DbTable: self.createTable(table)

    def createTable(self, tbl, overwrite=False):
        make_table = dbtables[tbl]
        if overwrite:
            sql = "DROP TABLE IF EXISTS " + tbl.name
            self.cursor.execute(sql)
        self.cursor.execute(make_table)
        self.connection.commit()

    def insert(self, tbl, **pairs):
        keys = ','.join(pairs.keys())
        ques = ','.join(['?'] * len(pairs))
        self.cursor.executemany(
            f'INSERT INTO {tbl.name} ({keys}) VALUES ({ques})',
            [tuple(pairs.values())]
        )
        self.connection.commit()

    def selectWhere(self, tbl, **pairs):
        ntuple = table_columns[tbl]
        condition = ' AND '.join(
            f'{key}={repr(val)}' for key, val in pairs.items()
        )
        self.cursor.execute(f'SELECT * FROM {tbl.name} WHERE {condition}')
        return [ntuple(*row) for row in self.cursor.fetchall()]

    def selectColumns(self, tbl, cols):
        self.cursor.execute(f'SElECT {",".join(cols)} FROM {tbl.name}')
        return self.cursor.fetchall()

    def getTable(self, tbl):
        self.cursor.execute(f'SELECT * FROM {tbl.name}')
        return table_columns[tbl]._fields, self.cursor.fetchall()