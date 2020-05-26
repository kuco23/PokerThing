from aenum import Enum, IntEnum, extend_enum
from .pokerlib.enums import (
    RoundPublicOutId, RoundPrivateOutId, 
    RoundPublicInId, Turn
)

class ServerGameCode(IntEnum):
    MESSAGE = -6
    PLAYERSETUP = 16
    PLAYERLEFT = 17
    PLAYERSUPDATE = 18
    PLAYERSBOUGHTIN = 19

for e in RoundPublicOutId:
    extend_enum(ServerGameCode, e.name, e.value)
for e in RoundPrivateOutId:
    extend_enum(ServerGameCode, e.name, e.value)

class ClientGameCode(IntEnum):
    MESSAGE = -6
    TABLEID = -5

for e in RoundPublicInId: 
    extend_enum(ClientGameCode, e.name, e.value)

class TableCode(IntEnum):
    PLAYERJOINED = 100
    STARTROUND = 101
    PLAYERLEFT = 102


class ClientDbCode(IntEnum):
    GETTABLE = 0
    GETPLAYER = 1
    
    