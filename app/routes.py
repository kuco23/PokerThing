import json, random
from time import sleep
from flask import (
    render_template, redirect, request,
    make_response, Response, url_for
)
from app import app

@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    username = request.cookies.get('user')
    return render_template(
        'index.html' if username else 'login.html'
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = request.form['username']
    resp = make_response(render_template('base.html'))
    resp.set_cookie('user', user)
    return resp

def sseFormat(data : dict):
    jsn = json.dumps(data)
    return f'event: listen\ndata: {jsn}\n\n'

@app.route('/stream', methods=['GET'])
def stream():
    def listenstream():
        yield sseFormat({'rand': str(random.random())})
        sleep(0.5)
    return Response(response=listenstream(), content_type='text/event-stream')

@app.route("/streamTarget")
def streamTarget():
    return render_template('stream.html')