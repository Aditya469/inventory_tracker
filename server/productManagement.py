from unittest.mock import _patch_dict

from flask import (
	Blueprint, render_template, request, make_response, jsonify
)
from werkzeug.utils import secure_filename

from .auth import login_required
from dbSchema import ProductType
from db import getDbSession
from sqlalchemy import select, or_

bp = Blueprint('productManagement', __name__)


@bp.route('/productManagement')
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

	results = session.execute(stmt).scalars().all()
	productList = [row.toDict() for row in results]

	return make_response(jsonify(productList), 200)


@bp.route('/addProduct', methods=('POST',))
@login_required
def addNewProductType():
	session = getDbSession()
	newProduct = ProductType()
	session.add(newProduct)
	errorState, product = updateProductFromRequestForm(session, newProduct)
	if errorState is None:
		session.commit()
		return make_response("New product added", 200)
	else:
		return make_response(errorState, 400)


@bp.route('/updateProduct', methods=('POST',))
@login_required
def updateProductType():
	if 'id' not in request.form:
		return make_response("Product type ID required", 400)

	session = getDbSession()
	product = session.query(ProductType).filter(ProductType.id == request.form['id']).first()
	session.add(product)
	errorState, product = updateProductFromRequestForm(session, product)
	if errorState is None:
		session.commit()
		return make_response("Product details updated", 200)
	else:
		return make_response(errorState, 400)


@bp.route('/deleteProduct', methods=('POST',))
@login_required
def deleteProductType():
	if 'id' not in request.form:
		return make_response("Product type ID required", 400)

	session = getDbSession()
	productType = session.get(ProductType, request.form['id'])
	session.delete(productType)

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

	product.initialQuantity = request.form["initialQuantity"]
	product.barcode = request.form["barcode"]
	if "productDescriptor1" in request.form:
		product.productDescriptor1 = request.form["productDescriptor1"]
	if "productDescriptor2" in request.form:
		product.productDescriptor2 = request.form["productDescriptor2"]
	if "productDescriptor3" in request.form:
		product.productDescriptor3 = request.form["productDescriptor3"]
	if "expectedPrice" in request.form:
		product.expectedPrice = request.form["expectedPrice"]

	if "canExpire" in request.form and request.form["canExpire"] == "True":
		product.canExpire = True

	return None, product

