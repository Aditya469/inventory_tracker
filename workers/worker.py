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

import decimal
import json
import logging
import os
import sys
import datetime
import pika
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from dbSchema import Base, StockItem, CheckInRecord, CheckOutRecord, ProductType, ItemId, Bin, VerificationRecord, Job

systemRootDir = "/home/richard/work/DigitME/inventory_tracker"
dbConnString = f'sqlite:///{systemRootDir}/inventoryDB.sqlite'


def onAddStockRequest(ch, method, properties, body):
	try:
		print(" [x] Received %r" % body)
		logging.info("Processing request to add item")
		# check barcode number
		# create stock item
		engine = create_engine(dbConnString, echo=False)  # temporary for dev use
		Base.metadata.create_all(engine)

		Session = sessionmaker(bind=engine, future=True)
		session = Session()
		requestParams = json.loads(bytes.decode(body, 'utf-8'))

		if 'idNumber' not in requestParams:
			logging.error("Failed to process request to add item. ID number not provided")
			ch.basic_ack(delivery_tag=method.delivery_tag)
			return

		logging.info(f"Adding item with ID number {requestParams['idNumber']}")
		stockItem = session.query(StockItem).filter(StockItem.idNumber == requestParams['idNumber']).first()
		if stockItem is not None:
			productType = session.query(ProductType).filter(ProductType.id == stockItem.productType).first()
			if productType.tracksSpecificItems or not productType.tracksAllItemsOfProductType:
				logging.error("Got an ID number that exists for a non-bulk product")
				ch.basic_ack(delivery_tag=method.delivery_tag)
				return

			# stockItem is an existing bulk stock entry
			session.add(stockItem)
			stockItem.quantityRemaining += productType.initialQuantity
			session.commit()
			# ch.basic_ack(delivery_tag=method.delivery_tag)
			# return

		else:
			stockItem = StockItem()
			session.add(stockItem)
			itemId = session.query(ItemId).filter(ItemId.idNumber == requestParams['idNumber']).first()
			session.add(itemId)
			itemId.isPendingAssignment = False
			itemId.isAssigned = True
			stockItem.idNumber = requestParams['idNumber']
			stockItem.addedTimestamp = func.now()
			stockItem.isCheckedIn = True

			if 'expiryDate' in requestParams:
				stockItem.expiryDate = datetime.datetime.strptime(requestParams['expiryDate'], "%Y-%m-%d")

			if 'quantityCheckingIn' in requestParams:
				productQuantity = decimal.Decimal(requestParams['quantityCheckingIn'])

			if 'barcode' not in requestParams \
					or (session.query(ProductType).filter(ProductType.barcode == requestParams['barcode']).count() == 0):
				productType = session\
					.query(ProductType)\
					.filter(ProductType.productName == "undefined product type")\
					.first()
				stockItem.productType = productType.id
				stockItem.quantityRemaining = productType.initialQuantity
				stockItem.price = productType.expectedPrice
			else:
				productType = session\
					.query(ProductType)\
					.filter(ProductType.barcode == requestParams['barcode'])\
					.first()
				stockItem.productType = productType.id
				stockItem.quantityRemaining = productType.initialQuantity
				stockItem.price = productType.expectedPrice

		session.flush()
		checkInRecord = CheckInRecord()
		checkInRecord.stockItem = stockItem.id
		checkInRecord.qtyBeforeCheckout = None
		checkInRecord.checkInTimestamp = func.now()
		checkInRecord.quantityCheckedIn = productType.initialQuantity

		if 'binIdString' in requestParams:
			checkInRecord.binId = session.query(Bin.id).filter(Bin.idString == requestParams['binIdString']).first()[0]

		session.add(checkInRecord)
		session.flush()
		verificationRecord = VerificationRecord()
		verificationRecord.associatedCheckInRecord = checkInRecord.id
		verificationRecord.associatedStockItemId = stockItem.id
		verificationRecord.isVerified = False
		if "barcode" in requestParams:
			verificationRecord.itemBarcode = requestParams['barcode']
		session.add(verificationRecord)

		session.commit()
	except Exception as e:
		logging.error(e)
	ch.basic_ack(delivery_tag=method.delivery_tag)


def onCheckInRequest(ch, method, properities, body):
	try:
		print(" [x] Received %r" % body)
		engine = create_engine(dbConnString, echo=False)  # temporary for dev use
		Base.metadata.create_all(engine)

		Session = sessionmaker(bind=engine, future=True)
		session = Session()
		requestParams = json.loads(body)

		if 'stockIdNumber' not in requestParams:
			logging.error("Failed to process check In Request. Stock ID number not provided")
			ch.basic_ack(delivery_tag=method.delivery_tag)
			return
		logging.info(f"Processing check in request for stock item with ID number {requestParams['stockIdNumber']}")

		stockItem = session.query(StockItem)\
			.filter(StockItem.idNumber == int(requestParams['stockIdNumber']))\
			.limit(1)\
			.first()

		if stockItem is None:
			logging.error(f"Stock Item {requestParams['stockIdNumber']} does not exist in the database")

		if stockItem.isCheckedIn is True and session.query(ProductType.tracksSpecificItems)\
			.filter(ProductType.id == stockItem.productType).first()[0] is True:
			logging.error("Attempting to check in specific item that is already checked in")
			ch.basic_ack(delivery_tag=method.delivery_tag)
			return

		if "quantityCheckingIn" not in requestParams:
			logging.error("Failed to check in stock item. No quantity provided")
			ch.basic_ack(delivery_tag=method.delivery_tag)
			return

		checkInRecord = CheckInRecord()
		session.add(checkInRecord)
		checkInRecord.quantityCheckedIn = decimal.Decimal(requestParams['quantityCheckingIn'])
		checkInRecord.checkInTimestamp = func.now()
		checkInRecord.stockItem = stockItem.id

		if "jobId" in requestParams:
			checkInRecord.jobId = requestParams['jobId']

		if 'binId' in requestParams:
			checkInRecord.binId = requestParams['binId']

		stockItem.quantityRemaining += decimal.Decimal(requestParams['quantityCheckingIn'])
		stockItem.isCheckedIn = True
		session.commit()
	except Exception as e:
		logging.error(e)
	ch.basic_ack(delivery_tag=method.delivery_tag)


def onCheckOutRequest(ch, method, properities, body):
	try:
		print(" [x] Received %r" % body)
		engine = create_engine(dbConnString, echo=False)  # temporary for dev use
		Base.metadata.create_all(engine)

		Session = sessionmaker(bind=engine, future=True)
		session = Session()
		requestParams = json.loads(body)

		if 'stockIdNumber' not in requestParams:
			logging.error("Failed to process check out Request. Stock ID number not provided")
			ch.basic_ack(delivery_tag=method.delivery_tag)
			return

		logging.info(f"Processing check out request for stock item with ID number {requestParams['stockIdNumber']}")

		stockItem = session.query(StockItem)\
			.filter(StockItem.idNumber == int(requestParams['stockIdNumber']))\
			.limit(1)\
			.first()

		if stockItem is None:
			logging.error(f"Stock Item {requestParams['stockIdNumber']} does not exist in the database")
			ch.basic_ack(delivery_tag=method.delivery_tag)
			return

		isSpecificItem = session.query(ProductType.tracksSpecificItems)\
			.filter(ProductType.id == stockItem.productType).first()[0]
		if stockItem.isCheckedIn is False and isSpecificItem:
			logging.error("Attempting to check out specific item that is already checked out")
			ch.basic_ack(delivery_tag=method.delivery_tag)
			return

		checkOutRecord = CheckOutRecord()
		session.add(checkOutRecord)
		checkOutRecord.stockItem = stockItem.id
		checkOutRecord.checkOutTimestamp = func.now()
		checkOutRecord.qtyBeforeCheckout = stockItem.quantityRemaining

		if 'quantityCheckedOut' in requestParams:
			checkOutRecord.quantityCheckedOut = decimal.Decimal(requestParams['quantityCheckedOut'])
		else:
			if session.query(ProductType.tracksSpecificItems).filter(ProductType.id == stockItem.productType).first()[0] is False:
				logging.warning(
					"Bulk or non-specific stock item checked out without specifying quantity. Assuming all."
				)
			checkOutRecord.quantityCheckedOut = stockItem.quantityRemaining  # assumed to be specific items

		stockItem.quantityRemaining -= checkOutRecord.quantityCheckedOut

		if "jobId" in requestParams:
			checkOutRecord.jobId = requestParams['jobId']
		else:
			checkOutRecord.jobId = None

		if isSpecificItem:
			stockItem.isCheckedIn = False

		session.commit()
	except Exception as e:
		logging.error(e)
	ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
	rabbitMqHost = 'localhost'
	logging.basicConfig(filename="worker.log", level=logging.DEBUG, format='%(asctime)s %(message)s')
	logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
	logging.info("Worker starting")
	connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMqHost))
	logging.info(f"Connected to rabbitMQ node at {rabbitMqHost}")
	logger = logging.getLogger("pika")
	logger.setLevel(logging.WARNING)

	channel = connection.channel()
	channel.queue_declare(queue='addStockRequests')
	channel.queue_declare(queue='checkInRequests')
	channel.queue_declare(queue='checkOutRequests')

	channel.basic_consume(queue='addStockRequests', on_message_callback=onAddStockRequest)
	channel.basic_consume(queue='checkInRequests', on_message_callback=onCheckInRequest)
	channel.basic_consume(queue='checkOutRequests', on_message_callback=onCheckOutRequest)
	logging.info("Waiting for messages")
	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming()


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('Interrupted')
		try:
			sys.exit(0)
		except SystemExit:
			os._exit(0)