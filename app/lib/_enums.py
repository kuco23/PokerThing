from aenum import Enum, IntEnum, extend_enum
from .pokerlib.enums import (
    RoundPublicOutId, RoundPrivateOutId, 
    RoundPublicInId, Turn
)

class ServerCode(IntEnum):
    MESSAGE = -6
    PLAYERJOINED = 16
    PLAYERSETUP = 17
    PLAYERLEFT = 18

for e in RoundPublicOutId:
    extend_enum(ServerCode, e.name, e.value)
for e in RoundPrivateOutId:
    extend_enum(ServerCode, e.name, e.value)

class ClientCode(IntEnum):
    MESSAGE = -6

for e in RoundPublicInId: 
    extend_enum(ClientCode, e.name, e.value)

class TableCode(IntEnum):
    PLAYERJOINED = 100
    STARTROUND = 101
    PLAYERLEFT = 102

class DbTable(Enum):
    ACCOUNTS = 'accounts'
    POKERTABLES = 'pokertables'
    PLAYERS = 'players'
    ROUNDS = 'rounds'
    BOARDS = 'boards'
    PLAYERCARDS = 'playercards'
    PLAYERACTIONS = 'playeractions'

class DbPlayerTurn(IntEnum):
    pass

for e in Turn: 
    extend_enum(DbPlayerTurn, e.name, e.value)

class DbPlayerAction(IntEnum):
    SMALLBLIND = 0
    BIGBLIND = 1
    FOLD = 2
    CHECK = 3
    CALL = 4
    RAISE = 5
    ALLIN = 6
    
    