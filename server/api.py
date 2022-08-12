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
from .auth import login_required
from dbSchema import ProductType, StockItem, Bin
from db import getDbSession
from sqlalchemy import select, or_
import decimal

bp = Blueprint('api', __name__)



# note that these functions doesn't have login requirement at the moment as
# they're used by the app. TODO: secure this

@bp.route("/getAppProductData")
def getAppProductData():
	dbSession = getDbSession()
	products = dbSession.query(ProductType).all()

	productList = []
	for product in products:
		productDict = {
			"id": product.id,
			"barcode": product.barcode,
			"name": product.productName,
			"expires": product.canExpire,
			"isBulk": product.tracksAllItemsOfProductType,
			"isAssignedStockId": False,
			"associatedStockId": None,
			"productUnit": product.quantityUnit
		}
		if product.tracksAllItemsOfProductType:
			associatedStockItem = dbSession.query(StockItem).filter(StockItem.productType == product.id).first()
			if associatedStockItem is not None:
				productDict["isAssignedId"] = True
				productDict["assocaitedStockId"] = associatedStockItem.id
		productList.append(productDict)

	return make_response(jsonify(productList), 200)


@bp.route("/getAppBinData")
def getAppBinData():
	dbSession = getDbSession()
	binList = [{"idString": bin_.idString, "locationName": bin_.locationName} for bin_ in dbSession.query(Bin).all()]
	return make_response(jsonify(binList), 200)
