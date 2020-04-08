import json, sqlite3
from pathlib import Path
from hashlib import sha256
from time import sleep
from flask import (
    render_template, redirect, request,
    make_response, Response, url_for, jsonify
)
from .lib import DbTable
from app import app, con
from app import config, sqlsup

users = set()
recv = dict()

def checkLogin(form):
    password = form.get('password').encode('utf-8')
    passhash = sha256(password).hexdigest()
    account = sqlsup.selectWhere(
        con, DbTable.ACCOUNTS, 
        username = form.get('username'), 
        password_hash = passhash
    )
    return bool(account)

def checkSignup(form):
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

@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET', 'POST'])
def index():
    username = request.cookies.get('username')
    return render_template('index.html', username = username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if checkLogin(request.form):
            resp = make_response(redirect('/index'))
            resp.set_cookie('username', request.form.get('username'))
            return resp
        return render_template('login.html', errors = ['Incorrect username or password'])
    elif request.method == 'GET':
        if request.cookies.get('username'):
            return redirect('/index')
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if checkSignup(request.form):
            userSignup(request.form)
            resp = make_response(redirect('/index'))
            resp.set_cookie('username', request.form.get('username'))
            return resp
        return render_template('signup.html', errors = ['Username taken'])
    if request.method == 'GET':
        if request.cookies.get('username'):
            return redirect('/index')
        return render_template('signup.html')

@app.route('/signout', methods = ['GET'])
def signout():
    resp = make_response(redirect('/index'))
    resp.delete_cookie('username')
    return resp

@app.route('/database', methods = ['GET', 'POST'])
def database():
    if request.method == 'POST':
        table = request.json.get('table')
        columns = ['username', 'money', 'email', 'password_hash']
        rows = sqlsup.selectColumns(con, table, columns)
        return jsonify({'table' : rows, 'headers': columns})
    elif request.method == 'GET':
        user = request.cookies.get('username')
        return render_template('database.html', username=user)


def sseFormat(data : dict):
    jsn = json.dumps(data)
    return f'event: listen\ndata: {jsn}\n\n'

@app.route('/table', methods = ['GET'])
def table():
    user = request.cookies.get('username')
    if user: return render_template('table.html', username=user)
    else: return redirect('/index')

@app.route('/message', methods=['POST'])
def message():
    user = request.cookies.get('username')
    message = request.json.get('message')
    for user in users: recv[user] = message
    return jsonify({})

@app.route('/stream', methods=['GET'])
def stream():
    user = request.cookies.get('username')
    users.add(user)
    def listenstream():
        while True:
            if recv.get(user):
                message = recv[user]
                recv[user] = None
                yield sseFormat({'author': user, 'message': message})
            break
    return Response(response=listenstream(), content_type='text/event-stream')

@app.route("/streamTarget")
def streamTarget():
    return render_template('stream.html')
