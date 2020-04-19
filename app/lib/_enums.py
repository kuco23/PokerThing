from enum import Enum, IntEnum
from .pokerlib.enums import PublicOutId, TableAction

class ServerCode:
    MESSAGE = -6,
    DEALTCARDS = 0,
    NEWROUND = 1,
    ROUNDFINISHED = 2,
    NEWTURN = 3,
    SMALLBLIND = 4,
    BIGBLIND = 5,
    PLAYERFOLD = 6,
    PLAYERCHECK = 7,
    PLAYERCALL = 8,
    PLAYERRAISE = 9,
    PLAYERALLIN = 10,
    PLAYERAMOUNTTOCALL = 11,
    DECLAREPREMATUREWINNER = 12,
    DECLAREFINISHEDWINNER = 13,
    PUBLICCARDSHOW = 14

class ClientCode:
    MESSAGE = -6
    FOLD = -5,
    CHECK = -4,
    CALL = -3,
    RAISE = -2,
    ALLIN = -1,

class DbTable(Enum):
    ACCOUNTS = 'accounts'
    POKERTABLES = 'pokertables'
    PLAYERS = 'players'
    ACTIONS = 'actions'
