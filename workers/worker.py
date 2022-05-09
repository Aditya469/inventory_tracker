from .dbSchema import Base, ItemId, StockItem, CheckInOutRecord, ProductType
import json
import logging
import pika
from sqlalchemy import create_engine, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, Sequence, String, \
	Text, inspect
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

dbConnString = 'sqlite:///inventoryDB.sqlite'

def onAddStockRequest(ch, method, properties, body):
	print(" [x] Received %r" % body)
	logging.info("Processing request to add item")
	# check barcode number
	# create stock item
	engine = create_engine(dbConnString, echo=True)  # temporary for dev use
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine, future=True)
	session = Session()
	requestParams = json.loads(body)

	stockItem = StockItem()
	session.add(stockItem)

	if 'idNumber' not in requestParams:
		logging.error("Failed to process request to add item. ID number not provided")
		ch.basic_ack(delivery_tag=method.delivery_tag)
		return

	logging.info(f"Adding item with ID number {requestParams['idNumber']}")
	stockItem.idNumber = requestParams['idNumber']

	stockItem.addedTimestamp = func.now()

	if 'expiryDate' in requestParams:
		stockItem.expiryDate = requestParams['expiryDate']

	if 'canExpire' in requestParams:
		stockItem.canExpire = requestParams['canExpire']

	if 'barcode' not in requestParams or session.query(ProductType)\
			.filter(ProductType.barcode == requestParams['barcode']).count() == 0:
		stockItem.productType = session\
			.query(ProductType.id)\
			.filter(ProductType.productName == "undefined product type")\
			.first()
	else:
		productType = session\
			.query(ProductType)\
			.filter(ProductType.barcode == requestParams['barcode'])\
			.first()
		stockItem.idNumber = requestParams['idNumber']
		stockItem.productType = productType.id
		stockItem.quantityRemaining = productType['initialQuantity']
		stockItem.price = productType.expectedPrice

	session.commit()
	ch.basic_ack(delivery_tag=method.delivery_tag)


def onCheckInoutRequest(ch, method, properities, body):
	print(" [x] Received %r" % body)
	engine = create_engine(dbConnString, echo=True)  # temporary for dev use
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine, future=True)
	session = Session()
	requestParams = json.loads(body)

	if 'stockIdNumber' not in requestParams:
		logging.error("Failed to process checkInOutRequest. Stock ID number not provided")
		ch.basic_ack(delivery_tag=method.delivery_tag)
		return
	else:
		logging.info(f"Processing request for stock item with ID number {requestParams['stockIdNumber']}")

		stockItem = session.query(StockItem)\
			.filter_by(StockItem.idNumber == int(requestParams['stockIdNumber']))\
			.limit(1)\
			.first()

		if stockItem is None:
			logging.error(f"Stock Item {requestParams['stockIdNumber']} does not exist in the database")

		elif requestParams['requestType'] == 'checkout':
			checkInOutRecord = CheckInOutRecord()
			checkInOutRecord.stockItem = stockItem.id
			checkInOutRecord.checkoutTimestamp = func.now()
			checkInOutRecord.qtyBeforeCheckout = stockItem.quantityRemaining

			if 'quantityCheckedOut' in requestParams['quantityCheckedOut']:
				checkInOutRecord.quantityCheckedOut = float(requestParams['quantityCheckedOut'])
			else:
				if session.query(ProductType.tracksSpecificItems).filter(stockItem.productType).limit(1).first() is False:
					logging.warning(
						"Bulk or non-specific stock item checked out without specifying quantity. Assuming all."
					)
				checkInOutRecord.quantityCheckedOut = stockItem.quantityRemaining # assumed to be specific items

			stockItem.quantityRemaining -= checkInOutRecord.quantityCheckedOut
			session.add(checkInOutRecord)

		elif requestParams['requestType'] == 'checkin':
			checkInOutRecord = session.query(CheckInOutRecord)\
				.filter(CheckInOutRecord.id == stockItem.id)
			if checkInOutRecord.quantityCheckedOut == 0:
				checkInOutRecord.quantityCheckedOut = \
					checkInOutRecord.qtyBeforeCheckout - float(requestParams['quantityRemaining'])
			checkInOutRecord.quantityCheckedIn = float(requestParams['quantityRemaining'])
			checkInOutRecord.checkinTimestamp = func.now()
			session.add(checkInOutRecord)
			stockItem.quantityRemaining += float(requestParams['quantityRemaining'])



	ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
	rabbitMqHost = 'localhost'
	logging.basicConfig(filename="worker.log", level=logging.DEBUG, format='%(asctime)s %(message)s')
	logging.info("Worker starting")
	logging.info(f"Connected to rabbitMQ node at {rabbitMqHost}")
	connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMqHost))

	channel = connection.channel()
	channel.declare(queue='checkInOutRequests')

	channel.basic_consume(queue='checkInOutRequests', on_message_callback=onCheckInoutRequest)
