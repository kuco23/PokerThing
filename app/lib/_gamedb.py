from hashlib import sha256
from ._enums import DbTable

account_id_from_username = """
SELECT account_id FROM {} WHERE username = {{}}
""".format(DbTable.ACCOUNTS.value)

account_select = """
SELECT money FROM {} WHERE account_id = {{}}
""".format(DbTable.ACCOUNTS.value)

insert_player = """
INSERT INTO {} (id, account_id, pokertable_id) 
VALUES (?, ?, ?)
""".format(DbTable.PLAYERS.value)

withdraw_from_account = """
UPDATE {} SET money={{}} WHERE account_id={{}}
""".format(DbTable.ACCOUNTS.value)

delete_from_players = """
DELETE FROM {} WHERE account_id = {{}} AND table_id = {{}}
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
INSERT INTO {} (round_id, account_id, turn_id, action, amount) 
VALUES (?, ?, ?, ?, ?)
""".format(DbTable.PLAYERACTIONS.value)

insert_board = """
INSERT INTO {} (round_id, turn_id, cards) VALUES (?, ?, ?)
""".format(DbTable.BOARDS.value)

class GameDb:

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def withdrawFromAccount(self, account_id, money, withdraw):
        if withdraw > money: withdraw = money
        self.cursor.execute(
            withdraw_from_account.format(money, account_id)
        )
        return withdraw
    
    def accountIdFromUsername(self, username):
        self.cursor.execute(
            account_id_from_username.format(username)
        )
        return self.cursor.fetchall()[0][0]
    
    def registerPlayer(self, account_id, table_id, money):
        self.cursor.execute(account_select.format(account_id))
        assets, *_ = self.cursor.fetchall()[0]
        withdrawn = self.withdrawFromAccount(account_id, money, assets)
        player_id = self._encodePlayerId(account_id, table_id)
        self.cursor.executemany(
            insert_player,
            [(player_id, account_id, table_id, withdrawn)]
        )
        self.conn.commit()
        return player_id, withdrawn
    
    def unregisterPlayer(self, account_id, table_id):
        self.cursor.execute(delete_from_players.format(
            account_id, table_id
        ))
        self.conn.commit()
    
    def registerNewRound(self, table_id):
        round_id, *_ = self.cursor.execute(
            get_last_round_id.format()
        ).cursor.fetchall()[0]
        self.cursor.executemany(
            insert_round,
            [(round_id + 1, table_id)]
        )
        self.conn.commit()
        return round_id + 1

    def insertPlayerCards(self, account_id, round_id, cards):
        self.cursor.executemany(
            insert_player_cards,
            [(round_id, account_id, cards)]
        )
        self.conn.commit()
    
    def insertPlayerAction(
        self, round_id, account_id, 
        turn_id, action_id, amount=0
    ):
        self.cursor.executemany(
            insert_player_action,
            [(round_id, account_id, turn_id, action_id, amount)]
        )
        self.conn.commit()
    
    def insertBoard(self, round_id, turn_id, cards):
        self.cursor.executemany(
            insert_board,
            [(round_id, turn_id, cards)]
        )
        self.conn.commit()
