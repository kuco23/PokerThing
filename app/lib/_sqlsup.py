from collections import namedtuple
import sqlite3
from ._enums import DbTable

make_accounts_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.ACCOUNTS.value} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL CHECK(length(password_hash) = 64),
    email TEXT NOT NULL,
    money INTEGER NOT NULL
) 
"""
make_pokertables_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.POKERTABLES.value} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    blind INTEGER NOT NULL
)
"""
make_players_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.PLAYERS.value} (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    pokertable_id INTEGER,
    FOREIGN KEY (account_id) 
        REFERENCES {DbTable.ACCOUNTS.value}(id),
    FOREIGN KEY (pokertable_id) 
        REFERENCES {DbTable.POKERTABLES.value}(id)
)
"""
make_rounds_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.ROUNDS.value} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokertable_id INTEGER NOT NULL,
    FOREIGN KEY (pokertable_id)
        REFERENCES {DbTable.POKERTABLES.value}(id)
)
"""
make_boards_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.BOARDS.value} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL,
    turn_id INTEGER NOT NULL,
    cards TEXT NOT NULL,
    FOREIGN KEY (round_id)
        REFERENCES {DbTable.ROUNDS.value}(id)
)
"""
make_playercards_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.PLAYERCARDS.value} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    cards TEXT NOT NULL,
    FOREIGN KEY (round_id)
        REFERENCES {DbTable.ROUNDS.value}(id)
    FOREIGN KEY (account_id)
        REFERENCES {DbTable.ACCOUNTS.value}(id)
)
"""
make_actions_table = f"""
CREATE TABLE IF NOT EXISTS {DbTable.PLAYERACTIONS.value} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    round_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    turn_id INTEGER NOT NULL,
    action_id INTEGER NOT NULL,
    amount INTEGER DEFAULT 0,
    FOREIGN KEY (round_id)
        REFERENCES {DbTable.ROUNDS.value}(id)
    FOREIGN KEY (account_id) 
        REFERENCES {DbTable.PLAYERACTIONS.value}(id)
)
"""

dbtables = dict(zip(
    DbTable, [
        make_accounts_table,
        make_pokertables_table,
        make_players_table,
        make_rounds_table,
        make_boards_table,
        make_playercards_table,
        make_actions_table
    ]
))

table_columns = dict(zip(DbTable, map(
    namedtuple, [table.value for table in DbTable], [
        ['id', 'username', 'password_hash', 'email', 'money'],
        ['id', 'blind'], 
        ['id', 'account_id', 'pokertable_id'],
        ['id', 'pokertable_id'],
        ['id', 'turn_id', 'round_id', 'cards'],
        ['id', 'round_id', 'account_id', 'cards'],
        ['id', 'timestamp', 'round_id', 'account_id', 
        'turn_id', 'action_id', 'amount'],
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
            sql = "DROP TABLE IF EXISTS " + tbl.value
            self.cursor.execute(sql)
        self.cursor.execute(make_table)
        self.connection.commit()

    def insert(self, tbl, **pairs):
        keys = ','.join(pairs.keys())
        ques = ','.join(['?'] * len(pairs))
        self.cursor.executemany(
            f'INSERT INTO {tbl.value} ({keys}) VALUES ({ques})',
            [tuple(pairs.values())]
        )
        self.connection.commit()

    def selectWhere(self, tbl, **pairs):
        ntuple = table_columns[tbl]
        condition = ' AND '.join(
            f'{key}={repr(val)}' for key, val in pairs.items()
        )
        self.cursor.execute(f'SELECT * FROM {tbl.value} WHERE {condition}')
        return [ntuple(*row) for row in self.cursor.fetchall()]

    def selectColumns(self, tbl, cols):
        self.cursor.execute(f'SElECT {",".join(cols)} FROM {tbl.value}')
        return self.cursor.fetchall()

    def getTable(self, tbl):
        self.cursor.execute(f'SELECT * FROM {tbl.value}')
        return table_columns[tbl]._fields, self.cursor.fetchall()