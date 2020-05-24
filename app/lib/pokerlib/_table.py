from operator import add
from .enums import RoundPublicInId
from ._player import Player, PlayerGroup
from ._round import Round

class Table:
    PlayerSprite = PlayerGroup
    RoundClass = Round

    def __init__(
        self, _id, seats, buyin, minbuyin, 
        small_blind, big_blind
    ):
        self.id = _id
        self.seats = seats
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.buyin = buyin
        self.minbuyin = minbuyin
        self.button = 0
        self.round = None
        self.interrupt = False
        self.players = self.PlayerSprite([])
        # players that have left
        self._player_removal_schedule = dict()
        # player that are waiting to be added
        self._player_addition_schedule = dict()

    def __bool__(self):
        return 2 <= len(
            self.players.getPlayersWithMoreMoney(self.minbuyin)
        ) <= self.seats
    
    def __eq__(self, other):
        return self.id == other.id

    def __contains__(self, _id):
        return self.all_players.getPlayerById(_id) is not None

    def __iter__(self):
        return iter(self.all_players)
    
    def __iadd__(self, players):
        self._addPlayers(players)
        return self

    def __isub__(self, players):
        self._removePlayers(players)
        return self

    @property
    def seats_free(self):
        return (
            self.seats - len(self.players) - 
            len(self._player_addition_schedule)
        )
                    
    @property
    def all_players(self):
        return self.PlayerSprite(add(
            self.players, 
            list(self._player_addition_schedule.values())
        ))

    def _popRoundQueue(self):
        private_out_queue = self.round.private_out_queue.copy()
        self.round.private_out_queue.clear()
        public_out_queue = self.round.public_out_queue.copy()
        self.round.public_out_queue.clear()
        return private_out_queue, public_out_queue
    
    def _addPlayers(self, players):
        self._clearPlayersFromSchedules(players)
        self._addPlayersToAdditionSchedule(players)
        if not self.round: self._updatePlayers()
    
    def _removePlayers(self, players):
        self._clearPlayersFromSchedules(players)
        self._addPlayersToRemovalSchedule(players)
        if not self.round: self._updatePlayers()
        else:
            for player in players:
                if player.id == self.round.current_player.id:
                    self.round.publicIn(
                        player.id, RoundPublicInId.FOLD
                    )
                elif player.id in self.round:
                    player.is_folded = True
    
    def _addPlayersToAdditionSchedule(self, players):
        for player in players:
            self._player_addition_schedule[player.id] = player
    
    def _addPlayersToRemovalSchedule(self, players):
        for player in players:
            self._player_removal_schedule[player.id] = player

    def _clearPlayersFromSchedules(self, players):
        for player in players:
            if player.id in self._player_removal_schedule:
                self._player_removal_schedule.pop(player.id)
            if player.id in self._player_addition_schedule:
                self._player_addition_schedule.pop(player.id)
        
    # called only when round is finished
    def _updatePlayers(self):
        self.players.remove(self._player_removal_schedule.values())
        self._player_removal_schedule.clear()
        for player in self.players:
            if player.money < self.minbuyin:
                self._player_addition_schedule[player.id] = player
        self.players = self.PlayerSprite(filter(
            lambda player: player.money >= self.minbuyin,
            self.players
        ))
        for _id, player in self._player_addition_schedule.items():
            if len(self.players) >= self.seats: break
            if player.money >= self.minbuyin:
                self.players.append(player)
        for player in self.players:
            if player.id in self._player_addition_schedule:
                self._player_addition_schedule.pop(player.id)

    def newRound(self, round_id):
        if self.round: return False
        self._updatePlayers()
        if not self: return False
        self.button = (self.button + 1) % len(self.players)
        self.round = self.Round(
            round_id,
            self.players,
            self.button,
            self.small_blind,
            self.big_blind
        )
        return True