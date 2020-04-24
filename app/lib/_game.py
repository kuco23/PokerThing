from json import dumps
from .pokerlib import Game, Player, Round, Table, PlayerGroup
from ._gamedb import *
from ._enums import ServerCode, ClientCode, TableCode, DbTable

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

class ServerTable(Table):
    Round = ServerRound

    def __init__(self, db, _id, players, buyin, small_blind, big_blind):
        super().__init__(self, _id, players, buyin, small_blind, big_blind)
        self.gamebase = db

    async def notifyAll(self, data):
        for player in self.players:
            player.send(data)

    def _popRoundQueue(self):
        public_out_queue = self.round.public_out_queue.copy()
        public_out_queue.clear()
        private_out_queue = self.round.public_out_queue.copy()
        private_out_queue.clear()
        return (
            [dict(out._asdict()) for out in private_out_queue], 
            [dict(out._asdict()) for out in public_out_queue]
        )
    
    async def _processRoundQueue(self):
        private, public = self._popRoundQueue()
        for out in private: 
            self.executeRoundOut(out['id'], out['user_id'], **out['data'])
        for out in public: 
            self.executeRoundOut(out['id'], None, **out['data'])
    
    async def _onPlayerAdd(self, username, sock):
        account_id = self.gamebase.accountIdFromUsername(username)
        player_id, withdrawn = self.gamebase.registerPlayer(
            username, self.id, self.buyin
        )
        self._addPlayers([ServerPlayer(
            account_id, self.id, player_id, username, withdrawn, sock
        )])
        self.notifyAll({
            'id': ServerCode.INTRODUCEPLAYER,
            'data': {
                'player_id': player_id,
                'player_name': username,
                'player_money': withdrawn
            }
        })
    
    async def _onPlayerLeft(self, user_id):
        player = self.all_players.getPlayerById(user_id)
        if player is not None: 
            self.gamebase.unregisterPlayer(player.account_id, self.id)
            self._removePlayers([player])    
    
    async def _onStartRound(self):
        while self.newRound(0):
            if self.round is not None:
                self._processRoundQueue()

    async def _onNewRound(self, user_id):
        self.notifyAll({"id": ServerCode.NEWROUND})
    
    async def _onDealtCards(self, user_id, cards):
        player = self.all_players.getPlayerById(user_id)
        if player: player.send({
            "id": ServerCode.DEALTCARDS,
            "data": {
                "user_id": user_id,
                "cards": cards
            }
        })
    
    async def _onSmallBlind(self, user_id, stake):
        self.notifyAll({
            "id": ServerCode.SMALLBLIND,
            "data": {
                "user_id": user_id,
                "small_blind": self.small_blind,
                "stake": stake
            }
        }) 

    async def _onBigBlind(self, user_id, stake):
        self.notifyAll({
            "id": ServerCode.BIGBLIND,
            "data": {
                "user_id": user_id,
                "big_blind": self.big_blind,
                "stake": stake
            }
        })
    
    async def _onPlayerAmountToCall(self, user_id, to_call):
        player = self.all_players.getPlayerById(user_id)
        if player: player.send({
            "id": ServerCode.PLAYERAMOUNTTOCALL,
            "data": {
                "user_id": user_id,
                "to_call": to_call
            }
        })
    
    async def _onPlayerFold(self, user_id):
        self.notifyAll({
            "id": ServerCode.PLAYERFOLD,
            "data": {
                "user_id": user_id
            }
        })
    
    async def _onPlayerCheck(self, user_id):
        self.notifyAll({
            "id": ServerCode.PLAYERCHECK,
            "data": {
                "user_id": user_id
            }
        })
    
    async def _onPlayerCheck(self, user_id, called):
        self.notifyAll({
            "id": ServerCode.PLAYERCALL,
            "data": {
                "user_id": user_id,
                "called": called
            }
        })
    
    async def _onPlayerRaise(self, user_id, raised_by):
        self.notifyAll({
            "id": ServerCode.PLAYERRAISE,
            "data": {
                "user_id": user_id,
                "raised_by": raised_by
            }
        })
    
    async def _onPlayerAllin(self, user_id, allin_stake):
        self.notifyAll({
            "id": ServerCode.PLAYERALLIN,
            "data": {
                "user_id": user_id,
                "allin_stake": allin_stake
            }
        })
    
    async def _onPublicCardShow(self, user_id):
        self.notifyAll({"id": ServerCode.PUBLICCARDSHOW})
    
    async def _onDeclarePrematureWinner(self, user_id, won, kickers):
        self.notifyAll({
            "id": ServerCode.PREMATUREWINNER,
            "data": {
                "user_id": user_id,
                "won": won,
                "kickers": kickers
            }
        })
    
    async def executeTableIn(self, code_id, user_id, **data):
        if code_id == TableCode.PLAYERJOINED:
            self._onPlayerAdd()
            if not self.round and self: 
                self._onStartRound()
        elif code_id == TableCode.PLAYERLEFT:
            self._onPlayerLeft()
        elif code_id == TableCode.STARTROUND:
            self._onStartRound()
    
    async def executeRoundOut(self, code_id, user_id, **data):
        if code_id == ServerCode.NEWROUND:
            self._onNewRound()
        elif code_id == ServerCode.DEALTCARDS:
            self._onDealtCards(user_id, data)
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