from json import dumps
from .pokerlib import Game, Player, Round, Table, PlayerGroup
from ._gamedb import *
from ._enums import (
    ServerCode, ClientCode, TableCode, 
    DbTable, DbPlayerTurn, DbPlayerAction
)

class ServerPlayer(Player):

    def __init__(self, account_id, table_id, _id, name, money, sock):
        super().__init__(table_id, _id, name, money)
        self.account_id = account_id
        self.sock = sock

    async def send(self, data):
        data['id'] = int(data['id'])
        jsned = dumps(data)
        await self.sock.send(jsned)

class ServerPlayerGroup(PlayerGroup):
    pass

class ServerRound(Round):
    __cards = [[j, i] for i in range(4) for j in range(13)]

    def publicOut(self, out_id, **kwargs):
        kwargs.update({'turn_id': self.turn})
        out = self.PublicOut(out_id, kwargs)
        self.public_out_queue.append(out)

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
        for player in self.players:
            player.send(data)

    def _popRoundQueue(self):
        public_out_queue = self.round.public_out_queue.copy()
        public_out_queue.clear()
        private_out_queue = self.round.public_out_queue.copy()
        private_out_queue.clear()
        return private_out_queue, public_out_queue
    
    async def _processRoundQueue(self):
        private, public = self._popRoundQueue()
        for out in private: 
            self.executeRoundOut(out.id, out.player_id, **out.data)
        for out in public: 
            self.executeRoundOut(out.id, None, **out.data)
    
    async def _onPlayerAdd(self, username, sock):
        account_id = self.gamebase.accountIdFromUsername(username)
        player_id, withdrawn = self.gamebase.registerPlayer(
            username, self.id, self.buyin
        )
        self._addPlayers([ServerPlayer(
            account_id, self.id, player_id, 
            username, withdrawn, sock
        )])
        self.notifyAll({
            "id": ServerCode.INTRODUCEPLAYER,
            "data": {
                "player_id": player_id,
                "player_name": username,
                "player_money": withdrawn
            }
        })
    
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

    async def _onNewRound(self, player_id):
        self.notifyAll({"id": ServerCode.NEWROUND})
    
    async def _onNewTurn(self, turn, table):
        self.gamebase.insertBoard(
            self.round_id, turn.value, table
        )
        self.notifyAll({
            "id": ServerCode.NEWTURN,
            "data": {
                "turn": turn.value,
                "table": table
            }
        })
    
    async def _onDealtCards(self, player_id, cards):
        self.gamebase.insertPlayerCards(
            self.round_id, player_id, cards
        )
        player = self.all_players.getPlayerById(player_id)
        if player: player.send({
            "id": ServerCode.DEALTCARDS,
            "data": {
                "player_id": player_id,
                "cards": cards
            }
        })
    
    async def _onSmallBlind(self, player_id, stake):
        self.gamebase.insertPlayerAction(
            self.round_id, player_id, 
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

    async def _onBigBlind(self, player_id, stake):
        self.gamebase.insertPlayerAction(
            self.round_id, player_id, 
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
    
    async def _onPlayerAmountToCall(self, player_id, to_call):
        player = self.all_players.getPlayerById(player_id)
        if player: player.send({
            "id": ServerCode.PLAYERAMOUNTTOCALL,
            "data": {
                "player_id": player_id,
                "to_call": to_call
            }
        })
    
    async def _onPlayerFold(self, player_id, turn_id):
        self.insertPlayerAction(
            self.round_id, player_id, turn_id, 
            DbPlayerAction.FOLD
        )
        self.notifyAll({
            "id": ServerCode.PLAYERFOLD,
            "data": {
                "player_id": player_id
            }
        })
    
    async def _onPlayerCheck(self, player_id, turn_id):
        self.insertPlayerAction(
            self.round_id, player_id, turn_id,
            DbPlayerAction.CHECK
        )
        self.notifyAll({
            "id": ServerCode.PLAYERCHECK,
            "data": {
                "player_id": player_id
            }
        })
    
    async def _onPlayerCall(self, player_id, called, turn_id):
        self.insertPlayerAction(
            self.round_id, player_id, turn_id,
            DbPlayerAction.CALL, called
        )
        self.notifyAll({
            "id": ServerCode.PLAYERCALL,
            "data": {
                "player_id": player_id,
                "called": called
            }
        })
    
    async def _onPlayerRaise(self, player_id, raised_by, turn_id):
        self.insertPlayerAction(
            self.round_id, player_id, turn_id,
            DbPlayerAction.RAISE, raised_by
        )
        self.notifyAll({
            "id": ServerCode.PLAYERRAISE,
            "data": {
                "player_id": player_id,
                "raised_by": raised_by
            }
        })
    
    async def _onPlayerAllin(self, player_id, allin_stake, turn_id):
        self.insertPlayerAction(
            self.round_id, player_id, turn_id,
            DbPlayerAction.ALLIN, allin_stake
        )
        self.notifyAll({
            "id": ServerCode.PLAYERALLIN,
            "data": {
                "player_id": player_id,
                "allin_stake": allin_stake
            }
        })
    
    async def _onPublicCardShow(self, player_id, turn_id):
        self.notifyAll({
            "id": ServerCode.PUBLICCARDSHOW,
            "data": {
                player.id: player.cards
                for player in self.round.players
            }
        })
    
    async def _onDeclarePrematureWinner(
        self, player_id, won, kickers, turn_id
    ):
        self.notifyAll({
            "id": ServerCode.PREMATUREWINNER,
            "data": {
                "player_id": player_id,
                "won": won,
                "kickers": kickers
            }
        })
    
    async def executeTableIn(self, code_id, player_id, **data):
        if code_id == TableCode.PLAYERJOINED:
            self._onPlayerAdd()
            if not self.round and self: 
                self._onStartRound()
        elif code_id == TableCode.PLAYERLEFT:
            self._onPlayerLeft()
        elif code_id == TableCode.STARTROUND:
            self._onStartRound()
    
    async def executeRoundOut(self, code_id, player_id, **data):
        if code_id == ServerCode.NEWROUND:
            self._onNewRound()
        elif code_id == ServerCode.DEALTCARDS:
            self._onDealtCards(player_id, data)
        elif code_id == ServerCode.NEWTURN:
            self._onNewTurn()
        elif code_id == ServerCode.SMALLBLIND:
            self._onSmallBlind()
        elif code_id == ServerCode.BIGBLIND:
            self._onBigBlind()
        elif code_id == ServerCode.PLAYERAMOUNTTOCALL:
            self._onAmountToCall()
        elif code_id == ServerCode.PLAYERFOLD:
            self._onPlayerFold()
        elif code_id == ServerCode.PLAYERCHECK:
            self._onPlayerCheck()
        elif code_id == ServerCode.PLAYERCALL:
            self._onPlayerCall()
        elif code_id == ServerCode.PLAYERRAISE:
            self._onPlayerRaise()
        elif code_id == ServerCode.PLAYERALLIN:
            self._onPlayerAllin()
        elif code_id == ServerCode.PUBLICCARDSHOW:
            self._onPlayerPublicCardShow()
        elif code_id == ServerCode.DECLAREPREMATUREWINNER:
            self._onDeclarePrematureWinner()
        elif code_id == ServerCode.DECLAREFINISHEDWINNER:
            self._onDeclareFinishedWinner()
        elif code_id == ServerCode.ROUNDFINISHED:
            self._onRoundFinished()               

class ServerGame(Game):
    pass