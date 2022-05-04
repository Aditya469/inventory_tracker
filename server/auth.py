import functools

from flask import (
	Blueprint, flash, g, redirect, render_template, request, session, url_for, request
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from .db import getDbSession, User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=('GET', 'POST'))
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		dbSession = getDbSession()
		error = None
		user = dbSession.query(User).filter(User.username == username).first()
		
		if user is None:
			error = 'Incorrect username'
		elif not check_password_hash(user.passwordHash, password):
			error = 'Incorrect login'
			
		if error is None:
			session.clear()
			session['username'] = user.username
			return redirect(url_for('overview.getOverview'))

		flash(error)

	return render_template('login.html')


@bp.before_app_request
def load_logged_in_user():
	username = session.get('username')

	if username is None:
		g.user = None
	else:
		dbSession = getDbSession()
		g.user = dbSession.query(User).filter(User.username == username).first()
		print(g.user)



		
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

