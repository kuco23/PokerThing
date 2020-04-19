from enum import IntEnum

class Value(IntEnum):
    TWO = 0
    THREE = 1
    FOUR = 2
    FIVE = 3
    SIX = 4
    SEVEN = 5
    EIGHT = 6
    NINE = 7
    TEN = 8
    JACK = 9
    QUEEN = 10
    KING = 11
    ACE = 12

class Suit(IntEnum):
    SPADE = 0
    CLUB = 1
    DIAMOND = 2
    HEART = 3

class Hand(IntEnum):
    HIGHCARD = 0
    ONEPAIR = 1
    TWOPAIR = 2
    THREEOFAKIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULLHOUSE = 6
    FOUROFAKIND = 7
    STRAIGHTFLUSH = 8
    

class Turn(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3

class PlayerActionId(IntEnum):
    FOLD = -5,
    CHECK = -4,
    CALL = -3,
    RAISE = -2,
    ALLIN = -1,

class PrivateOutId(IntEnum):
    DEALTCARDS = 0,

class PublicOutId(IntEnum):
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

class TableAction(IntEnum):
    STARTROUND = 15