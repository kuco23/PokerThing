from .enums import *
from ._round import Round
from ._player import Player, PlayerGroup
from ._table import Table

class Game:

    def __init__(self):
        self.tables = dict()

    def __iadd__(self, table):
        self.tables[table.id] = table
        return self

    def __getitem__(self, table_id):
        return self.tables[table_id]