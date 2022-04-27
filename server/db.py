import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash
import os


def init_app(app):
	app.teardown_appcontext(close_db)
	app.cli.add_command(init_db_command)


def get_db():
	if 'db' not in g:
		g.db = sqlite3.connect(
			current_app.config['DATABASE'],
			detect_types = sqlite3.PARSE_DECLTYPES
		)
		g.db.row_factory = sqlite3.Row
		
	return g.db
	

def close_db(e = None):
	db = g.pop('db', None)
	
	if db is not None:
		db.close()
		

def init_db():
	db = get_db()
	
	with current_app.open_resource('schema.sql') as f:
		db.executescript(f.read().decode('utf8'))

	db.commit()


def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d
		
		
@click.command('init-db')
@with_appcontext
def init_db_command():
	"""Clear the existing data and create and initialise new tables."""
	init_db()

	db = get_db()
	db.execute(
		"INSERT INTO users (username, password, isAdmin) VALUES (?, ?, ?)",
		("admin", generate_password_hash("admin"), 1)
	)
	db.commit()

	click.echo("Initialised the database.")

