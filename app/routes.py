import json, sqlite3, time
from hashlib import sha256
from jinja2 import DictLoader
from sanic import response
from sanic.websocket import ConnectionClosed
from jinja2_sanic import template, render_template, setup
from .lib import (
    ServerPlayer, TableCode,
    ServerGameCode, ClientGameCode, ClientDbCode
)
from .lib.database import DbTable, table_enum
from app import app, dbase, game, dbgame, dbbrowser, config

from sanic.log import logger

TABLE_ID = 0

app.static('/css/main.css', 'app/static/css/main.css')
app.static('/css/base.css', 'app/static/css/base.css')
app.static('/css/navbar.css', 'app/static/css/navbar.css')
app.static('/css/forms.css', 'app/static/css/forms.css')
app.static('/css/database.css', 'app/static/css/database.css')
app.static('/css/pokertable.css', 'app/static/css/pokertable.css')
app.static('/favicon.ico', 'app/static/favicon.ico')

setup(
    app,
    loader=DictLoader({
        "template_base": open('app/templates/base.html').read(),
        "template_signin": open('app/templates/signin.html').read(),
        "template_signup": open('app/templates/signup.html').read(),
        "template_database": open('app/templates/database.html').read(),
        "template_table": open('app/templates/table.html').read()
    })
)

def signinValidate(form):
    password = form.get('password').encode('utf-8')
    passhash = sha256(password).hexdigest()
    account = dbase.selectWhere(
        DbTable.ACCOUNTS, 
        username = form.get('username'), 
        password_hash = passhash
    )
    return bool(account)

def signupValidate(form):
    username_in_table = dbase.selectWhere(
        DbTable.ACCOUNTS, 
        username = form.get('username')
    )
    return not username_in_table

def userSignup(form):
    password = form.get('password').encode('utf-8')
    passhash = sha256(password).hexdigest()
    dbase.insert(
        DbTable.ACCOUNTS, 
        username = form.get('username'),
        password_hash = passhash,
        email = form.get('email'),
        money = config.STARTING_MONEY
    )

@app.route("/base", methods=['GET'])
@template("template_base")
async def base(request):
    username = request.cookies.get('username')
    return {"username" : username}

@app.route("/signup", methods=['GET', 'POST'])
async def signup(request):
    if request.method == 'POST':
        if signupValidate(request.form):
            userSignup(request.form)
            resp = response.redirect('/base')
            resp.cookies['username'] = request.form.get('username')
            return resp
        return render_template("template_signin", request, {})
    if request.method == 'GET':
        if request.cookies.get('username'):
            return response.redirect('/base')
        return render_template('template_signup', request, {})

@app.route('/signin', methods=['GET', 'POST'])
async def signin(request):
    if request.method == 'POST':
        if signinValidate(request.form):
            resp = response.redirect('/base')
            resp.cookies['username'] = request.form.get('username')
            return resp
        return render_template('template_signin', request, {})
    elif request.method == 'GET':
        if request.cookies.get('username'):
            return response.redirect('/base')
        return render_template('template_signin', request, {})

@app.route('/signout', methods = ['GET'])
async def signout(request):
    resp = response.redirect('/base')
    del resp.cookies['username']
    return resp


@app.route('/database', methods = ['GET', 'POST'])
async def database(request):
    if request.method == 'POST':
        client_id = request.json.get('id')
        client_data = request.json.get('data')

        if client_id == ClientDbCode.GETTABLE:
            columns, rows = dbbrowser.readTable(
                table_enum[client_data['table']]
            )
        elif client_id == ClientDbCode.GETPLAYER:
            columns, rows = dbbrowser.getPlayer(
                client_data['account_id']
            )
        return response.json({
            'rows' : rows, 'columns': columns
        })

    elif request.method == 'GET':
        user = request.cookies.get('username')
        return render_template(
            'template_database', 
            request, {'username': user}
        )


@app.websocket('/tablefeed')
async def feed(request, ws):
    table = game[TABLE_ID]
    username = request.cookies.get('username')
    await table.executeTableIn(
        TableCode.PLAYERJOINED,
        username = username, sock = ws
    )
    await table.executeTableIn(TableCode.STARTROUND)
    try:
        while True:
            client_data = json.loads(await ws.recv())
            client_code = client_data.get('id')
            logger.info(client_data)
            if client_code == ClientGameCode.MESSAGE:
                await table.notifyTable({
                    'id': ServerGameCode.MESSAGE,
                    'data': {
                        'username': username,
                        'message': client_data['data']
                    }
                })
            else: await table.executeRoundIn(
                client_code, username, 
                **client_data['data']
            )
    except ConnectionClosed:
        logger.info('Connection Closed')
        await table.executeTableIn(
            TableCode.PLAYERLEFT, 
            username = username
        )

@app.route('/table', methods = ['GET'])
async def table(request):
    table = game[TABLE_ID]
    user = request.cookies.get('username')
    if (
        user and len(table.players) < table.seats and
        table.players.getPlayerByAttr('name', user) is None
    ):
        account = dbgame.accountFromUsername(user)
        if (account and account.money >= table.minbuyin):
            return render_template(
                'template_table', request, 
                {'username': user}
            )
    return response.redirect('/base')