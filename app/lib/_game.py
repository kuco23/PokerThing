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

    def privateOut(self, out_id, player_id, **kwargs):
        if out_id == RoundPrivateOutId.DEALTCARDS:
            player = self.players.getPlayerById(player_id)
            kwargs.update({
                'player_cards': player.cards,
                'player_name': player.name,
                'round_id': self.id
            })
        super().privateOut(player_id, out_id, **kwargs)

    def publicOut(self, out_id, **kwargs):
        kwargs.update({
            'turn_id': self.turn, 
            'round_id': self.id,
        })
        player_id = kwargs.get('player_id')
        if player_id is not None: 
            player = self.players.getPlayerById(player_id)
            kwargs['player_money'] = player.money
            kwargs['player_name'] = player.name
        if out_id == RoundPublicOutId.DECLAREFINISHEDWINNER:
            # format hand description
            kwargs['hand'] = player.hand.handenum
        elif out_id == RoundPublicOutId.PUBLICCARDSHOW:
            kwargs['player_cards'] = player.cards
        elif out_id == RoundPublicOutId.NEWTURN:
            kwargs['board_cards'] = self.board
        super().publicOut(out_id, **kwargs)

# serves the table, by translating the Client and Server
# codes into round input and vice-versa
class ServerTable(Table):
    Round = ServerRound
    PlayerSprite = ServerPlayerGroup

    def __init__(
        self, db, _id, seats, buyin, 
        small_blind, big_blind
    ):
        super().__init__(
            _id, seats, buyin, 
            small_blind, big_blind
        )
        self.gamebase = db
        self.round_id = self.gamebase.registerNewRound(_id)

    async def notifyAll(self, data):
        for player in self.players: await player.send(data)
    
    async def _processRoundQueue(self):
        private, public = self._popRoundQueue()
        for out in private: 
            out.data['player_id'] = out.player_id
            await self._executeRoundOut(out.id, **out.data)
        for out in public: 
            await self._executeRoundOut(out.id, **out.data)
    
    async def _onPlayerAdd(self, player_name, sock):
        account_id = self.gamebase.accountIdFromUsername(
            player_name
        )
        player_id, withdrawn = self.gamebase.registerPlayer(
            account_id, self.id, self.buyin
        )
        player = ServerPlayer(
            account_id, self.id, player_id,
            player_name, withdrawn, sock
        )
        await player.send({
            "id": ServerCode.PLAYERSETUP,
            "data": {
                "player_name": player_name,
                "player_money": withdrawn,
                "player_names": [
                    player.name for player in self.players
                ],
                "player_moneys": [
                    player.money for player in self.players
                ]
            }
        })
        await self.notifyAll({
            "id": ServerCode.PLAYERJOINED,
            "data": {
                "player_name": player_name,
                "player_money": withdrawn
            }
        })
        self._addPlayers([player])
        
    async def _onPlayerLeft(self, player_name):
        player = self.players.getPlayerByAttr(
            'name', player_name
        )
        if player is not None: 
            self._removePlayers([player])    
            self.gamebase.unregisterPlayer(
                player.account_id, self.id
            )
            await self.notifyAll({
                "id": ServerCode.PLAYERLEFT,
                "data": {
                    "player_name": player_name
                }
            })
    
    async def _onStartRound(self):
        while self.newRound(self.round_id):
            self.round_id = self.gamebase.registerNewRound(
                self.id
            )
            if self.round is not None:
                await self._processRoundQueue()

    async def _onNewRound(self):
        await self.notifyAll({"id": ServerCode.NEWROUND})
    
    async def _onNewTurn(self, turn, board, round_id):
        self.gamebase.insertBoard(
            round_id, turn.value, dumps(board)
        )
        await self.notifyAll({
            "id": ServerCode.NEWTURN,
            "data": {
                "turn": turn.value,
                "board_cards": board
            }
        })
    
    async def _onDealtCards(
        self, player_id, player_name, cards, round_id
    ):
        self.gamebase.insertPlayerCards(
            round_id, player_id, cards
        )
        player = self.players.getPlayerById(player_id)
        if player is not None: await player.send({
            "id": ServerCode.DEALTCARDS,
            "data": {
                "player_cards": cards,
                "player_name": player_name
            }
        })
    
    async def _onSmallBlind(
        self, player_id, player_name, 
        player_money, stake, round_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, 
            DbPlayerTurn.PREFLOP.value, 
            DbPlayerAction.SMALLBLIND.value, 
            stake
        )
        await self.notifyAll({
            "id": ServerCode.SMALLBLIND,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "small_blind": self.small_blind,
                "stake": stake
            }
        }) 

    async def _onBigBlind(
        self, player_id, player_name, 
        player_money, stake, round_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, 
            DbPlayerTurn.PREFLOP.value, 
            DbPlayerAction.BIGBLIND.value, 
            stake
        )
        await self.notifyAll({
            "id": ServerCode.BIGBLIND,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "big_blind": self.big_blind,
                "stake": stake
            }
        })
    
    async def _onPlayerAmountToCall(
        self, player_id, player_name, to_call
    ):
        await self.notifyAll({
            "id": ServerCode.PLAYERAMOUNTTOCALL,
            "data": {
                "player_name": player_name,
                "to_call": to_call
            }
        })
    
    async def _onPlayerFold(
        self, player_id, player_name, round_id, turn_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, turn_id, 
            DbPlayerAction.FOLD
        )
        await self.notifyAll({
            "id": ServerCode.PLAYERFOLD,
            "data": {
                "player_name": player_name
            }
        })
    
    async def _onPlayerCheck(
        self, player_id, player_name, round_id, turn_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.CHECK
        )
        await self.notifyAll({
            "id": ServerCode.PLAYERCHECK,
            "data": {
                "player_name": player_name
            }
        })
    
    async def _onPlayerCall(
        self, player_id, player_name, player_money, 
        called, round_id, turn_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.CALL, called
        )
        await self.notifyAll({
            "id": ServerCode.PLAYERCALL,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "called": called
            }
        })
    
    async def _onPlayerRaise(
        self, player_id, player_name, player_money, 
        raised_by, round_id, turn_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.RAISE, raised_by
        )
        await self.notifyAll({
            "id": ServerCode.PLAYERRAISE,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "raised_by": raised_by
            }
        })
    
    async def _onPlayerAllin(
        self, player_id, player_name, player_money, 
        allin_stake, round_id, turn_id
    ):
        self.gamebase.insertPlayerAction(
            round_id, player_id, turn_id,
            DbPlayerAction.ALLIN, allin_stake
        )
        await self.notifyAll({
            "id": ServerCode.PLAYERALLIN,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "allin_stake": allin_stake
            }
        })
    
    async def _onPublicCardShow(
        self, player_id, player_name, cards
    ):
        await self.notifyAll({
            "id": ServerCode.PUBLICCARDSHOW,
            "data": {
                "player_name": player_name,
                "player_cards": cards
            }
        })
    
    async def _onDeclarePrematureWinner(
        self, player_id, player_name, player_money, won
    ):
        await self.notifyAll({
            "id": ServerCode.DECLAREPREMATUREWINNER,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "won": won
            }
        })
    
    # log winners + winnings into database
    async def _onDeclareFinishedWinner(
        self, player_id, player_name, player_money, 
        won, hand, kickers, turn_id, round_id
    ):
        await self.notifyAll({
            "id": ServerCode.DECLAREFINISHEDWINNER,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "won": won,
                "hand": hand,
                "kickers": kickers
            }
        })
    
    async def _onRoundFinished(self): 
        await self.notifyAll({
            "id": ServerCode.ROUNDFINISHED
        })

    async def _executeRoundOut(self, code_id, **data):
        if code_id == RoundPublicOutId.NEWROUND:
            await self._onNewRound()
        elif code_id == RoundPrivateOutId.DEALTCARDS:
            await self._onDealtCards(
                data['player_id'], data['player_name'],
                data['player_cards'], data['round_id']
            )
        elif code_id == RoundPublicOutId.NEWTURN:
            await self._onNewTurn(
                data['turn'], data['board_cards'], 
                data['round_id']
            )
        elif code_id == RoundPublicOutId.SMALLBLIND:
            await self._onSmallBlind(
                data['player_id'], data['player_name'],
                data['player_money'], data['turn_stake'], 
                data['round_id']
            )
        elif code_id == RoundPublicOutId.BIGBLIND:
            await self._onBigBlind(
                data['player_id'], data['player_name'],
                data['player_money'], data['turn_stake'], 
                data['round_id']
            )
        elif code_id == RoundPublicOutId.PLAYERAMOUNTTOCALL:
            await self._onPlayerAmountToCall(
                data['player_id'], data['player_name'],
                data['to_call']
            )
        elif code_id == RoundPublicOutId.PLAYERFOLD:
            await self._onPlayerFold(
                data['player_id'], data['player_name'],
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERCHECK:
            await self._onPlayerCheck(
                data['player_id'], data['player_name'],
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERCALL:
            await self._onPlayerCall(
                data['player_id'], data['player_name'],
                data['player_money'], data['called'], 
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERRAISE:
            await self._onPlayerRaise(
                data['player_id'], data['player_name'],
                data['player_money'], data['raised_by'], 
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PLAYERALLIN:
            await self._onPlayerAllin(
                data['player_id'], data['player_name'],
                data['player_money'], data['all_in_stake'], 
                data['round_id'], data['turn_id']
            )
        elif code_id == RoundPublicOutId.PUBLICCARDSHOW:
            await self._onPublicCardShow(
                data['player_id'], data['player_name'],
                data['player_cards']
            )
        elif code_id == RoundPublicOutId.DECLAREPREMATUREWINNER:
            await self._onDeclarePrematureWinner(
                data['player_id'], data['player_name'],
                data['player_money'], data['money_won']
            )
        elif code_id == RoundPublicOutId.DECLAREFINISHEDWINNER:
            await self._onDeclareFinishedWinner(
                data['player_id'], data['player_name'], 
                data['player_money'], data['money_won'], 
                data['hand'], data['kickers'], 
                data['turn_id'], data['round_id']
            )
        elif code_id == RoundPublicOutId.ROUNDFINISHED:
            await self._onRoundFinished()    
    
    async def executeRoundIn(self, code_id, player_name, **data):
        player = self.players.getPlayerByAttr(
            'name', player_name
        )
        if code_id == ClientCode.FOLD:
            self.round.publicIn(
                player.id, RoundPublicInId.FOLD
            )
        elif code_id == ClientCode.CHECK:
            self.round.publicIn(
                player.id, RoundPublicInId.CHECK
            )
        elif code_id == ClientCode.CALL:
            self.round.publicIn(
                player.id, RoundPublicInId.CALL
            )
        elif code_id == ClientCode.RAISE:
            self.round.publicIn(
                player.id, RoundPublicInId.RAISE, 
                data['raised_by']
            )
        elif code_id == ClientCode.ALLIN:
            self.round.publicIn(
                player.id, RoundPublicInId.ALLIN
            )
        else: return
        await self._processRoundQueue()   

    async def executeTableIn(self, code_id, **data):
        if code_id == TableCode.PLAYERJOINED:
            await self._onPlayerAdd(
                data['username'], data['sock']
            )
        elif code_id == TableCode.PLAYERLEFT:
            await self._onPlayerLeft(
                data['username']
            )
        elif code_id == TableCode.STARTROUND:
            await self._onStartRound()        

class ServerGame(Game): pass