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

    async def sendOutQueue(self, public, private):
        for out in public:
            for player in self.players:
                player.send(out)
        for out in private:
            player = self.players.getPlayerById(out.user_id)
            if player: player.send(out)

    def emptyOutQueue(self):
        public_out_queue = self.round.public_out_queue.copy()
        public_out_queue.clear()
        private_out_queue = self.round.public_out_queue.copy()
        private_out_queue.clear()
        return (
            [dict(out._asdict()) for out in private_out_queue], 
            [dict(out._asdict()) for out in public_out_queue]
        )
    
    async def takeAction(self, action_id, **kwargs):
        if action_id == TableAction.STARTROUND:
            status = self.newRound(0)
            if status:
                await self.sendOutQueue(*self.emptyOutQueue())
                if self.round: 
                    await self.sendToAll({
                        'id': PublicOutId.NEWROUND, 
                        'data': {
                            'button_id': self.round.button,
                            'current_id': self.round.current_index
                        }
                    })
                        

class ServerGame(Game):
    pass