from collections import namedtuple, deque
from json import dumps
from .pokerlib import Game, Player, Round, Table, PlayerGroup
from ._enums import *

class ServerPlayer(Player):

    def __init__(self, table_id, _id, name, money, sock):
        super().__init__(table_id, _id, name, money)
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

    async def sendToAll(self, data):
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
    
    async def _addPlayer(self, table_id, _id, name, money, sock):
        player = ServerPlayer(table_id, _id, name, money, sock)
        self += [player]
        player.send({
            'id': ServerCode.INTRODUCEPLAYER,
            'data': {
                'player_id': player.id,
                'player_name': name,
                'player_money': money
            }
        })
    
    async def _startRound(self):
        while self.newRound(0):
            if self.round is not None:
                private, public = self._popRoundQueue()
                for out in private:
                    self.execute(out['id'], out['user_id'], **out['data'])
                for out in public: 
                    self.execute(out['id'], None, **out['data'])
    
    async def _dealtCards(self, user_id, data):
        player = self.players.getPlayerById(user_id)
        if player: player.send(data)
    
    async def _newRound(self, user_id):
        self.sendToAll({"id": ServerCode.NEWROUND})
    
    async def _smallBlind(self, user_id):
        
    
    async def execute(self, action_id, user_id, **data):
        if action_id == TableCode.NEWPLAYER:
            self._addPlayer()
            if not self.round and self: self._startRound()
        elif action_id == TableCode.STARTROUND:
            self._startRound()
        elif action_id == ServerCode.DEALTCARDS:
            self._dealtCards(user_id, data)
        elif action_id == ServerCode.NEWROUND:
            self._newRound()
        elif action_id == ServerCode.SMALLBLIND:
            self._smallBlind()
        
            
        
            
        
                        

class ServerGame(Game):
    pass