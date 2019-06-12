from flask import render_template, flash, redirect
from app import app
from app.forms import LoginForm

@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def login():
    user = {'name' : 'john'}
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}'.format(form.username.data))
        return redirect('/index')
    return render_template('index.html', form=form)
