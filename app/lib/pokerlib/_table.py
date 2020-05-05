from operator import add
from .enums import RoundPublicInId
from ._player import Player, PlayerGroup
from ._round import Round

class Table:
    PlayerSprite = PlayerGroup
    RoundClass = Round

    def __init__(
        self, _id, seats, buyin, small_blind, big_blind
    ):
        self.id = _id
        self.seats = seats
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.buyin = buyin
        self.players = self.PlayerSprite([])
        self.button = 0
        self.round = None
        self.interrupt = False
        self._player_removal_schedule = dict()
        self._player_addition_schedule = dict()

    def __bool__(self):
        return 2 <= len(
            self.players.getNotBrokePlayers()
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
    def all_players(self):
        return add(
            self.players, 
            Table.PlayerSprite(
                self._player_addition_schedule.values()
            )
        )

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
        while (
            len(self.players) < self.seats and
            len(self._player_addition_schedule) > 0
        ):
            id_, player = self._player_addition_schedule.popitem()
            self.players.append(player)

    def newRound(self, round_id):
        if self.round: return False
        self._updatePlayers()
        if not self: return False
        round_players = self.players.getNotBrokePlayers()
        self.button = (self.button + 1) % len(round_players)
        self.round = self.Round(
            round_id,
            round_players,
            self.button,
            self.small_blind,
            self.big_blind
        )
        return True