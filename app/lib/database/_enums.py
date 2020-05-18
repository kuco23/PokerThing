from aenum import Enum, IntEnum

class DbTable(Enum):
    ACCOUNTS = 'accounts'
    POKERTABLES = 'pokertables'
    PLAYERS = 'players'
    ROUNDS = 'rounds'
    BOARDS = 'boards'
    PLAYERCARDS = 'playercards'
    PLAYERACTIONS = 'playeractions'

class DbPlayerTurn(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3

class DbPlayerAction(IntEnum):
    SMALLBLIND = 0
    BIGBLIND = 1
    FOLD = 2
    CHECK = 3
    CALL = 4
    RAISE = 5
    ALLIN = 6

table_enum = dict(zip(
    (table.value for table in DbTable), DbTable
))