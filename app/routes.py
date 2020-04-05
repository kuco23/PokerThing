import json, random
from hashlib import sha256
from time import sleep
from flask import (
    render_template, redirect, request,
    make_response, Response, url_for
)
from app import app

def checkData(form):
    return (
        'username' in form and
        'password' in form and
        'email' in form
    )

def sseFormat(data : dict):
    jsn = json.dumps(data)
    return f'event: listen\ndata: {jsn}\n\n'

@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET', 'POST'])
def index():
    username = request.cookies.get('username')
    return render_template('index.html', username = username)

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/acceptLoginForm', methods = ['POST'])
def acceptLoginForm():
    if checkData(request.form):
        return render_template('index.html')
    else:
        return render_template('login.html')

@app.route('/acceptSignupForm', methods = ['POST'])
def acceptSignupForm():
    if checkData(request.form):
        username = request.form['username']
        resp = make_response(redirect('/index'))
        resp.set_cookie('username', username)
        return resp
    else:
        return render_template('signup.html')

@app.route('/signOut', methods = ['GET'])
def signOut():
    resp = make_response(redirect('/index'))
    resp.delete_cookie('username')
    return resp

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