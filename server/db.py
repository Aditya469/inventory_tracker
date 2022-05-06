import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash
import os

from sqlalchemy import create_engine, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, Sequence, String, \
	Text, inspect
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

from .dbSchema import Base, User, ProductType, StockItem, Setting, ItemId

def initApp(app):
	# engine = create_engine('postgresql://server:server@localhost:5432/inventorydb')
	engine = create_engine('sqlite:///inventoryDB.sqlite', echo=True)  # temporary for dev use
	Base.metadata.create_all(engine)

	# check if admin user exists and add the default if they don't
	Session = sessionmaker(bind=engine, future=True)
	session = Session()

	# check if the admin user exists. This is used as a proxy for the database being set up
	res = session.query(User).filter(User.username == 'admin').count()
	if res == 0:
		adminUser = User(username='admin', passwordHash=generate_password_hash('admin'), isAdmin=True)
		session.add(adminUser)

		# set up default settings
		session.add(Setting(name="stickerSheetPageHeight_mm", value="297"))
		session.add(Setting(name="stickerSheetPageWidth_mm", value="210"))
		session.add(Setting(name="stickerSheetStickersHeight_mm", value="266"))
		session.add(Setting(name="stickerSheetStickersWidth_mm", value="190"))
		session.add(Setting(name="stickerSheetDpi", value="300"))
		session.add(Setting(name="stickerSheetRows", value="6"))
		session.add(Setting(name="stickerSheetColumns", value="3"))
		session.add(Setting(name="stickerPadding_mm", value="5"))

		session.add(Setting(name="idCardHeight_mm", value="55"))
		session.add(Setting(name="idCardHeight_mm", value="85"))
		session.add(Setting(name="idCardDpi", value="300"))

		session.commit()

		# set up some development data for temporary use
		IDs = []
		for i in range(6):
			IDs.append(ItemId())
			session.add(IDs[i])

		session.commit()

		productType1 = ProductType(productName="productType1")
		session.add(productType1)
		session.commit()

		stockItem1 = StockItem(
			idNumber=IDs[0].idNumber,
			productType=productType1.id,
			quantityRemaining=10
		)
		stockItem2 = StockItem(
			idNumber=IDs[1].idNumber,
			productType=productType1.id,
			quantityRemaining=10
		)
		session.add(stockItem1)
		session.add(stockItem2)

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
