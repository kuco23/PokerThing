from enum import Enum, IntEnum

class DbTable(Enum):
    ACCOUNTS = 'accounts'
    POKERTABLES = 'pokertables'
    PLAYERS = 'players'
    ACTIONS = 'actions'

class TableAction(IntEnum):
    STARTROUND = 0
