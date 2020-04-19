from operator import add
from .enums import PlayerActionId
from ._player import Player, PlayerGroup
from ._round import Round

class Table:
    Round = Round

    def __init__(self, _id, players, small_blind, big_blind):
        self.id = _id
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.players = players
        self.button = 0
        self.round = None
        self.interrupt = False
        self._player_removal_schedule = dict()
        self._player_addition_schedule = dict()

    def __bool__(self):
        return 2 <= len(self.players.getNotBrokePlayers()) <= 9
    
    def __eq__(self, other):
        return self.id == other.id

    def __contains__(self, _id):
        return self.all_players.getPlayerById(_id) is not None

    def __iter__(self):
        return iter(self.all_players)
    
    def __iadd__(self, players):
        self._clearPlayersFromSchedules(players)
        self._addPlayersToAdditionSchedule(players)
        if not self.round: self._updatePlayers()
        return self

    def __isub__(self, players):
        self._clearPlayersFromSchedules(players)
        self._addPlayersToRemovalSchedule(players)
        if not self.round: self._updatePlayers()
        else:
            for player in players:
                if player.id == self.round.current_player.id:
                    self.round.privateIn(PlayerActionId.FOLD)
                elif player.id in self.round:
                    player.is_folded = True
        return self
                    
    @property
    def all_players(self):
        return add(
            self.players, 
            list(self._player_addition_schedule.values())
        )
    
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
        self.players.extend(self._player_addition_schedule.values())
        self.players.remove(self._player_removal_schedule.values())
        self._player_addition_schedule.clear()
        self._player_removal_schedule.clear()

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