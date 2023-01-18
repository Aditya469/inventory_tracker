"""
Copyright 2022 DigitME2

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
import sqlite3

from filelock import FileLock, Timeout
from flask import g, after_this_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash

from dbSchema import Base, User, ProductType, Settings, Bin
from paths import dbPath, dbLockFilePath

dbLock = FileLock(dbLockFilePath, timeout=1)
# outsideContextConnectionCount = 0
# outsideContextSession = None

def initApp(app):
	engine = create_engine(f'sqlite:///{dbPath}', echo=True)
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine, future=True)
	session = Session()

	# check if the admin user exists. This is used as a proxy for the database being set up
	res = session.query(User).filter(User.username == 'admin').count()
	if res == 0:
		adminUser = User(username='admin', passwordHash=generate_password_hash('admin'), accessLevel=2)
		session.add(adminUser)
		session.add(Settings())  # add a row to settings with the defaults from the DB schema

		# set up placeholder product
		session.add(ProductType(
			id=-1,
			productName="undefined product type",
			tracksSpecificItems=False,
			tracksAllItemsOfProductType=False,
			initialQuantity=0
		))

		# set up an undefined bin location
		session.add(Bin(
			id=-1,
			locationName = "undefined location"
		))

		session.commit()

# app.teardown_appcontext(close_db)


def getDbSession():
	if 'dbSession' not in g:
		try:
			dbLock.acquire(timeout=5)
			engine = create_engine(f'sqlite:///{dbPath}', echo=False)
			Session = sessionmaker(bind=engine)
			g.dbSession = Session()
		except Timeout:
			abort("Database is locked. Acquire lock timed out", 500)

	return g.dbSession


# TODO: test that this works
def close_db(e=None):
	try:
		db = g.pop('dbSession', None)
		if db is not None:
			logging.debug("closing database")
			db.close()
	except sqlite3.ProgrammingError as e:
		print(e)
	finally:
		dbLock.release(True)
		logging.debug("dbLock released")

