from collections import namedtuple, deque
from json import dumps
from .pokerlib.enums import *
from .pokerlib import Game, Player, Round, Table

class ServerPlayer(Player):

    def __init__(self, *args, sock):
        super(*args)
        self.sock = sock

    def send(self, data):
        jsned = dumps(data)
        sock.send(jsned)

class ServerRound(Round):
    __cards = [[j, i] for i in range(4) for j in range(13)]
    pass

class ServerTable(Table):

    def sendToAll(self, data):
        for player in self.players:
            player.send(data)

    def sendOutQueue(self, public, private):
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
    
    def takeAction(self, action_id, **kwargs):
        if action_id == TableAction.STARTROUND:
            status = self.newRound(0)
            if status:
                self.sendOutQueue(*self.emptyOutQueue())
                if self.round: 
                    self.sendToAll({
                        'id': PublicOutId.NEWROUND, 
                        'data': {
                            'button_id': self.round.button_id,
                            'current_id': self.round.current_id
                        }
                    })
                        

class ServerGame(Game):
    pass