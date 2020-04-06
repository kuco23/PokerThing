from collections import namedtuple
import sqlite3

make_accounts_table = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL CHECK(length(password_hash) = 64),
    email TEXT NOT NULL,
    money INTEGER NOT NULL
) 
"""

user_table_cols = namedtuple(
    'accounts_row',
    ['id', 'username', 'password_hash', 'email', 'money']
)

rowtuples = {
    'accounts': user_table_cols
}

def createUserTable(connection, overwrite=False):
    cursor = connection.cursor()
    if overwrite:
        cursor.execute("DROP TABLE IF EXISTS accounts")
    cursor.execute(make_accounts_table)
    connection.commit()

def insert(connection, tbl, **pairs):
    keys = ','.join(pairs.keys())
    ques = ','.join(['?'] * len(pairs))
    cursor = connection.cursor()
    cursor.executemany(
        f'INSERT INTO {tbl} ({keys}) VALUES ({ques})',
        [tuple(pairs.values())]
    )
    connection.commit()

def selectWhere(connection, tbl, **pairs):
    ntuple = rowtuples[tbl]
    condition = ' AND '.join(
        f'{key}={repr(val)}' for key, val in pairs.items()
    )
    cursor = connection.cursor()
    cursor.execute(f'SELECT * FROM {tbl} WHERE {condition}')
    return [ntuple(*row) for row in cursor.fetchall()]

def selectColumn(connection, tbl, colname):
    cursor = connection.cursor()
    cursor.execute(f'SElECT {colname} FROM {tbl}')
    return [elt for elt, *_ in cursor.fetchall()]

if __name__ == '__main__':
    with sqlite3.connect('app/database/game.db') as conn:
        createUserTable(conn, overwrite=True)

