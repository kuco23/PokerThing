from collections import namedtuple
import sqlite3
from .database import DbTable, dbtables, table_columns

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