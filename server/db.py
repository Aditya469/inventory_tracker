import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash
import os

from sqlalchemy import create_engine, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, Sequence, String, Text, inspect
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class ItemId(Base):
	__tablename__ = "itemIds"

	idNumber = Column(Integer, primary_key=True, unique=True)
	isAssigned = Column(Boolean, default=False)
	associatedStock = relationship("StockItem", backref='itemIds', uselist=False)


class StockItem(Base):
	__tablename__ = "stockItem"

	id = Column(Integer, primary_key=True) # ID in the database rather than QR code ID
	idNumber = Column(Integer, ForeignKey("itemIds.idNumber"))
	productType = Column(Integer, ForeignKey("productTypes.id"))
	addedTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	expiryDate = Column(Date)
	quantityRemaining = Column(Numeric)
	canExpire = Column(Boolean, default=False)


class ProductType(Base):
	__tablename__ = "productTypes"

	id = Column(Integer, primary_key=True)
	productName = Column(Text)
	productIdentifier1 = Column(Text) 	# identifiers are to allow related stock to be collated,
										# e.g. different size paint tins
	productIdentifier2 = Column(Text)
	productIdentifier3 = Column(Text)
	addedTimestamp = Column(DateTime)
	initialQuantity = Column(Numeric)
	expectedPrice = Column(Numeric)
	barcode = Column(String)
	associatedStock = relationship("StockItem", backref='productTypes', uselist=False)


class checkInOutRecord(Base):
	__tablename__ = "checkInOutLog"

	id = Column(Integer, primary_key=True)
	stockItem = Column(Integer, ForeignKey("stockItem.id"))
	checkoutTimestamp = Column(DateTime(timezone=True))
	quantityCheckedOut = Column(Numeric)
	checkinTimestamp = Column(DateTime(timezone=True))
	quantityCheckedIn = Column(Numeric)


class User(Base):
	__tablename__ = "users"

	username = Column(Text, primary_key=True, unique=True)
	passwordHash = Column(Text)
	isAdmin = Column(Boolean, default=False)


def initApp(app):
	#engine = create_engine('postgresql://server:server@localhost:5432/inventorydb')
	engine = create_engine('sqlite:///inventoryDB.sqlite', echo=True)  # temporary for dev use
	Base.metadata.create_all(engine)

	# check if admin user exists and add the default if they don't
	Session = sessionmaker(bind=engine, future=True)
	session = Session()

	res = session.query(User).filter(User.username == 'admin').count()
	if res == 0:
		adminUser = User(username='admin', passwordHash=generate_password_hash('admin'), isAdmin=True)
		session.add(adminUser)
		session.commit()

	#app.teardown_appcontext(close_db)


def getDbSession():
	if 'dbSession' not in g:
		#engine = create_engine('postgresql://server:server@localhost:5432/inventorydb')
		engine = create_engine('sqlite:///inventoryDB.sqlite', echo=True)  # temporary for dev use
		Session = sessionmaker(bind=engine)
		g.dbSession = Session()

	return g.dbSession
	

# TODO: test that this works
def close_db(e = None):
	db = g.pop('dbSession', None)
	
	if db is not None:
		db.close()
