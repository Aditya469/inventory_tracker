from sqlalchemy import create_engine, Boolean, Column, Date, DateTime, ForeignKey, Integer, Sequence, String, \
	Text, inspect
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# this section borrowed from https://stackoverflow.com/questions/10355767/how-should-i-handle-decimal-in-sqlalchemy-sqlite
from decimal import Decimal as D
import sqlalchemy.types as types


class Numeric(types.TypeDecorator):
	impl = types.String

	def load_dialect_impl(self, dialect):
		return dialect.type_descriptor(types.VARCHAR(100))

	def process_bind_param(self, value, dialect):
		return str(value)

	def process_result_value(self, value, dialect):
		if value != "None":
			return D(value)
		return None


class ItemId(Base):
	__tablename__ = "itemIds"

	idNumber = Column(Integer, primary_key=True, unique=True)
	isPendingAssignment = Column(Boolean, default=False)
	isAssigned = Column(Boolean, default=False)
	associatedStock = relationship("StockItem", backref='itemIds', uselist=False)


class StockItem(Base):
	__tablename__ = "stockItem"

	id = Column(Integer, primary_key=True)  # ID in the database rather than QR code ID
	idNumber = Column(Integer, ForeignKey("itemIds.idNumber"))
	productType = Column(Integer, ForeignKey("productTypes.id"))
	addedTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	expiryDate = Column(Date, server_default=None)
	quantityRemaining = Column(Numeric, default=0)
	canExpire = Column(Boolean, default=False)
	price = Column(Numeric)


class ProductType(Base):
	__tablename__ = "productTypes"

	id = Column(Integer, primary_key=True)
	productName = Column(Text)
	tracksSpecificItems = Column(Boolean, default=False)
	tracksAllItemsOfProductType = Column(Boolean, default=False)
	# descriptors are to allow related stock to be collated,
	# e.g. different size paint tins
	productDescriptor1 = Column(Text)
	productDescriptor2 = Column(Text)
	productDescriptor3 = Column(Text)
	addedTimestamp = Column(DateTime, server_default=func.now())
	initialQuantity = Column(Numeric)
	expectedPrice = Column(Numeric)
	barcode = Column(String)
	canExpire = Column(Boolean, default=False)
	associatedStock = relationship("StockItem", backref='productTypes', uselist=False)


class CheckInOutRecord(Base):
	__tablename__ = "checkInOutLog"

	id = Column(Integer, primary_key=True)
	stockItem = Column(Integer, ForeignKey("stockItem.id"))
	qtyBeforeCheckout = Column(Numeric, default=0)
	checkoutTimestamp = Column(DateTime(timezone=True))
	quantityCheckedOut = Column(Numeric, default=0)
	checkinTimestamp = Column(DateTime(timezone=True))
	quantityCheckedIn = Column(Numeric, default=0)


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
