import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash
import os

from sqlalchemy import create_engine, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, Sequence, String, \
	Text, inspect
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

from dbSchema import Base, User, ProductType, StockItem, Settings, ItemId, Bin


def initApp(app):
	# engine = create_engine('postgresql://server:server@localhost:5432/inventorydb')
	engine = create_engine('sqlite:///inventoryDB.sqlite', echo=True)  # temporary for dev use
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine, future=True)
	session = Session()

	# check if the admin user exists. This is used as a proxy for the database being set up
	res = session.query(User).filter(User.username == 'admin').count()
	if res == 0:
		adminUser = User(username='admin', passwordHash=generate_password_hash('admin'), isAdmin=True)
		session.add(adminUser)
		session.add(Settings())  # add a row to settings with the defaults from the DB schema

		# set up placeholder product
		session.add(ProductType(
			productName="undefined product type"
		))

		# set up some development data for temporary use
		IDs = []
		for i in range(6):
			IDs.append(ItemId())
			if i == 0 or i == 1:
				IDs[i].isAssigned = True
			session.add(IDs[i])

		session.flush()

		productType1 = ProductType(
			productName="productType1",
			tracksSpecificItems=True,
			initialQuantity=10,
			expectedPrice=100,
			barcode="prod1Specific",
			canExpire=True
		)
		session.add(productType1)
		productType2 = ProductType(
			productName="productType2",
			tracksAllItemsOfProductType=True,
			initialQuantity=10,
			expectedPrice=10,
			barcode="prod2Bulk",
			canExpire=False
		)
		session.add(productType2)

		Bin1 = Bin(idString = "bin1")
		Bin2 = Bin(idString = "bin2")
		session.add(Bin1)
		session.add(Bin2)

		session.commit()

		session.commit()

# app.teardown_appcontext(close_db)


def getDbSession():
	if 'dbSession' not in g:
		# engine = create_engine('postgresql://server:server@localhost:5432/inventorydb')
		engine = create_engine('sqlite:///inventoryDB.sqlite', echo=True)  # temporary for dev use
		Session = sessionmaker(bind=engine)
		g.dbSession = Session()

	return g.dbSession


# TODO: test that this works
def close_db(e=None):
	db = g.pop('dbSession', None)

	if db is not None:
		db.close()
