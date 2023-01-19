"""
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
"""
import datetime
import decimal

from flask import (
	Blueprint, render_template, request, make_response, jsonify, send_file, current_app
)
from sqlalchemy import select, or_, func, asc

from auth import login_required, create_access_required, admin_access_required
from db import getDbSession, close_db
from dbSchema import ProductType, StockItem, User, TemplateStockAssignment, AssignedStock, Settings
from emailNotification import sendEmail
from messages import getStockCheckInformationMessage
from qrCodeFunctions import generateIdQrCodeSheets
from stockManagement import updateNewStockWithNewProduct, deleteStockItemById, getAvailableStockTotalsDataFromRequest
from utilities import writeDataToCsvFile

bp = Blueprint('productManagement', __name__)


@bp.teardown_request
def afterRequest(self):
	close_db()

@bp.route('/productsAndNewStock')
@login_required
def getProductManagementPage():
	return render_template("productManagement.html")


@bp.route('/getProducts')
@login_required
def getProducts():
	productList = getProductsDataFromRequest()
	return make_response(jsonify(productList), 200)

def getProductsDataFromRequest():
	session = getDbSession()
	stmt = select(ProductType).where(ProductType.productName != "undefined product type")

	if "searchTerm" in request.args:
		searchTerm = "%" + request.args.get('searchTerm') + "%"

		stmt = stmt.where(
			or_(
				ProductType.productName.like(searchTerm),
				ProductType.productDescriptor1.like(searchTerm),
				ProductType.productDescriptor2.like(searchTerm),
				ProductType.productDescriptor3.like(searchTerm),
				ProductType.barcode.ilike(searchTerm)
			)
		)

	# add other search conditions as required

	stmt = stmt.order_by(ProductType.productName.asc())

	results = session.execute(stmt).scalars().all()
	productList = [row.toDict() for row in results]

	return productList


@bp.route('/getProduct/<productId>')
@login_required
def getProduct(productId):
	session = getDbSession()
	product = session.query(ProductType).filter(ProductType.id == productId).first()

	return make_response(jsonify(product.toDict()), 200)


@bp.route('/addProduct', methods=('POST',))
@create_access_required
def addNewProductType():
	session = getDbSession()
	errorState = None

	existingProductByBarcode = session.query(ProductType).filter(
		ProductType.barcode == request.form.get("barcode", default=None).strip()).first()
	if existingProductByBarcode is not None:
		errorState = "A product with that barcode already exists"

	existingProductByName = session.query(ProductType).filter(
		ProductType.productName == request.form.get("productName", default=None).strip()).first()
	if existingProductByName is not None:
		errorState = "A product with that name already exists"

	if errorState is None:
		newProduct = ProductType()
		session.add(newProduct)
		errorState, product = updateProductFromRequestForm(session, newProduct)

	if errorState is None:
		session.commit()
		updateNewStockWithNewProduct(product)
		return make_response(jsonify({"success": True, "message": "New product added", "id": product.id}), 200)
	else:
		return make_response(errorState, 400)


@bp.route('/updateProduct', methods=('POST',))
@create_access_required
def updateProductType():
	if 'id' not in request.form:
		return make_response("Product type ID required", 400)

	session = getDbSession()
	product = session.query(ProductType).filter(ProductType.id == request.form['id']).first()
	session.add(product)
	errorState, product = updateProductFromRequestForm(session, product)
	if errorState is None:
		session.commit()
		updateNewStockWithNewProduct(product)
		return make_response(jsonify({"success": True, "message": "Product details updated", "id": product.id}), 200)
	else:
		return make_response(jsonify({"success": False, "message": errorState}, 400))


@bp.route('/deleteProduct', methods=('POST',))
@create_access_required
def deleteProductType():
	if 'id' not in request.form:
		return make_response("Product type ID required", 400)

	dbSession = getDbSession()
	productType = dbSession.get(ProductType, request.form['id'])

	# delete associated stock items first. Ideally this would be cascaded through by SqlAlchemy, but in the interests
	# of getting this work quickly, I'm doing it this way. TODO: improve this.
	stockItems = dbSession.query(StockItem).filter(StockItem.productType == productType.id).all()
	for stockItem in stockItems:
		deleteStockItemById(stockItem.id)

	# any stock or template assignments referencing this product type also need to be deleted.
	# TODO: set up cascading as above
	dbSession.query(TemplateStockAssignment).filter(TemplateStockAssignment.productId == productType.id).delete()
	dbSession.query(AssignedStock).filter(AssignedStock.productId == productType.id).delete()

	dbSession.delete(productType)
	dbSession.commit()

	return make_response("Product deleted", 200)


def updateProductFromRequestForm(session, product):
	error = None

	if "productName" not in request.form:
		error = "Product name must be defined"
	if "itemTrackingType" not in request.form:
		error = "This product must be specified as specific items or bulk items"
	if "initialQuantity" not in request.form:
		error = "The initial pack quantity of the product must be defined"
	if "barcode" not in request.form:
		error = "The product barcode must be defined"

	if error is not None:
		return error, None

	product.productName = request.form["productName"].strip()
	if request.form["itemTrackingType"] == "specific":
		product.tracksSpecificItems = True
		product.tracksAllItemsOfProductType = False
	elif request.form["itemTrackingType"] == "bulk":
		product.tracksSpecificItems = False
		product.tracksAllItemsOfProductType = True

	if "quantityUnit" in request.form:
		product.quantityUnit = request.form["quantityUnit"].strip()

	product.initialQuantity = decimal.Decimal(request.form["initialQuantity"])
	product.barcode = request.form["barcode"]
	if "productDescriptor1" in request.form:
		product.productDescriptor1 = request.form["productDescriptor1"].strip()
	if "productDescriptor2" in request.form:
		product.productDescriptor2 = request.form["productDescriptor2"].strip()
	if "productDescriptor3" in request.form:
		product.productDescriptor3 = request.form["productDescriptor3"].strip()
	if "expectedPrice" in request.form and request.form['expectedPrice'] != "":
		product.expectedPrice = decimal.Decimal(request.form["expectedPrice"])

	if "canExpire" in request.form:
		if request.form["canExpire"] == "true":
			product.canExpire = True
		else:
			product.canExpire = False

	if "notifyExpiry" in request.form:
		if request.form["notifyExpiry"] == "true":
			product.notifyExpiry = True
		else:
			product.notifyExpiry = False

	if "expiryWarningDayCount" in request.form:
		product.expiryWarningDayCount = int(request.form["expiryWarningDayCount"])

	if "reorderLevel" in request.form and request.form["reorderLevel"] != "":
		product.reorderLevel = decimal.Decimal(request.form["reorderLevel"])
	else:
		product.reorderLevel = None

	if "sendStockNotifications" in request.form:
		product.sendStockNotifications = request.form["sendStockNotifications"] == "true"

	if "newStockOrdered" in request.form:
		product.stockReordered = request.form["newStockOrdered"] == "true"

	product.lastUpdated = func.current_timestamp()

	return None, product

@bp.route('/runStockCheck', methods=('POST',))
@admin_access_required
def runStockCheck():
	performStockCheckAndReport()
	return make_response("Stock Check Complete", 200)


def performStockCheckAndReport():
	"""
	Function to run periodically which finds products that are below the
	reorder level and marks them appropriately in the database.

	Produces an email notification that includes a list of stock needing
	reordering, and stock that is within its product-type's expiry warning
	period.
	"""
	dbSession = getDbSession()

	useAvailableStockTotals = dbSession.query(Settings.stockCheckAvailableLevels).first()[0]

	productList = dbSession.query(ProductType)\
		.filter(ProductType.reorderLevel != None) \
		.filter(ProductType.reorderLevel != "None") \
		.order_by(asc(func.lower(ProductType.productName))) \
		.all()

	productsNeedingReorder = []
	expiringStockItems = []
	expiredStockItems = []



	availableStock = getAvailableStockTotalsDataFromRequest()

	for product in productList:
		if useAvailableStockTotals:
			# loop through availableStock to find this product. This is a very ugly way of doing this,
			# but I'm short of time, so it'll do for now. TODO: rework this into something less cumbersome
			for i in range(len(availableStock)):
				if availableStock[i]['productId'] == product.id:
					stockQty = availableStock[i]['stockAmountRaw']
					break
		else:
			stockQty = dbSession.query(func.sum(StockItem.quantityRemaining))\
				.filter(StockItem.productType == product.id)\
				.first()[0]

		if stockQty is None or stockQty <= product.reorderLevel:
			product.needsReordering = True
			if product.sendStockNotifications and not product.stockReordered:
				productsNeedingReorder.append(product)
		else:
			product.needsReordering = False

		# check for expiring stock of this product type
		currentDate = datetime.datetime.now().date()
		if product.notifyExpiry:
			expiryDateUpperLimit = datetime.datetime.now() + datetime.timedelta(product.expiryWarningDayCount)
			expiringStock = dbSession.query(StockItem)\
				.filter(StockItem.productType == product.id)\
				.filter(StockItem.expiryDate >= currentDate)\
				.filter(StockItem.expiryDate <= expiryDateUpperLimit)\
				.filter(StockItem.quantityRemaining > 0)\
				.all()

			for stockItem in expiringStock:
				expiringStockItems.append(stockItem)

		# check for expired stock
		expiredStock = dbSession.query(StockItem) \
			.filter(StockItem.productType == product.id) \
			.filter(StockItem.expiryDate < currentDate) \
			.filter(StockItem.quantityRemaining > 0) \
			.all()

		for stockItem in expiredStock:
			expiredStockItems.append(stockItem)

	emailAddressList = [row[0] for row in dbSession.query(User.emailAddress).filter(User.receiveStockNotifications == True).all()]
	message = getStockCheckInformationMessage(productsNeedingReorder, expiringStockItems, expiredStockItems)
	sendEmail(emailAddressList, "Stock Check Information", message)

	dbSession.commit()
	close_db()


@bp.route("/getProductsCsvFile", methods=("GET",))
@login_required
def getProductsCsvFile():
	productData = getProductsDataFromRequest()
	headingDictList = [
		{"heading": "Product Name", "dataName": "productName"},
		{"heading": "Barcode", "dataName": "barcode"},
		{"heading": "Is Bulk?", "dataName": "tracksAllItemsOfProductType"},
		{"heading": "Descriptor 1", "dataName": "productDescriptor1"},
		{"heading": "Descriptor 2", "dataName": "productDescriptor2"},
		{"heading": "Descriptor 3", "dataName": "productDescriptor3"},
	]
	csvPath = writeDataToCsvFile(headingsDictList=headingDictList, dataDictList=productData)

	return send_file(csvPath, as_attachment=True, download_name="ProductInfo.csv", mimetype="text/csv")


@bp.route("/getProductTypeLastUpdateTimestamp")
@login_required
def getProductTypeLastUpdateTimestamp():
	itemId = request.args.get("itemId")
	dbSession = getDbSession()
	item = dbSession.query(ProductType).filter(ProductType.id == itemId).one()
	timestamp = item.lastUpdated.strftime("%d/%m/%y %H:%M:%S")
	return make_response(timestamp, 200)


@bp.route("/getProductBarcodeStickerSheet")
@login_required
def getProductBarcodeStickerSheet():
	if "idQty" in request.args:
		idQty = request.args.get("idQty")
	else:
		idQty = None

	if "productId" not in request.args:
		return make_response("productId must be specified", 400)

	dbSession = getDbSession()
	product = dbSession.query(ProductType).filter(ProductType.id == request.args.get("productId")).first()

	sheets, error = generateIdQrCodeSheets(idQty, product.barcode, sheetHeaderText=f"{product.productName} Identifier Sticker Sheet")

	if error is not None:
		return make_response(error)

	sheets[0].save(f"{current_app.instance_path}/stickers.png")
	return send_file(f"{current_app.instance_path}/stickers.png", as_attachment=True,
					 download_name=f"{product.productName} ID Sticker Sheet.png")