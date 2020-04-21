from aenum import Enum, IntEnum, extend_enum
from .pokerlib.enums import (
    PublicOutId, PrivateOutId, PlayerActionId
)

class ServerCode(IntEnum):
    MESSAGE = -6
    INTRODUCEPLAYER = 16

for e in PublicOutId:
    extend_enum(ServerCode, e.name, e.value)
for e in PrivateOutId:
    extend_enum(ServerCode, e.name, e.value)

class ClientCode(IntEnum):
    MESSAGE = -6

for e in PlayerActionId:
    extend_enum(ClientCode, e.name, e.value)

class TableCode(IntEnum):
    NEWPLAYER = 100
    STARTROUND = 101

class DbTable:
    ACCOUNTS = 'accounts'
    POKERTABLES = 'pokertables'
    PLAYERS = 'players'
    ACTIONS = 'actions'
