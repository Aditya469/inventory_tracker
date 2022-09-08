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

from flask import (
	Blueprint, render_template, request, make_response, jsonify
)
from werkzeug.utils import secure_filename

from stockManagement import updateNewStockWithNewProduct
from .auth import login_required, admin_access_required,create_access_required,edit_access_required
from dbSchema import ProductType, StockItem
from db import getDbSession
from sqlalchemy import select, or_
import decimal

bp = Blueprint('productManagement', __name__)


@bp.route('/productsAndNewStock')
@login_required
def getProductManagementPage():
	return render_template("productManagement.html")


@bp.route('/getProducts')
@login_required
def getProducts():
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

	return make_response(jsonify(productList), 200)


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
	existingProduct = session.query(ProductType).filter(ProductType.barcode == request.form.get("barcode", default=None)).first()
	if existingProduct:
		errorState = "A product with that barcode already exists"
	else:
		newProduct = ProductType()
		session.add(newProduct)
		errorState, product = updateProductFromRequestForm(session, newProduct)
	if errorState is None:
		session.commit()
		updateNewStockWithNewProduct(product)
		return make_response("New product added", 200)
	else:
		return make_response(errorState, 400)


@bp.route('/updateProduct', methods=('POST',))
@edit_access_required
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
		return make_response("Product details updated", 200)
	else:
		return make_response(errorState, 400)


@bp.route('/deleteProduct', methods=('POST',))
@create_access_required
def deleteProductType():
	if 'id' not in request.form:
		return make_response("Product type ID required", 400)

	session = getDbSession()
	productType = session.get(ProductType, request.form['id'])
	session.delete(productType)
	session.commit()

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

	product.productName = request.form["productName"]
	if request.form["itemTrackingType"] == "specific":
		product.tracksSpecificItems = True
		product.tracksAllItemsOfProductType = False
	elif request.form["itemTrackingType"] == "bulk":
		product.tracksSpecificItems = False
		product.tracksAllItemsOfProductType = True

	if "quantityUnit" in request.form:
		product.quantityUnit = request.form["quantityUnit"]

	product.initialQuantity = decimal.Decimal(request.form["initialQuantity"])
	product.barcode = request.form["barcode"]
	if "productDescriptor1" in request.form:
		product.productDescriptor1 = request.form["productDescriptor1"]
	if "productDescriptor2" in request.form:
		product.productDescriptor2 = request.form["productDescriptor2"]
	if "productDescriptor3" in request.form:
		product.productDescriptor3 = request.form["productDescriptor3"]
	if "expectedPrice" in request.form and request.form['expectedPrice'] != "":
		product.expectedPrice = decimal.Decimal(request.form["expectedPrice"])

	if "canExpire" in request.form:
		if request.form["canExpire"] == "true":
			product.canExpire = True
		else:
			product.canExpire = False

	if "reorderLevel" in request.form:
		product.reorderLevel = request.form["reorderLevel"]

	if "sendStockNotifications" in request.form:
		product.sendStockNotifications = request.form["sendStockNotifications"] == "true"

	return None, product


