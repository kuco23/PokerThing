import json, sqlite3
from pathlib import Path
from hashlib import sha256
from time import sleep
from flask import (
    render_template, redirect, request,
    make_response, Response, url_for
)
from app import app, con
from app import config, sqlsup

def checkLogin(form):
    password = form.get('password').encode('utf-8')
    passhash = sha256(password).hexdigest()
    account = sqlsup.selectWhere(
        con, 'accounts', 
        username = form.get('username'), 
        password_hash = passhash
    )
    return bool(account)

def checkSignup(form):
    username_in_table = sqlsup.selectWhere(
        con, 'accounts', 
        username = form.get('username')
    )
    return not username_in_table

def userSignup(form):
    password = form.get('password').encode('utf-8')
    passhash = sha256(password).hexdigest()
    sqlsup.insert(
        con, 'accounts', 
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

@app.route('/login', methods=['GET'])
def login():
    if request.cookies.get('username'):
        return redirect('/index')
    return render_template('login.html')

@app.route('/signup', methods=['GET'])
def signup():
    if request.cookies.get('username'):
        return redirect('/index')
    return render_template('signup.html')

@app.route('/acceptLoginForm', methods = ['POST'])
def acceptLoginForm():
    if checkLogin(request.form):
        resp = make_response(redirect('/index'))
        resp.set_cookie('username', request.form.get('username'))
        return resp
    return render_template('login.html')

@app.route('/acceptSignupForm', methods = ['POST'])
def acceptSignupForm():
    if checkSignup(request.form):
        userSignup(request.form)
        resp = make_response(redirect('/index'))
        resp.set_cookie('username', request.form.get('username'))
        return resp
    return render_template('signup.html')

@app.route('/signout', methods = ['GET'])
def signout():
    resp = make_response(redirect('/index'))
    resp.delete_cookie('username')
    return resp


def sseFormat(data : dict):
    jsn = json.dumps(data)
    return f'event: listen\ndata: {jsn}\n\n'

@app.route('/stream', methods=['GET'])
def stream():
    user = request.cookies.get('user')
    def listenstream():
        yield sseFormat({'rand': user})
        sleep(0.5)
    return Response(response=listenstream(), content_type='text/event-stream')

@app.route("/streamTarget")
def streamTarget():
    return render_template('stream.html')
