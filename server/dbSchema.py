from sqlalchemy import create_engine, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, Sequence, String, \
	Text, inspect
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class ItemId(Base):
	__tablename__ = "itemIds"

	idNumber = Column(Integer, primary_key=True, unique=True)
	isPendingAssignment = Column(Boolean, default=True)
	isAssigned = Column(Boolean, default=False)
	associatedStock = relationship("StockItem", backref='itemIds', uselist=False)


class StockItem(Base):
	__tablename__ = "stockItem"

	id = Column(Integer, primary_key=True)  # ID in the database rather than QR code ID
	idNumber = Column(Integer, ForeignKey("itemIds.idNumber"))
	productType = Column(Integer, ForeignKey("productTypes.id"))
	addedTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	expiryDate = Column(Date)
	quantityRemaining = Column(Numeric)
	canExpire = Column(Boolean, default=False)
	assignedToJob = Column(Boolean, default=False)


class ProductType(Base):
	__tablename__ = "productTypes"

	id = Column(Integer, primary_key=True)
	productName = Column(Text)
	productIdentifier1 = Column(Text)  # identifiers are to allow related stock to be collated,
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


class Bin(Base):
	__tablename__ = "bins"

	id = Column(Integer, primary_key=True)
	idString = Column(String)
	locationName = Column(String)


class User(Base):
	__tablename__ = "users"

	username = Column(Text, primary_key=True, unique=True)
	passwordHash = Column(Text)
	isAdmin = Column(Boolean, default=False)


class Setting(Base):
	__tablename__ = "settings"

	name = Column(String, primary_key=True)
	value = Column(String, primary_key=True)
