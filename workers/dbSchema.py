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

	def toDict(self):
		return {
			"idNumber": self.idNumber,
			"isPendingAssignment": self.isPendingAssignment,
			"isAssigned": self.isAssigned
		}


class StockItem(Base):
	__tablename__ = "stockItems"

	id = Column(Integer, primary_key=True)  # ID in the database rather than QR code ID
	idNumber = Column(Integer, ForeignKey("itemIds.idNumber"))
	productType = Column(Integer, ForeignKey("productTypes.id"))
	addedTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	expiryDate = Column(Date, server_default=None)
	quantityRemaining = Column(Numeric, default=0)
	canExpire = Column(Boolean, default=False)
	price = Column(Numeric)


	def toDict(self):
		return {
			"id": self.id,
			"idNumber": self.idNumber,
			"productType": self.productType,
			"addedTimestamp": self.addedTimestamp,
			"expiryDate": self.expiryDate,
			"quantityRemaining": self.quantityRemaining,
			"canExpire": self.canExpire,
			"price": self.price
		}


class VerificationRecord(Base):
	__tablename__ = "stockVerificationRecords"

	id = Column(Integer, primary_key=True)
	associatedStockItemId = Column(Integer, ForeignKey("stockItems.id"))
	isVerified = Column(Boolean, default=False)
	associatedCheckInRecord = Column(Integer, ForeignKey("checkInOutLog.id"))

	def toDict(self):
		return {
			"id": self.id,
			"associatedStockItemId": self.associatedStockItemId,
			"isVerified": self.isVerified,
			"checkInRecord": self.checkInRecord
		}


class ProductType(Base):
	__tablename__ = "productTypes"

	id = Column(Integer, primary_key=True)
	productName = Column(Text)
	tracksSpecificItems = Column(Boolean, default=False)
	tracksAllItemsOfProductType = Column(Boolean, default=False)
	# descriptors are to allow related stock to be collated,
	# e.g. different size paint tins
	productDescriptor1 = Column(Text, default="")
	productDescriptor2 = Column(Text, default="")
	productDescriptor3 = Column(Text, default="")
	addedTimestamp = Column(DateTime, server_default=func.now())
	initialQuantity = Column(Numeric)
	expectedPrice = Column(Numeric)
	barcode = Column(String)
	canExpire = Column(Boolean, default=False)
	associatedStock = relationship("StockItem", backref='productTypes')

	def toDict(self):
		return {
			"id": self.id,
			"productName": self.productName,
			"tracksSpecificItems": self.tracksSpecificItems,
			"tracksAllItemsOfProductType": self.tracksAllItemsOfProductType,
			"productDescriptor1": self.productDescriptor1,
			"productDescriptor2": self.productDescriptor2,
			"productDescriptor3": self.productDescriptor3,
			"addedTimestamp": self.addedTimestamp,
			"initialQuantity": self.initialQuantity,
			"expectedPrice": self.expectedPrice,
			"barcode": self.barcode,
			"canExpire": self.canExpire
		}


class CheckInOutRecord(Base):
	__tablename__ = "checkInOutLog"

	id = Column(Integer, primary_key=True)
	stockItem = Column(Integer, ForeignKey("stockItems.id"))
	qtyBeforeCheckout = Column(Numeric, default=0)
	checkoutTimestamp = Column(DateTime(timezone=True))
	quantityCheckedOut = Column(Numeric, default=0)
	checkinTimestamp = Column(DateTime(timezone=True))
	quantityCheckedIn = Column(Numeric, default=0)
	binId = Column(Integer, ForeignKey("bins.id"))
	jobId = Column(Integer, ForeignKey("jobs.id"))

	def toDict(self):
		return {
			"id": self.id,
			"stockItem": self.stockItem,
			"qtyBeforeCheckout": self.qtyBeforeCheckout,
			"checkoutTimestamp": self.checkoutTimestamp,
			"quantityCheckedOut": self.quantityCheckedOut,
			"checkinTimestamp": self.checkinTimestamp,
			"quantityCheckedIn": self.quantityCheckedIn,
			"binId": self.binId
		}


class Bin(Base):
	__tablename__ = "bins"

	id = Column(Integer, primary_key=True)
	idString = Column(String)
	locationName = Column(String)

	def toDict(self):
		return {
			"id": self.id,
			"idString": self.idString,
			"locationName": self.locationName
		}


class Job(Base):
	__tablename__ = "jobs"

	id = Column(Integer, primary_key=True)
	jobName = Column(String)
	associatedStockCheckouts = relationship("CheckInOutRecord", backref='Job')

	def toDict(self):
		return {
			"id": self.id,
			"jobName": self.jobName
		}



class User(Base):
	__tablename__ = "users"

	username = Column(Text, primary_key=True, unique=True)
	passwordHash = Column(Text)
	isAdmin = Column(Boolean, default=False)


class Setting(Base):
	__tablename__ = "settings"

	name = Column(String, primary_key=True)
	value = Column(String)