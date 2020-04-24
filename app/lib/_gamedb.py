from hashlib import sha256
from ._enums import DbTable

account_id_from_username = """
SELECT account_id FROM {} WHERE username = {{}}
""".format(DbTable.ACCOUNTS.name)

account_select = """
SELECT money FROM {} WHERE account_id = {{}}
""".format(DbTable.ACCOUNTS.name)

insert_into_players = """
INSERT INTO {} (id, account_id, pokertable_id) 
VALUES (?, ?, ?)
""".format(DbTable.PLAYERS.name)

withdraw_from_account = """
UPDATE {} SET money={{}} WHERE account_id={{}}
""".format(DbTable.ACCOUNTS.name)

delete_from_players = """
DELETE FROM {} WHERE player_id = {{}}
""".format(DbTable.PLAYERS.name)

class GameDb:

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def _encodePlayerId(self, account_id, table_id):
        return sum(
            int.from_bytes(sha256(str(_id)).digest()) 
            for _id in [account_id, table_id]
        )
    
    def withdrawFromAccount(self, account_id, money, withdraw):
        if withdraw > money: withdraw = money
        self.cursor.execute(
            withdraw_from_account.format(money, account_id)
        )
        return withdraw
    
    def accountIdFromUsername(self, username):
        self.cursor.execute(account_id_from_username.format(username))
        return self.cursor.fetchall()[0][0]
    
    def registerPlayer(self, account_id, table_id, money):
        self.cursor.execute(account_select.format(account_id))
        assets, _ = self.cursor.fetchall()[0]
        withdrawn = self.withdrawFromAccount(account_id, money, assets)
        player_id = self._encodePlayerId(account_id, table_id)
        self.cursor.executemany(
            insert_into_players,
            [(player_id, account_id, table_id, withdrawn)]
        )
        self.conn.commit()
        return player_id, withdrawn
    
    def unregisterPlayer(self, account_id, table_id):
        player_id = self._encodePlayerId(account_id, table_id)
        self.cursor.execute(delete_from_players.format(player_id))
    
    