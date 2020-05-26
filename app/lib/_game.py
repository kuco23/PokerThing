from json import dumps
from .pokerlib import Game, Player, Round, Table, PlayerGroup
from .database import DbTable, DbPlayerTurn, DbPlayerAction
from ._enums import (
    ServerGameCode, ClientGameCode, TableCode, 
    RoundPublicInId, RoundPublicOutId, 
    RoundPrivateOutId
)

from sanic.log import logger

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

    async def close(self):
        await self.sock.close()

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
        self, db, _id, name, seats, 
        buyin, minbuyin, small_blind, big_blind
    ):
        super().__init__(
            _id, seats, buyin, minbuyin,
            small_blind, big_blind
        )
        self.name = name
        self.minbuyin = minbuyin
        self.gamebase = db
        self.round_id = self.gamebase.registerNewRound(_id)

    async def notifyTable(self, data):
        for player in self.all_players: 
            await player.send(data)
    
    async def notifyPlayer(self, player_id, data):
        player = self.all_players.getPlayerById(player_id)
        if player is not None: await player.send(data)
    
    async def notifyOthers(self, player_id, data):
        for player in self.all_players:
            if player.id != player_id: 
                await player.send(data)
    
    async def _processRoundQueue(self):
        private, public = self._popRoundQueue()
        for out in private: 
            out.data['player_id'] = out.player_id
            await self._executeRoundOut(out.id, **out.data)
        for out in public: 
            await self._executeRoundOut(out.id, **out.data)
    
    async def _onPlayerJoined(self, player_name, sock):
        player_id = self.gamebase.player_id
        account = self.gamebase.accountFromUsername(player_name)
        buyin = min(account.money, self.buyin)
        self.gamebase.withdrawFromAccount(account.id, buyin)
        self.gamebase.registerPlayer(
            account.id, player_id, self.id
        )
        player = ServerPlayer(
            account.id, self.id, player_id,
            player_name, buyin, sock
        )
        self._addPlayers([player])
        await self.notifyPlayer(player_id, {
            "id": ServerGameCode.PLAYERSETUP,
            "data": {
                "player_name": player_name,
                "player_money": buyin,
                "players_data": [{
                    "name": player.name,
                    "money": player.money
                } for player in self.players]
            }
        })
        
    async def _onPlayerLeft(self, player_name):
        player = self.players.getPlayerByAttr(
            'name', player_name
        )
        if player is not None: 
            self._removePlayers([player])   
            self.gamebase.transferToAccount(
                player.account_id, player.money
            ) 
            self.gamebase.unregisterPlayer(
                player.account_id, self.id
            )
            await self.notifyTable({
                "id": ServerGameCode.PLAYERLEFT,
                "data": {
                    "player_name": player_name
                }
            })
    
    async def _onStartRound(self):
        self._updatePlayers()
        if self and not self.round:
            await self.notifyTable({
                "id": ServerGameCode.PLAYERSBOUGHTIN,
                "data": {
                    "players_data": [{
                        "name": player.name, 
                        "money": player.money
                    } for player in self.players
                ]}
            })
            self.newRound(self.round_id)
            self.round_id = self.gamebase.registerNewRound(
                self.id
            )
            await self._processRoundQueue()

    async def _onNewRound(self):
        await self.notifyTable({
            "id": ServerGameCode.NEWROUND
        })
    
    async def _onNewTurn(self, turn, board, round_id):
        self.gamebase.insertBoard(
            round_id, turn.value, dumps(board)
        )
        await self.notifyTable({
            "id": ServerGameCode.NEWTURN,
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
        await self.notifyPlayer(player_id, {
            "id": ServerGameCode.DEALTCARDS,
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
        await self.notifyTable({
            "id": ServerGameCode.SMALLBLIND,
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
        await self.notifyTable({
            "id": ServerGameCode.BIGBLIND,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "big_blind": self.big_blind,
                "stake": stake
            }
        })
    
    async def _onPlayerActionRequired(
        self, player_id, player_name, to_call
    ):
        await self.notifyTable({
            "id": ServerGameCode.PLAYERACTIONREQUIRED,
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
        await self.notifyTable({
            "id": ServerGameCode.PLAYERFOLD,
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
        await self.notifyTable({
            "id": ServerGameCode.PLAYERCHECK,
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
        await self.notifyTable({
            "id": ServerGameCode.PLAYERCALL,
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
        await self.notifyTable({
            "id": ServerGameCode.PLAYERRAISE,
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
        await self.notifyTable({
            "id": ServerGameCode.PLAYERALLIN,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "allin_stake": allin_stake
            }
        })
    
    async def _onPublicCardShow(
        self, player_id, player_name, cards
    ):
        await self.notifyTable({
            "id": ServerGameCode.PUBLICCARDSHOW,
            "data": {
                "player_name": player_name,
                "player_cards": cards
            }
        })
    
    async def _onDeclarePrematureWinner(
        self, player_id, player_name, player_money, won
    ):
        await self.notifyTable({
            "id": ServerGameCode.DECLAREPREMATUREWINNER,
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
        await self.notifyTable({
            "id": ServerGameCode.DECLAREFINISHEDWINNER,
            "data": {
                "player_name": player_name,
                "player_money": player_money,
                "won": won,
                "hand": hand,
                "kickers": kickers
            }
        })
    
    async def _onRoundFinished(self): 
        self._updatePlayers()
        await self.notifyTable({
            "id": ServerGameCode.ROUNDFINISHED
        })
        await self.notifyTable({
            "id": ServerGameCode.PLAYERSUPDATE,
            "data": {
                "players_data": [{
                    "name": player.name,
                    "money": player.money
                } for player in self.players]
            }
        })
        await self._processRoundQueue()
        # preconfigured to start if possible
        await self._onStartRound()

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
        elif code_id == RoundPublicOutId.PLAYERACTIONREQUIRED:
            await self._onPlayerActionRequired(
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
        if not self.round: return
        player = self.players.getPlayerByAttr(
            'name', player_name
        )
        if code_id == ClientGameCode.FOLD:
            self.round.publicIn(
                player.id, RoundPublicInId.FOLD
            )
        elif code_id == ClientGameCode.CHECK:
            self.round.publicIn(
                player.id, RoundPublicInId.CHECK
            )
        elif code_id == ClientGameCode.CALL:
            self.round.publicIn(
                player.id, RoundPublicInId.CALL
            )
        elif code_id == ClientGameCode.RAISE:
            self.round.publicIn(
                player.id, RoundPublicInId.RAISE, 
                data['raised_by']
            )
        elif code_id == ClientGameCode.ALLIN:
            self.round.publicIn(
                player.id, RoundPublicInId.ALLIN
            )
        else: return
        await self._processRoundQueue()   

    async def executeTableIn(self, code_id, **data):
        if code_id == TableCode.PLAYERJOINED:
            await self._onPlayerJoined(
                data['username'], data['sock']
            )
        elif code_id == TableCode.PLAYERLEFT:
            await self._onPlayerLeft(
                data['username']
            )
        elif code_id == TableCode.STARTROUND:
            await self._onStartRound()        

class ServerGame(Game): pass