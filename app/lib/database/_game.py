from ._enums import DbTable
from ._tables import table_columns

account_from_username = """
SELECT * FROM {} WHERE username = '{{}}'
""".format(DbTable.ACCOUNTS.value)

account_select = """
SELECT money FROM {} WHERE id = {{}}
""".format(DbTable.ACCOUNTS.value)

insert_player = """
INSERT INTO {} (id, account_id, pokertable_id) 
VALUES (?, ?, ?)
""".format(DbTable.PLAYERS.value)

account_money_alter = """
UPDATE {} SET money={{}} WHERE id={{}}
""".format(DbTable.ACCOUNTS.value)

delete_from_players = """
DELETE FROM {} 
WHERE account_id = {{}} AND pokertable_id = {{}}
""".format(DbTable.PLAYERS.value)

get_last_round_id = """
SELECT max(id) FROM {}
""".format(DbTable.ROUNDS.value)

insert_round = """
INSERT INTO {} (id, pokertable_id) VALUES (?, ?)
""".format(DbTable.ROUNDS.value)

insert_player_cards = """
INSERT INTO {} (round_id, account_id, cards) 
VALUES (?, ?, ?)
""".format(DbTable.PLAYERCARDS.value)

insert_player_action = """
INSERT INTO {} (round_id, player_id, turn_id, action_id, amount) 
VALUES (?, ?, ?, ?, ?)
""".format(DbTable.PLAYERACTIONS.value)

insert_board = """
INSERT INTO {} (round_id, turn_id, cards) VALUES (?, ?, ?)
""".format(DbTable.BOARDS.value)

class DbGame:

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
        self._player_id = self.getLastPlayerId()
    
    @property
    def player_id(self):
        self._player_id += 1
        return self._player_id
    
    def getLastPlayerId(self):
        self.cursor.execute(
            f"SELECT MAX(id) FROM {DbTable.PLAYERS.value}"
        )
        last_id = self.cursor.fetchall()[0][0]
        return last_id or 0
    
    def accountFromUsername(self, username):
        self.cursor.execute(
            account_from_username.format(username)
        )
        row = self.cursor.fetchall()[0]
        return (
            table_columns[DbTable.ACCOUNTS](*row)
            if row[0] is not None else None
        )

    def withdrawFromAccount(self, account_id, money):
        self.cursor.execute(
            account_money_alter.format(
                f'money - {money}', account_id
            )
        )
        self.conn.commit()
    
    def transferToAccount(self, account_id, money):
        self.cursor.execute(
            account_money_alter.format(
                f'money + {money}', account_id
            )
        )
        self.conn.commit()

    def registerPlayer(
        self, account_id, player_id, table_id
    ):
        self.cursor.executemany(
            insert_player,
            [(player_id, account_id, table_id)]
        )
        self.conn.commit()
    
    def unregisterPlayer(self, account_id, table_id):
        self.cursor.execute(delete_from_players.format(
            account_id, table_id
        ))
        self.conn.commit()
    
    def registerNewRound(self, table_id):
        round_id, *_ = self.cursor.execute(
            get_last_round_id.format()
        ).fetchall()[0]
        if round_id is None: round_id = -1
        self.cursor.executemany(
            insert_round,
            [(round_id + 1, table_id)]
        )
        self.conn.commit()
        return round_id + 1

    def insertPlayerCards(self, account_id, round_id, cards):
        self.cursor.executemany(
            insert_player_cards,
            [(round_id, account_id, str(cards))]
        )
        self.conn.commit()
    
    def insertPlayerAction(
        self, round_id, player_id, 
        turn_id, action_id, amount=0
    ):
        self.cursor.executemany(
            insert_player_action,
            [(round_id, player_id, turn_id, action_id, amount)]
        )
        self.conn.commit()
    
    def insertBoard(self, round_id, turn_id, cards):
        self.cursor.executemany(
            insert_board,
            [(round_id, turn_id, cards)]
        )
        self.conn.commit()