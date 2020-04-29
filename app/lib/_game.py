from json import dumps
from .pokerlib import Game, Player, Round, Table, PlayerGroup
from ._gamedb import *
from ._enums import (
    ServerCode, ClientCode, TableCode, 
    DbTable, DbPlayerTurn, DbPlayerAction,
    RoundPublicInId, RoundPublicOutId, 
    RoundPrivateOutId
)

class ServerPlayer(Player):

    def __init__(
        self, account_id, table_id, 
        _id, name, money, sock
    ):
        super().__init__(table_id, _id, name, money)
        self.account_id = account_id
        self.sock = sock

    async def send(self, data):
        data['id'] = int(data['id'])
        jsned = dumps(data)
        await self.sock.send(jsned)

class ServerPlayerGroup(PlayerGroup): pass

class ServerRound(Round):
    __cards = [[j, i] for i in range(4) for j in range(13)]

    def privateOut(self, user_id, out_id, **kwargs):
        if out_id == RoundPrivateOutId.DEALTCARDS:
            player = self.players.getPlayerById(user_id)
            kwargs.update({'cards': player.cards})
        super().privateOut(self, user_id, out_id, kwargs)

    def publicOut(self, out_id, **kwargs):
        kwargs.update({
            'turn_id': self.turn, 
            'round_id': self.round,
        })
        if out_id == RoundPublicOutId.DECLAREFINISHEDWINNER:
            player = self.players.getPlayerById(
                kwargs['player_id'] # format hand description!
            )
            kwargs.update({'hand': player.hand.handenum})
        elif out_id == RoundPublicOutId.PUBLICCARDSHOW:
            player = self.players.getPlayerById(
                kwargs['player_id']
            )
            kwargs.update({'cards': player.cards})
        super().publicOut(self, out_id, **kwargs)

# serves the table, by translating the Client and Server
# codes into round input and vice-versa
class ServerTable(Table):
    Round = ServerRound

    def __init__(
        self, db, _id, players, 
        buyin, small_blind, big_blind
    ):
        super().__init__(
            self, _id, players, buyin, 
            small_blind, big_blind
        )
        self.gamebase = db
        self.round_id = self.gamebase.startRound()

    async def notifyAll(self, data):
        for player in self.players: player.send(data)

    def _popRoundQueue(self):
        public_out_queue = self.round.public_out_queue.copy()
        self.round.public_out_queue.clear()
        private_out_queue = self.round.public_out_queue.copy()
        self.round.private_out_queue.clear()
        return private_out_queue, public_out_queue
    
    async def _processRoundQueue(self):
        private, public = self._popRoundQueue()
        for out in private: 
            self.executeRoundOut(
                out.id, out.player_id, **out.data
            )
        for out in public: 
            self.executeRoundOut(out.id, None, **out.data)
    
    async def _onPlayerAdd(self, username, sock):
        account_id = self.gamebase.accountIdFromUsername(
            username
        )
        player_id, withdrawn = self.gamebase.registerPlayer(
            username, self.id, self.buyin
        )
        player = ServerPlayer(
            account_id, self.id, player_id,
            username, withdrawn, sock
        )
        player.send({
            "id": ServerCode.PLAYERSETUP,
            "data": {
                "player_id": player_id,
                "player_name": username,
                "player_money": withdrawn
            }
        })
        self.notifyAll({
            "id": ServerCode.PLAYERJOINED,
            "data": {
                "player_id": player_id,
                "player_name": username,
                "player_money": withdrawn
            }
        })
        self._addPlayers([player])

        self._addPlayers([ServerPlayer(
            account_id, self.id, player_id, 
            username, withdrawn, sock
        )])
        
    
    async def _onPlayerLeft(self, player_id):
        player = self.all_players.getPlayerById(player_id)
        if player is not None: 
            self._removePlayers([player])    
            self.gamebase.unregisterPlayer(
                player.account_id, self.id
            )
    
    async def _onStartRound(self):
        while self.newRound(self.round_id):
            self.round_id = self.gamebase.startRound()
            if self.round is not None:
                self._processRoundQueue()

    async def _onNewRound(self):
        self.notifyAll({"id": ServerCode.NEWROUND})
    
    async def _onNewTurn(self, turn, table, round_id):
        self.gamebase.insertBoard(
            round_id, turn.value, table
        )
        self.notifyAll({
            "id": ServerCode.NEWTURN,
            "data": {
                "turn": turn.value,
                "table": table
            }
        })
    
    async def _onDealtCards(
        self, player_id, cards, round_id
    ):
        self.gamebase.insertPlayerCards(
            round_id, player_id, cards
        )
        player = self.all_players.getPlayerById(player_id)
        if player: player.send({
            "id": ServerCode.DEALTCARDS,
            "data": {
                "cards": cards
            }
        })
    
    async def _onSmallBlind(
        self, player_id, stake, round_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, 
            DbPlayerTurn.PREFLOP.value, 
            DbPlayerAction.SMALLBLIND.value, 
            stake
        )
        self.notifyAll({
            "id": ServerCode.SMALLBLIND,
            "data": {
                "player_id": player_id,
                "small_blind": self.small_blind,
                "stake": stake
            }
        }) 

    async def _onBigBlind(
        self, player_id, stake, round_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, 
            DbPlayerTurn.PREFLOP.value, 
            DbPlayerAction.BIGBLIND.value, 
            stake
        )
        self.notifyAll({
            "id": ServerCode.BIGBLIND,
            "data": {
                "player_id": player_id,
                "big_blind": self.big_blind,
                "stake": stake
            }
        })
    
    async def _onPlayerAmountToCall(
        self, player_id, to_call
    ):
        player = self.all_players.getPlayerById(player_id)
        if player: player.send({
            "id": ServerCode.PLAYERAMOUNTTOCALL,
            "data": {
                "player_id": player_id,
                "to_call": to_call
            }
        })
    
    async def _onPlayerFold(
        self, player_id, round_id, turn_id
    ):
        self.insertPlayerAction(
            round_id, player_id, turn_id, 
            DbPlayerAction.FOLD
        )
        self.notifyAll({
            "id": ServerCode.PLAYERFOLD,
            "data": {
                "player_id": player_id
            }
        })
    
    async def _onPlayerCheck(
        self, player_id, round_id, turn_id
    ):
        self.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.CHECK
        )
        self.notifyAll({
            "id": ServerCode.PLAYERCHECK,
            "data": {
                "player_id": player_id
            }
        })
    
    async def _onPlayerCall(
        self, player_id, called, round_id, turn_id
    ):
        self.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.CALL, called
        )
        self.notifyAll({
            "id": ServerCode.PLAYERCALL,
            "data": {
                "player_id": player_id,
                "called": called
            }
        })
    
    async def _onPlayerRaise(
        self, player_id, raised_by, round_id, turn_id
    ):
        self.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.RAISE, raised_by
        )
        self.notifyAll({
            "id": ServerCode.PLAYERRAISE,
            "data": {
                "player_id": player_id,
                "raised_by": raised_by
            }
        })
    
    async def _onPlayerAllin(
        self, player_id, allin_stake, round_id, turn_id
    ):
        self.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.ALLIN, allin_stake
        )
        self.notifyAll({
            "id": ServerCode.PLAYERALLIN,
            "data": {
                "player_id": player_id,
                "allin_stake": allin_stake
            }
        })
    
    async def _onPublicCardShow(self, player_id, cards):
        player = self.players.getPlayerById()
        self.notifyAll({
            "id": ServerCode.PUBLICCARDSHOW,
            "data": {
                "player_id": player_id,
                "cards": player.cards
            }
        })
    
    async def _onDeclarePrematureWinner(
        self, player_id, won
    ):
        self.notifyAll({
            "id": ServerCode.DECLAREPREMATUREWINNER,
            "data": {
                "player_id": player_id,
                "won": won
            }
        })
    
    # log winners + winnings into database
    async def _onDeclareFinishedWinner(
        self, player_id, won, hand, kickers, turn_id
    ):
        self.notifyAll({
            "id": ServerCode.DECLAREFINISHEDWINNER,
            "data": {
                "player_id": player_id,
                "won": won,
                "kickers": kickers
            }
        })
    
    async def _onRoundFinished(self): 
        self.notifyAll({
            "id": ServerCode.ROUNDFINISHED
        })
    
    async def executeTableIn(self, code_id, player_id, **data):
        if code_id == TableCode.PLAYERJOINED:
            self._onPlayerAdd(
                player_id, 
                data['name'], data['sock']
            )
        elif code_id == TableCode.PLAYERLEFT:
            self._onPlayerLeft(player_id)
        elif code_id == TableCode.STARTROUND:
            self._onStartRound()
    
    async def executeRoundIn(self, code_id, player_id, **data):
        if code_id == ClientCode.FOLD:
            self.round.publicIn(
                player_id, RoundPublicInId.FOLD
            )
        elif code_id == ClientCode.CHECK:
            self.round.publicIn(
                player_id, RoundPublicInId.CHECK
            )
        elif code_id == ClientCode.CALL:
            self.round.publicIn(
                player_id, RoundPublicInId.CALL
            )
        elif code_id == ClientCode.RAISE:
            self.round.publicIn(
                player_id, RoundPublicInId.RAISE, 
                data['raised_by']
            )
        elif code_id == ClientCode.ALLIN:
            self.round.publicIn(
                player_id, RoundPublicInId.ALLIN
            )
        self._processRoundQueue()

    # should probably a private method
    async def executeRoundOut(self, code_id, player_id, **data):
        if code_id == RoundPublicOutId.NEWROUND:
            self._onNewRound()
        elif code_id == RoundPublicOutId.DEALTCARDS:
            self._onDealtCards(
                player_id, 
                data['cards'], data['round_id']
            )
        elif code_id == RoundPublicOutId.NEWTURN:
            self._onNewTurn(
                data['turn'], data['table'], 
                data['round_id']
            )
        elif code_id == RoundPublicOutId.SMALLBLIND:
            self._onSmallBlind(
                data['player_id'], data['turn_stake']
            )
        elif code_id == RoundPublicOutId.BIGBLIND:
            self._onBigBlind(
                data['player_id'], data['turn_stake'],
                data['round_id']
            )
        elif code_id == RoundPublicOutId.PLAYERAMOUNTTOCALL:
            self._onPlayerAmountToCall(
                data['player_id'], data['to_call']
            )
        elif code_id == RoundPublicOutId.PLAYERFOLD:
            self._onPlayerFold(
                data['player_id'], data['round_id'],
                data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERCHECK:
            self._onPlayerCheck(
                data['player_id'], data['round_id'],
                data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERCALL:
            self._onPlayerCall(
                data['player_id'], data['called'], 
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERRAISE:
            self._onPlayerRaise(
                data['player_id'], data['raised_by'],
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERALLIN:
            self._onPlayerAllin(
                data['player_id'], data['all_in_stake'],
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PUBLICCARDSHOW:
            self._onPublicCardShow(
                data['player_id'], data['cards']
            )
        elif code_id == RoundPublicOutId.DECLAREPREMATUREWINNER:
            self._onDeclarePrematureWinner(
                data['player_id'], data['money_won']
            )
        elif code_id == RoundPublicOutId.DECLAREFINISHEDWINNER:
            self._onDeclareFinishedWinner(
                data['player_id'], data['money_won'],
                data['hand'], data['kickers'], 
                data['turn_id']
            )
        elif code_id == RoundPublicOutId.ROUNDFINISHED:
            self._onRoundFinished()               

class ServerGame(Game): pass