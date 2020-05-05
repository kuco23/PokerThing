from string import ascii_letters
from random import sample, choice
from hashlib import sha256
import sqlite3

'''
random_hash = sha256(b'sdnajfn').hexdigest()
random_string = lambda n: ''.join(sample(ascii_letters, n))

tables_ids = [0,1,2,3,4,5]
n = 100

fake_users = []
for i in range(n):
    name = random_string(6)
    pasw = random_string(8)
    fake_users.append([
        name, sha256(pasw.encode('utf-8')).hexdigest(),
        name + '@gmail.com', 1000
    ])

tables = [[100] for _ in tables_ids]
players = [[i, choice(tables_ids)] for i in range(n)]
'''

insert_player = """
INSERT INTO {} (id, account_id, pokertable_id) 
VALUES (?, ?, ?)
""".format("PLAYERS")
with sqlite3.connect('game1.db') as con:
    cursor = con.cursor()
    cursor.execute("SELECT * FROM ACCOUNTS WHERE username='kuco23'")
    assets, *_ = cursor.fetchall()[0]
    withdrawn = 100
    cursor.execute("SELECT MAX(id) FROM players WHERE id=10000")
    print(cursor.fetchall())

    
