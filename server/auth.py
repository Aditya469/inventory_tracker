import functools

from flask import (
	Blueprint, flash, g, redirect, render_template, request, session, url_for, request
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=('GET', 'POST'))
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		db = get_db()
		error = None
		user = db.execute(
			"SELECT * FROM users WHERE username = ?", (username,)
		).fetchone()
		
		if user is None:
			error = 'Incorrect username'
		elif not check_password_hash(user['password'], password):
			error = 'Incorrect login'
			
		if error is None:
			session.clear()
			session['username'] = user['username']
			return redirect(url_for('frontPage.getFrontPage'))

		flash(error)
		
	return render_template('login.html')


@bp.before_app_request
def load_logged_in_user():
	username = session.get('username')
	
	if username is None:
		g.user = None
	else:
		g.user = get_db().execute(
			'SELECT * FROM users WHERE username = ?', (username,)
		).fetchone()
		
		
@bp.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('auth.login'))


def login_required(view):
	@functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.user is None:
			return redirect(url_for('auth.login'))
		
		return view(**kwargs)
	
	return wrapped_view

