'''
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
'''
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, \
	Text, Time
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# this section borrowed from https://stackoverflow.com/questions/10355767/how-should-i-handle-decimal-in-sqlalchemy-sqlite
from decimal import Decimal as D
import sqlalchemy.types as types
from datetime import datetime

class Numeric(types.TypeDecorator):
	impl = types.String

	def load_dialect_impl(self, dialect):
		return dialect.type_descriptor(types.VARCHAR(100))

	def process_bind_param(self, value, dialect):
		return str(value)

	def process_result_value(self, value, dialect):
		if value != "None" and value != None:
			return D(value)
		return None
#############################################################`

class ItemId(Base):
	__tablename__ = "itemIds"

	idNumber = Column(Integer, primary_key=True, unique=True)
	isPendingAssignment = Column(Boolean, default=False)
	isAssigned = Column(Boolean, default=False)
	idString = Column(String)
	associatedStock = relationship("StockItem", backref='itemIds', uselist=False)

	def toDict(self):
		return {
			"idNumber": self.idNumber,
			"isPendingAssignment": self.isPendingAssignment,
			"isAssigned": self.isAssigned,
			"idString": self.idString
		}


# simple alias class to allow one ID to point to another, to allow for multiple IDs to be the same bulk product
class IdAlias(Base):
	__tablename__ = "idAlias"
	id = Column(Integer, primary_key=True, unique=True)
	idString = Column(String)
	stockItemAliased = Column(String, ForeignKey("stockItems.id"))


class StockItem(Base):
	__tablename__ = "stockItems"

	id = Column(Integer, primary_key=True)  # ID in the database rather than QR code ID
	idString = Column(String, ForeignKey("itemIds.idString"))
	productType = Column(Integer, ForeignKey("productTypes.id"))
	addedTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	expiryDate = Column(Date, server_default=None)
	quantityRemaining = Column(Numeric, default=0)
	price = Column(Numeric)
	isCheckedIn = Column(Boolean)  # this only applies to specific items, and should always be True for bulk
	associatedProduct = relationship("ProductType", back_populates="associatedStock")

	def toDict(self):
		dataDict = {
			"id": self.id,
			"idNumber": self.idString,
			"productType": self.productType,
			"addedTimestamp": "",
			"expiryDate": self.expiryDate,
			"quantityRemaining": self.quantityRemaining,
			"price": self.price,
			"isCheckedIn": self.isCheckedIn
		}
		if self.addedTimestamp:
			dataDict["addedTimestamp"] = self.addedTimestamp.strftime("%d/%m/%y %H:%M")



class VerificationRecord(Base):
	__tablename__ = "stockVerificationRecords"

	id = Column(Integer, primary_key=True)
	associatedStockItemId = Column(Integer, ForeignKey("stockItems.id"))
	isVerified = Column(Boolean, default=False)
	itemBarcode = Column(String)
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
	initialQuantity = Column(Numeric, default="")
	quantityUnit = Column(String, default="")
	expectedPrice = Column(Numeric, default=0)
	barcode = Column(String, default="undefined")
	canExpire = Column(Boolean, default=False)
	reorderLevel = Column(Numeric, default=None)
	sendStockNotifications = Column(Boolean, default=False)
	needsReordering = Column(Boolean, default=False)
	stockReordered = Column(Boolean, default=False)
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
			"quantityUnit": self.quantityUnit,
			"expectedPrice": self.expectedPrice,
			"barcode": self.barcode,
			"canExpire": self.canExpire,
			"reorderLevel": self.reorderLevel,
			"sendStockNotifications": self.sendStockNotifications,
			"needsReordering": self.needsReordering,
			"stockReordered": self.stockReordered
		}


class CheckInRecord(Base):
	__tablename__ = "checkInRecords"

	id = Column(Integer, primary_key=True)
	stockItem = Column(Integer, ForeignKey("stockItems.id"))
	timestamp = Column(DateTime(timezone=True), server_default=func.now())
	quantity = Column(Numeric, default=0)
	binId = Column(Integer, ForeignKey("bins.id"), default=-1)
	jobId = Column(Integer, ForeignKey("jobs.id"))
	userId = Column(Integer, ForeignKey("users.id"))
	associatedStockItem = relationship("StockItem", backref="checkInRecords")
	createdByRequestId = Column(String)

	def toDict(self):
		dataDict = {
			"id": self.id,
			"stockItem": self.stockItem,
			"timestamp": "",
			"quantity": self.quantity,
			"binId": self.binId,
			"jobId": self.jobId,
			"userId": self.userId
		}
		if self.timestamp:
			dataDict["timestamp"] = self.timestamp.strftime("%d/%m/%y %H:%M")

		return dataDict


class CheckOutRecord(Base):
	__tablename__ = "checkOutRecords"

	id = Column(Integer, primary_key=True)
	stockItem = Column(Integer, ForeignKey("stockItems.id"))
	timestamp = Column(DateTime(timezone=True), server_default=func.now())
	quantity = Column(Numeric)
	binId = Column(Integer, ForeignKey("bins.id"))
	jobId = Column(Integer, ForeignKey("jobs.id"))
	userId = Column(Integer, ForeignKey("users.id"))
	associatedStockItem = relationship("StockItem", backref="checkOutRecords")
	createdByRequestId = Column(String)

	def toDict(self):
		dataDict = {
			"id": self.id,
			"stockItem": self.stockItem,
			"timestamp": "",
			"quantity": self.quantity,
			"binId": self.binId,
			"jobId": self.jobId,
			"userId": self.userId
		}
		if self.timestamp:
			dataDict["timestamp"] = self.timestamp.strftime("%d/%m/%y %H:%M")

		return dataDict


class Bin(Base):
	__tablename__ = "bins"

	id = Column(Integer, primary_key=True)
	idString = Column(String)
	locationName = Column(String)
	qrCodeName = Column(String)

	def toDict(self):
		return {
			"id": self.id,
			"idString": self.idString,
			"locationName": self.locationName,
			"qrCodeName": self.qrCodeName
		}


class Job(Base):
	__tablename__ = "jobs"

	id = Column(Integer, primary_key=True)
	idString = Column(String, unique=True)
	addedTimestamp = Column(DateTime(timezone=True), server_default=func.now())
	qrCodeName = Column(String)
	jobName = Column(String)
	associatedStockCheckins = relationship("CheckInRecord", backref='Job')
	associatedStockCheckouts = relationship("CheckOutRecord", backref='Job')
	associatedAssignedStock = relationship("AssignedStock", backref="Job")

	def toDict(self):
		dataDict = {
			"id": self.id,
			"addedTimestamp": "",
			"qrCodeName": self.qrCodeName,
			"jobName": self.jobName
		}
		if self.addedTimestamp:
			dataDict["addedTimestamp"] = self.addedTimestamp.strftime("%d/%m/%y %H:%M")
		return dataDict




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

	id = Column(Integer, primary_key=True, unique=True)
	username = Column(Text)
	idString = Column(Text)
	passwordHash = Column(Text)
	accessLevel = Column(Integer, default=0)  # 0 = read-only, 1 = edit, 2 = create, 3 = admin
	emailAddress = Column(Text)
	receiveStockNotifications = Column(Boolean, default=False)
	receiveDbStatusNotifications = Column(Boolean, default=False)

	def toDict(self):
		return{
			"username": self.username,
			"passwordHash": self.passwordHash,
			"accessLevel": self.accessLevel,
			"emailAddress": self.emailAddress,
			"receiveStockNotifications": self.receiveStockNotifications,
			"receiveDbStatusNotifications": self.receiveDbStatusNotifications
		}


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
	displayBinIdCardName = Column(Boolean, default=True)
	emailSmtpServerName = Column(String)
	emailSmtpServerPort = Column(String)
	emailAccountName = Column(String)
	emailAccountPassword = Column(String)
	emailSecurityMethod = Column(String)
	sendEmails = Column(Boolean)
	dbNumberOfBackups = Column(Integer, default=5)
	dbBackupAtTime = Column(Time(timezone=True))
	dbMakeBackups = Column(Boolean, default=True)
	stockLevelReorderCheckAtTime = Column(Time(timezone=True))

	def toDict(self):
		dataDict = {
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
			"idCardPadding_mm": self.idCardPadding_mm,
			"displayIdCardName": self.displayIdCardName,
			"displayJobIdCardName": self.displayJobIdCardName,
			"idCardFontSize_px": self.idCardFontSize_px,
			"displayBinIdCardName": self.displayBinIdCardName,
			"emailSmtpServerName": self.emailSmtpServerName,
			"emailSmtpServerPort": self.emailSmtpServerPort,
			"emailAccountName": self.emailAccountName,
			"emailAccountPassword": self.emailAccountPassword,
			"emailSecurityMethod": self.emailSecurityMethod,
			"sendEmails": self.sendEmails,
			"dbNumberOfBackups": self.dbNumberOfBackups,
			"dbMakeBackups": self.dbMakeBackups,
		}
		if self.dbBackupAtTime is None:
			dataDict["dbBackupAtTime"] = None
		else:
			dataDict["dbBackupAtTime"] = self.dbBackupAtTime.strftime("%H:%M")

		if self.stockLevelReorderCheckAtTime is None:
			dataDict["stockLevelReorderCheckAtTime"] = None
		else:
			dataDict["stockLevelReorderCheckAtTime"] = self.stockLevelReorderCheckAtTime.strftime("%H:%M")


		return dataDict

