from flask import render_template, redirect, request, make_response
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

