from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, \
	Text
from sqlalchemy.orm import declarative_base, relationship
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
#############################################################`

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
	price = Column(Numeric)
	isCheckedIn = Column(Boolean)  # this only applies to specific items, and should always be True for bulk
	associatedProduct = relationship("ProductType", back_populates="associatedStock")

	def toDict(self):
		return {
			"id": self.id,
			"idNumber": self.idNumber,
			"productType": self.productType,
			"addedTimestamp": self.addedTimestamp,
			"expiryDate": self.expiryDate,
			"quantityRemaining": self.quantityRemaining,
			"price": self.price,
			"isCheckedIn": self.isCheckedIn
		}


class VerificationRecord(Base):
	__tablename__ = "stockVerificationRecords"

	id = Column(Integer, primary_key=True)
	associatedStockItemId = Column(Integer, ForeignKey("stockItems.id"))
	isVerified = Column(Boolean, default=False)
	associatedCheckInRecord = Column(Integer, ForeignKey("checkInRecords.id"))

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
	quantityUnit = Column(String)
	expectedPrice = Column(Numeric)
	barcode = Column(String)
	canExpire = Column(Boolean, default=False)
	associatedStock = relationship("StockItem", back_populates='associatedProduct')
	associatedAssignedStock = relationship("AssignedStock", backref="productTypes")


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


class CheckInRecord(Base):
	__tablename__ = "checkInRecords"

	id = Column(Integer, primary_key=True)
	stockItem = Column(Integer, ForeignKey("stockItems.id"))
	checkInTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	quantityCheckedIn = Column(Numeric, default=0)
	binId = Column(Integer, ForeignKey("bins.id"))
	jobId = Column(Integer, ForeignKey("jobs.id"))
	associatedStockItem = relationship("StockItem", backref="checkInRecords")

	def toDict(self):
		return {
			"id": self.id,
			"stockItem": self.stockItem,
			"checkinTimestamp": self.checkinTimestamp,
			"quantityCheckedIn": self.quantityCheckedIn,
			"binId": self.binId,
			"jobId": self.jobId
		}


class CheckOutRecord(Base):
	__tablename__ = "checkOutRecords"

	id = Column(Integer, primary_key=True)
	stockItem = Column(Integer, ForeignKey("stockItems.id"))
	checkOutTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	quantityCheckedOut = Column(Numeric)
	binId = Column(Integer, ForeignKey("bins.id"))
	jobId = Column(Integer, ForeignKey("jobs.id"))
	associatedStockItem = relationship("StockItem", backref="checkOutRecords")

	def toDict(self):
		return{
			"id": self.id,
			"stockItem": self.stockItem,
			"checkOutTimestamp": self.checkOutTimestamp,
			"quantityCheckedOut": self.quantityCheckedOut,
			"binId": self.binId,
			"jobId": self.jobId
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
	addedTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	qrcodePath = Column(String)
	jobName = Column(String)
	associatedStockCheckins = relationship("CheckInRecord", backref='Job')
	associatedStockCheckouts = relationship("CheckOutRecord", backref='Job')
	associatedAssignedStock = relationship("AssignedStock", backref="Job")

	def toDict(self):
		return {
			"id": self.id,
			"addedTimestamp": self.addedTimestamp,
			"qrcodePath": self.qrcodePath,
			"jobName": self.jobName
		}


class AssignedStock(Base):
	__tablename__ = "assignedStock"

	id = Column(Integer, primary_key=True)
	productId = Column(Integer, ForeignKey("productTypes.id"))
	quantity = Column(Numeric)
	associatedJob = Column(Integer, ForeignKey("jobs.id"))
	associatedProduct = relationship("ProductType", backref="AssignedStock")

	def toDict(self):
		return{
			"id": self.id,
			"productId": self.productId,
			"quantity": self.quantity,
			"associatedJob": self.associatedJob
		}


class User(Base):
	__tablename__ = "users"

	username = Column(Text, primary_key=True, unique=True)
	passwordHash = Column(Text)
	isAdmin = Column(Boolean, default=False)


class Settings(Base):
	__tablename__ = "settings"

	id = Column(Integer, primary_key=True)
	stickerSheetPageHeight_mm = Column(Integer, default=297)
	stickerSheetPageWidth_mm = Column(Integer, default=210)
	stickerSheetStickersHeight_mm = Column(Integer, default=266)
	stickerSheetStickersWidth_mm = Column(Integer, default=190)
	stickerSheetDpi = Column(Integer, default=300)
	stickerSheetRows = Column(Integer, default=6)
	stickerSheetColumns = Column(Integer, default=3)
	stickerPadding_mm = Column(Integer, default=5)
	idCardHeight_mm = Column(Integer, default=55)
	idCardWidth_mm = Column(Integer, default=85)
	idCardDpi = Column(Integer, default=300)
	idCardPadding_mm = Column(Integer, default=5)
	displayIdCardName = Column(Boolean, default=True)
	displayJobIdCardName = Column(Boolean, default=True)
	idCardFontSize_px = Column(Integer, default=40)

	def toDict(self):
		return {
			"id": self.id,
			"stickerSheetPageHeight_mm": self.stickerSheetPageHeight_mm,
			"stickerSheetPageWidth_mm": self.stickerSheetPageWidth_mm,
			"stickerSheetStickersHeight_mm": self.stickerSheetStickersHeight_mm,
			"stickerSheetStickersWidth_mm": self.stickerSheetStickersWidth_mm,
			"stickerSheetDpi": self.stickerSheetDpi,
			"stickerSheetRows": self.stickerSheetRows,
			"stickerSheetColumns": self.stickerSheetColumns,
			"stickerPadding_mm": self.stickerPadding_mm,
			"idCardHeight_mm": self.idCardHeight_mm,
			"idCardWidth_mm": self.idCardWidth_mm,
			"idCardDpi": self.idCardDpi,
			"displayIdCardName": self.displayIdCardName,
			"displayJobIdCardName": self.displayJobIdCardName,
			"idCardFontSize_px": self.idCardFontSize_px
		}
