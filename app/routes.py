import json, sqlite3, time
from hashlib import sha256
from jinja2 import DictLoader
from sanic import response
from sanic.websocket import ConnectionClosed
from jinja2_sanic import template, render_template, setup
from .lib import DbTable, sqlsup
from app import app, con, config

app.static('/css/main.css', 'app/static/css/main.css')
app.static('/css/base.css', 'app/static/css/base.css')
app.static('/css/sections.css', 'app/static/css/sections.css')
app.static('/css/forms.css', 'app/static/css/forms.css')
app.static('/css/database.css', 'app/static/css/database.css')
app.static('/css/tools.css', 'app/static/css/tools.css')
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
    account = sqlsup.selectWhere(
        con, DbTable.ACCOUNTS, 
        username = form.get('username'), 
        password_hash = passhash
    )
    return bool(account)

def signupValidate(form):
    username_in_table = sqlsup.selectWhere(
        con, DbTable.ACCOUNTS, 
        username = form.get('username')
    )
    return not username_in_table

def userSignup(form):
    password = form.get('password').encode('utf-8')
    passhash = sha256(password).hexdigest()
    sqlsup.insert(
        con, DbTable.ACCOUNTS, 
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
        table_str = request.json.get('table').upper()
        table_enum = list(filter(
            lambda en: en.name == table_str, DbTable
        ))[0]
        columns, rows = sqlsup.getTable(con, table_enum)
        return response.json({'rows' : rows, 'columns': columns})
    elif request.method == 'GET':
        user = request.cookies.get('username')
        return render_template(
            'template_database', request, {'username': user}
        )

context = {}

@app.websocket('/feed')
async def feed(request, ws):
    user = request.cookies.get('username')
    context[user] = ws
    try:
        while True:
            message = await ws.recv()
            for sock in context.values():
                await sock.send(message)
    except ConnectionClosed:
        context.pop(user)

@app.route('/table', methods = ['GET'])
async def table(request):
    user = request.cookies.get('username')
    if user: return render_template(
        'template_table', request, {'username': user}
    )
    else: return response.redirect('/base')