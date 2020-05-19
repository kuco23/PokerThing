from collections import namedtuple
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
    player_id INTEGER NOT NULL,
    turn_id INTEGER NOT NULL,
    action_id INTEGER NOT NULL,
    amount INTEGER DEFAULT 0,
    FOREIGN KEY (round_id)
        REFERENCES {DbTable.ROUNDS.value}(id)
    FOREIGN KEY (player_id) 
        REFERENCES {DbTable.PLAYERS.value}(id)
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
        ['id', 'timestamp', 'round_id', 'player_id', 
        'turn_id', 'action_id', 'amount']
    ]
)))

table_read_columns = dict(zip(DbTable, map(
    namedtuple, [table.value for table in DbTable], [
        ['username', 'email', 'money'],
        ['blind'],
        ['account_id', 'pokertable_id'],
        ['pokertable_id'],
        ['turn_id', 'round_id', 'cards'],
        ['round_id', 'account_id', 'cards'],
        ['timestamp', 'round_id', 'player_id', 
        'turn_id', 'action_id', 'amount']
    ]
)))