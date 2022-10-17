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

import csv
import decimal
import json

from flask import (
    Blueprint, current_app, make_response, render_template, send_file, jsonify, request
)
from werkzeug.utils import secure_filename
import datetime
from auth import login_required, admin_access_required, create_access_required, edit_access_required
from db import getDbSession, Settings
from qrCodeFunctions import convertDpiAndMmToPx, generateItemIdQrCodeSheets
from dbSchema import StockItem, ProductType, AssignedStock, CheckInRecord, VerificationRecord, Bin, CheckOutRecord, \
    User, Job
from utilities import writeDataToCsvFile
from sqlalchemy import select, delete, func, or_, update, and_

bp = Blueprint('stockManagement', __name__)


@bp.route('/stockManagement')
@login_required
def getStockPage():
    productName = request.args.get("productName", default=None)
    return render_template("stockManagement.html", productName=productName)


@bp.route('/getIdStickerSheet')
@create_access_required
def getItemStickerSheet():
    dbSession = getDbSession()
    pageWidth_mm = dbSession.query(Settings.stickerSheetPageWidth_mm).first()[0]
    pageHeight_mm = dbSession.query(Settings.stickerSheetPageHeight_mm).first()[0]
    stickerAreaWidth_mm = dbSession.query(Settings.stickerSheetStickersWidth_mm).first()[0]
    stickerAreaHeight_mm = dbSession.query(Settings.stickerSheetStickersHeight_mm).first()[0]
    stickerPadding_mm = dbSession.query(Settings.stickerPadding_mm).first()[0]
    stickerSheetDpi = dbSession.query(Settings.stickerSheetDpi).first()[0]

    pageWidthPx = convertDpiAndMmToPx(length_mm=pageWidth_mm, DPI=stickerSheetDpi)
    pageHeightPx = convertDpiAndMmToPx(length_mm=pageHeight_mm, DPI=stickerSheetDpi)
    stickerAreaWidthPx = convertDpiAndMmToPx(length_mm=stickerAreaWidth_mm, DPI=stickerSheetDpi)
    stickerAreaHeightPx = convertDpiAndMmToPx(length_mm=stickerAreaHeight_mm, DPI=stickerSheetDpi)
    stickerPaddingPx = convertDpiAndMmToPx(length_mm=stickerPadding_mm, DPI=stickerSheetDpi)

    stickerRows = dbSession.query(Settings.stickerSheetRows).first()[0]
    stickerColumns = dbSession.query(Settings.stickerSheetColumns).first()[0]

    if "idQty" in request.args:
        idQty = request.args.get("idQty")
    else:
        idQty = stickerRows * stickerColumns

    # temporary limitation until I find a suitable python pdf library
    if idQty > (stickerRows * stickerColumns):
        return make_response(f"You may only request up to {stickerRows * stickerColumns} at a time")

    sheets = generateItemIdQrCodeSheets(
        idQty,
        stickerRows,
        stickerColumns,
        pageWidthPx,
        pageHeightPx,
        stickerAreaWidthPx,
        stickerAreaHeightPx,
        stickerPaddingPx
    )

    sheets[0].save(f"{current_app.instance_path}/stickers.png")
    return send_file(f"{current_app.instance_path}/stickers.png", as_attachment=True, download_name="Item ID Sticker Sheet.png")


@bp.route('/getStock')
@login_required
def getStock():
    stockList = getStockDataFromRequest()
    return make_response(jsonify(stockList), 200)


def getStockDataFromRequest():
    session = getDbSession()
    stmt = select(
        StockItem.id,
        StockItem.idString,
        ProductType.canExpire,
        StockItem.expiryDate,
        StockItem.quantityRemaining,
        StockItem.price,
        ProductType.productName,
        ProductType.barcode,
        ProductType.quantityUnit
    ).join(ProductType, StockItem.productType == ProductType.id)

    # selection criteria...
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
        if request.args.get("searchByProductTypeName", default="false") == "true":
            stmt = stmt.where(ProductType.productName.ilike(searchTerm))
        if request.args.get("searchByIdNumber", default="false") == "true":
            stmt = stmt.where(StockItem.idString.ilike(searchTerm))
        if request.args.get("searchByBarcode", default="false") == "true":
            stmt = stmt.where(ProductType.barcode.ilike(searchTerm))
        if request.args.get("searchByDescriptors", default="false") == "true":
            stmt = stmt.where(or_(
                ProductType.productDescriptor1.ilike(searchTerm),
                ProductType.productDescriptor2.ilike(searchTerm),
                ProductType.productDescriptor3.ilike(searchTerm)
            ))

    if "onlyShowExpirableStock" in request.args:
        if request.args.get("onlyShowExpirableStock", default="false") == "true":
            stmt = stmt.where(ProductType.canExpire)

    if "limitExpiryDates" in request.args:
        if request.args.get("limitExpiryDates", default="false") == "true":
            if "expiryStartDate" in request.args:
                expRangeStartDate = datetime.datetime.strptime(request.args.get("expiryStartDate"), "%Y-%m-%d")
                stmt = stmt.where(StockItem.expiryDate >= expRangeStartDate)

            if "expiryEndDate" in request.args:
                expRangeEndDate = datetime.datetime.strptime(request.args.get("expiryEndDate"), "%Y-%m-%d")\
                    .replace(hour=11, minute=59)
                stmt = stmt.where(StockItem.expiryDate <= expRangeEndDate)

    if "limitByPrice" in request.args:
        if request.args.get("limitByPrice", default="false") == "true":
            if "priceRangeStart" in request.args:
                stmt = stmt.where(StockItem.price >= decimal.Decimal(request.args.get("priceRangeStart")))
            if "priceRangeEnd" in request.args:
                stmt = stmt.where(StockItem.price <= decimal.Decimal(request.args.get("priceRangeEnd")))

    if "hideZeroStockEntries" in request.args:
        if request.args.get("hideZeroStockEntries", default="false") == "true":
            stmt = stmt.where(StockItem.quantityRemaining != 0)

    if "hideNonzeroStockEntries" in request.args:
        if request.args.get("hideNonzeroStockEntries", default="false") == "true":
            stmt = stmt.where(StockItem.quantityRemaining == 0)

    # ... and ordering
    if "sortBy" in request.args:
        if request.args.get("sortBy") == "productNameAsc":
            stmt = stmt.order_by(ProductType.productName.asc())
        elif request.args.get("sortBy") == "productNameDesc":
            stmt = stmt.order_by(ProductType.productName.desc())
        elif request.args.get("sortBy") == "dateAddedAsc":
            stmt = stmt.order_by(StockItem.addedTimestamp.asc())
        elif request.args.get("sortBy") == "dateAddedDesc":
            stmt = stmt.order_by(StockItem.addedTimestamp.desc())
        elif request.args.get("sortby") == "expiryDateAsc":
            stmt = stmt.order_by(StockItem.expiryDate.asc())
        elif request.args.get("sortby") == "expiryDateDesc":
            stmt = stmt.order_by(StockItem.expiryDate.desc())
        # etc...
    else:
        stmt = stmt.order_by(StockItem.addedTimestamp)

    results = session.execute(stmt).all()

    stockList = []
    for row in results:
        rowDict = {}
        rowDict["id"] = row[0]
        rowDict["idNumber"] = row[1]
        rowDict["canExpire"] = row[2]
        if rowDict["canExpire"]:
            rowDict["expiryDate"] = row[3].strftime("%Y-%m-%d")
        else:
            rowDict["expiryDate"] = ""
        rowDict["quantityRemaining"] = row[4]
        rowDict["price"] = row[5]
        rowDict["productName"] = row[6]
        rowDict["productBarcode"] = row[7]
        rowDict["quantityUnit"] = row[8]
        stockList.append(rowDict)

    return stockList


@bp.route('/getStockDetails/<stockId>')
@login_required
def getStockItemById(stockId):
    session = getDbSession()
    stockItem = session.query(
        StockItem.id,
        StockItem.idString,
        StockItem.productType,
        StockItem.addedTimestamp,
        StockItem.expiryDate,
        ProductType.canExpire,
        StockItem.quantityRemaining,
        ProductType.quantityUnit,
        StockItem.price,
        StockItem.isCheckedIn,
        ProductType.productName,
        ProductType.productDescriptor1,
        ProductType.productDescriptor2,
        ProductType.productDescriptor3,
        ProductType.tracksAllItemsOfProductType,
        ProductType.tracksSpecificItems
    ) \
        .filter(StockItem.id == stockId) \
        .join(ProductType, ProductType.id == StockItem.productType) \
        .first()

    lastSeenBinId = session.query(CheckInRecord.binId) \
        .filter(CheckInRecord.stockItem == stockId) \
        .order_by(CheckInRecord.timestamp.desc()) \
        .first()[0]

    if lastSeenBinId is not None:
        binId = lastSeenBinId
    else:
        binId = None


    if stockItem[4]: # expiry date
        expiryDate = stockItem[4].strftime("%Y-%m-%d")
    else:
        expiryDate = ""


    # get a dictionary of all check-ins and -outs, formatted into a nice table-friendly structure, in reverse
    # chronological order
    checkInRecords = session.query(CheckInRecord).filter(CheckInRecord.stockItem == stockId).all()
    movementRecordsDict = {int(record.timestamp.timestamp()): record for record in checkInRecords}
    checkOutRecords = session.query(CheckOutRecord).filter(CheckOutRecord.stockItem == stockId).all()
    movementRecordsDict.update({int(record.timestamp.timestamp()): record for record in checkOutRecords})

    movementKeys = sorted(movementRecordsDict.keys(), reverse=True)

    movementList = []
    for key in movementKeys:
        record = movementRecordsDict[key]
        recordDict = record.toDict()

        if record.userId != None:
            recordDict["username"] = session.query(User.username).filter(User.id == record.userId).scalar()
        else:
            recordDict["username"] = ""

        if record.jobId != None:
            recordDict["jobName"] = session.query(Job.jobName).filter(Job.id == record.jobId).scalar()
        else:
            recordDict["jobName"] = ""

        if record.binId != None:
            recordDict["binName"] = session.query(Bin.locationName).filter(Bin.id == record.binId).scalar()
        else:
            recordDict["binName"] = ""

        if type(record) == CheckInRecord:
            recordDict["type"] = "Check In"
        elif type(record) == CheckOutRecord:
            recordDict["type"] = "Check Out"
        movementList.append(recordDict)

    if stockItem:
        itemDict = {
            "id": stockItem[0],
            "idNumber": stockItem[1],
            "productId": stockItem[2],
            "addedTimestamp": stockItem[3],
            "expiryDate": expiryDate,
            "canExpire": stockItem[5],
            "quantityRemaining": stockItem[6],
            "quantityUnit": stockItem[7],
            "price": stockItem[8],
            "isCheckedIn": stockItem[9],
            "productTypeName": stockItem[10],
            "productDescriptor1": stockItem[11],
            "productDescriptor2": stockItem[12],
            "productDescriptor3": stockItem[13],
            "isBulk": stockItem[14],
            "bin": binId,
            "movementRecords": movementList
        }

        bins = session.query(Bin) \
            .filter(Bin.locationName != "undefined location") \
            .order_by(Bin.locationName.asc()) \
            .all()
        products = session.query(ProductType) \
            .filter(ProductType.productName != "undefined product type") \
            .order_by(ProductType.productName.asc()) \
            .all()

        placeholderBin = session.query(Bin).filter(Bin.id == -1).scalar()
        placeholderProduct = session.query(ProductType).filter(ProductType.id == -1).scalar()

        data = {
            "stockItemDetails": itemDict,
            "bins": [placeholderBin.toDict()] + [bin.toDict() for bin in bins]
        }

        return make_response(jsonify(data), 200)
    else:
        return make_response("No such item", 404)


@bp.route('/getStockOverview')
@login_required
def getStockOverview():
    stockList = getStockOverviewDataFromRequest()
    return make_response(jsonify(stockList), 200)


def getStockOverviewDataFromRequest():
    overviewType = request.args.get('overviewType', default='totalStock')

    if overviewType == "totalStock":
        stockList = getStockOverviewTotalsDataFromRequest()
    elif overviewType == "availableStock":
        stockList = getAvailableStockTotalsDataFromRequest()
    elif overviewType == "nearExpiry":
        stockList = getStockNearExpiryDataFromRequest()
    elif overviewType == "expired":
        stockList = getExpiredStockDataFromRequest()

    return stockList


def getStockOverviewTotalsDataFromRequest():
    session = getDbSession()
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
    else:
        searchTerm = None

    query = session.query(
        ProductType.id,
        ProductType.productName,
        ProductType.tracksAllItemsOfProductType,
        ProductType.productDescriptor1,
        ProductType.productDescriptor2,
        ProductType.productDescriptor3,
        ProductType.quantityUnit,
        func.sum(StockItem.quantityRemaining)) \
        .join(StockItem, StockItem.productType == ProductType.id) \
        .group_by(StockItem.productType)\
        .order_by(ProductType.productName.asc())

    if searchTerm:
        query = query.where(
            or_(
                ProductType.productName.ilike(searchTerm),
                ProductType.productDescriptor1.ilike(searchTerm),
                ProductType.productDescriptor2.ilike(searchTerm),
                ProductType.productDescriptor3.ilike(searchTerm),
                ProductType.barcode.ilike(searchTerm)
            )
        )

    # ... run it and convert to a dict....
    result = query.all()
    productList = [
        {
            "productId": row[0],
            "productName": row[1],
            "isBulk": row[2],
            "descriptor1": row[3],
            "descriptor2": row[4],
            "descriptor3": row[5],
            "quantityUnit": row[6],
            "stockAmount": formatStockAmount(row[7], 2)
        }
        for row in result
    ]

    return productList


def getAvailableStockTotalsDataFromRequest():
    session = getDbSession()
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
    else:
        searchTerm = "%"

    # get all the other data first
    productTypesQueryResult = session.query(ProductType)\
        .order_by(ProductType.productName.asc())\
        .filter(
            or_(
                ProductType.productName.ilike(searchTerm),
                ProductType.productDescriptor1.ilike(searchTerm),
                ProductType.productDescriptor2.ilike(searchTerm),
                ProductType.productDescriptor3.ilike(searchTerm),
                ProductType.barcode.ilike(searchTerm)
            )
        ) \
        .filter(ProductType.associatedStock != None)\
        .all()

    productList = [
        {
            "productId": row.id,
            "productName": row.productName,
            "isBulk": row.tracksAllItemsOfProductType,
            "descriptor1": row.productDescriptor1,
            "descriptor2": row.productDescriptor2,
            "descriptor3": row.productDescriptor3,
            "quantityUnit": row.quantityUnit,
            "addedTimestamp": row.addedTimestamp,
        }
        for row in productTypesQueryResult
    ]

    # then get total stock and make a nice dict
    # TODO: see if the DB can do this.
    stockQueryResult = session.query(StockItem.productType, func.sum(StockItem.quantityRemaining))\
        .group_by(StockItem.productType)\
        .all()
    stockDict = {row[0]: row[1] for row in stockQueryResult}

    # then get assigned stock
    assignedStockQueryResult = session.query(AssignedStock.productId, func.sum(AssignedStock.quantity))\
        .group_by(AssignedStock.productId)\
        .all()

    # then work out how much stock is unassigned
    for row in assignedStockQueryResult:
        productId = row[0]
        assignedQty = row[1]
        if productId in stockDict:
            stockDict[productId] = stockDict[productId] - assignedQty
        else:
            stockDict[productId] = 0 - assignedQty

    # then update the product list
    for product in productList:
        if product['productId'] in stockDict:
            product['stockAmount'] = formatStockAmount(stockDict[product['productId']], 2)
        else:
            product['stockAmount'] = None

    return productList


def getStockNearExpiryDataFromRequest():
    session = getDbSession()
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
    else:
        searchTerm = "%"

    # get how close to expiry an item of stock needs to be to be counted
    dayCountLimit = request.args.get("dayCountLimit", type=int, default=10)
    maxExpiryDate = datetime.date.today() + datetime.timedelta(days=dayCountLimit)
    currentDate = datetime.date.today()

    query = session.query(
        ProductType.id,
        ProductType.productName,
        ProductType.tracksAllItemsOfProductType,
        ProductType.productDescriptor1,
        ProductType.productDescriptor2,
        ProductType.productDescriptor3,
        ProductType.quantityUnit,
        ProductType.addedTimestamp,
        func.sum(StockItem.quantityRemaining),
        ProductType.barcode) \
        .filter(StockItem.productType == ProductType.id) \
        .filter(ProductType.canExpire)\
        .group_by(StockItem.productType) \
        .order_by(ProductType.productName.asc()) \
        .filter(StockItem.expiryDate <= maxExpiryDate)\
        .filter(StockItem.expiryDate > currentDate)

    if searchTerm:
        query = query.where(
            or_(
                ProductType.productName.ilike(searchTerm),
                ProductType.productDescriptor1.ilike(searchTerm),
                ProductType.productDescriptor2.ilike(searchTerm),
                ProductType.productDescriptor3.ilike(searchTerm),
                ProductType.barcode.ilike(searchTerm)
            )
        )

    # ... run it and convert to a dict....
    result = query.all()
    productList = [
        {
            "productId": row[0],
            "productName": row[1],
            "isBulk": row[2],
            "descriptor1": row[3],
            "descriptor2": row[4],
            "descriptor3": row[5],
            "quantityUnit": row[6],
            "addedTimestamp": row[7],
            "stockAmount": formatStockAmount(row[8],2)
        }
        for row in result
    ]

    return productList


def getExpiredStockDataFromRequest():
    session = getDbSession()
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
    else:
        searchTerm = "%"

    query = session.query(
        ProductType.id,
        ProductType.productName,
        ProductType.tracksAllItemsOfProductType,
        ProductType.productDescriptor1,
        ProductType.productDescriptor2,
        ProductType.productDescriptor3,
        ProductType.quantityUnit,
        ProductType.addedTimestamp,
        func.sum(StockItem.quantityRemaining),
        ProductType.barcode) \
        .filter(StockItem.productType == ProductType.id) \
        .group_by(StockItem.productType) \
        .order_by(ProductType.productName.asc()) \
        .filter(StockItem.expiryDate <= datetime.date.today()) \
        .filter(ProductType.canExpire)

    if searchTerm:
        query = query.where(
            or_(
                ProductType.productName.ilike(searchTerm),
                ProductType.productDescriptor1.ilike(searchTerm),
                ProductType.productDescriptor2.ilike(searchTerm),
                ProductType.productDescriptor3.ilike(searchTerm),
                ProductType.barcode.ilike(searchTerm)
            )
        )

    # ... run it and convert to a dict....
    result = query.all()
    productList = [
        {
            "productId": row[0],
            "productName": row[1],
            "isBulk": row[2],
            "descriptor1": row[3],
            "descriptor2": row[4],
            "descriptor3": row[5],
            "quantityUnit": row[6],
            "addedTimestamp": row[7],
            "stockAmount": formatStockAmount(row[8], 2)
        }
        for row in result
    ]

    return productList


def formatStockAmount(stockAmount, maxDecimalPlaces):
    if int(stockAmount) != stockAmount:
        stockAmount = round(stockAmount, maxDecimalPlaces)

    return f"{stockAmount}"


@bp.route('/editStockItem', methods=("POST",))
@edit_access_required
def updateStock():
    if "id" not in request.form:
        return make_response("stockItem id not provided", 400)

    session = getDbSession()
    stockItem = session.query(StockItem).filter(StockItem.id == request.form.get("id")).scalar()

    if "productType" in request.form:
        stockItem.productType = request.form.get("productType")

    if "expiryDate" in request.form:
        expdate = datetime.datetime.strptime(request.form.get("expiryDate"), "%Y-%m-%d").date()
        stockItem.expiryDate = expdate

    if "canExpire" in request.form and request.form.get("canExpire") == "true":
        stockItem.canExpire = True
    elif "canExpire" in request.form and request.form.get("canExpire") == "false":
        stockItem.canExpire = False

    if "quantityRemaining" in request.form:
        stockItem.quantityRemaining = decimal.Decimal(request.form.get("quantityRemaining", type=float))

    if "price" in request.form:
        stockItem.price = request.form.get("price")

    # if the location of the stock has been changed, create a new check-in record to reflect this
    if "binId" in request.form:
        session.add(CheckInRecord(
            stockItem = stockItem.id,
            productType = stockItem.productType,
            quantityCheckedIn = 0,
            binId = request.form.get("binId")
        ))

    session.commit()

    return make_response("Changes saved", 200)


@bp.route('/deleteStockItem', methods=("POST",))
@create_access_required
def deleteStockItem():
    if "id" not in request.json:
        return make_response("stockItem id not provided", 400)

    session = getDbSession()
    stockItem = session.query(StockItem).filter(StockItem.id == request.json.get("id")).first()
    session.delete(stockItem)
    session.commit()

    return make_response("stock deleted", 200)


@bp.route('/deleteMultipleStockItems', methods=("POST",))
@create_access_required
def deleteMultipleStockItems():
    if "idList" not in request.json:
        return make_response("stockItem id list not provided", 400)

    session = getDbSession()
    placeholderId = session.query(ProductType.id).filter(ProductType.productName == "undefined product type").first()[0]
    stmt = delete(StockItem).where(
        and_(
            StockItem.id.in_(request.json["idList"]),
            StockItem.productType != placeholderId
        )
    )
    session.execute(stmt)
    session.commit()

    return make_response("stock deleted", 200)


@bp.route('/getNewlyAddedStock')
@login_required
def getNewlyAddedStock():
    session = getDbSession()
    # newly added stock list includes product name, stock item id number, quantity added.
    # as always, a text search is available.
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
    else:
        searchTerm = "%"

    query = session.query(
            VerificationRecord.id,
            StockItem.id,
            StockItem.productType,
            ProductType.productName,
            ProductType.quantityUnit,
            CheckInRecord.id,
            CheckInRecord.quantity
        )\
        .filter(VerificationRecord.isVerified == False)\
        .filter(ProductType.productName.ilike(searchTerm))\
        .join(StockItem, StockItem.id == VerificationRecord.associatedStockItemId) \
        .join(ProductType, ProductType.id == StockItem.productType) \
        .join(CheckInRecord, CheckInRecord.id == VerificationRecord.associatedCheckInRecord)\

    if request.args.get("onlyShowUnknownProducts", default="false") == "true":
        placeholderProduct = \
            session.query(ProductType).filter(ProductType.productName == "undefined product type").first()
        query = query.filter(StockItem.productType == placeholderProduct.id)

    unverifiedRecords = query.all()

    results = []
    for row in unverifiedRecords:
        results.append({
            "verificationRecordId": row[0],
            "stockItemId": row[1],
            "productName": row[3],
            "productQuantityUnit": row[4],
            "checkInRecordId": row[5],
            "quantity": row[6]
        })

    return make_response(jsonify(results), 200)


@bp.route('/verifyAllNewStock', methods=("POST",))
@create_access_required
def verifyAllNewStock():
    session = getDbSession()
    session.execute(update(VerificationRecord).where(VerificationRecord.isVerified==False).values(isVerified=True))
    session.commit()

    return make_response("done", 200)


def updateNewStockWithNewProduct(newProductType):
    # if a new stock item has been added, and the barcode is not known
    # it will have been assigned a placeholder product. The actual barcode
    # is recorded in the verification record.
    # If a new product is added with a matching barcode, the new stock will
    # but updated here to match.
    session = getDbSession()

    placeholderProduct = session.query(ProductType)\
        .filter(ProductType.productName == "undefined product type")\
        .one()

    stockItems = session.query(StockItem)\
        .join(VerificationRecord, StockItem.id == VerificationRecord.associatedStockItemId)\
        .filter(VerificationRecord.itemBarcode == newProductType.barcode)\
        .filter(StockItem.productType == placeholderProduct.id)\
        .all()

    for stockItem in stockItems:
        stockItem.productType == newProductType.id
        stockItem.quantityRemaining += newProductType.initialQuantity
        stockItem.price = newProductType.expectedPrice

    checkinRecords = session.query(CheckInRecord)\
        .join(VerificationRecord, CheckInRecord.id == VerificationRecord.associatedCheckInRecord)\
        .filter(VerificationRecord.itemBarcode == newProductType.barcode)\
        .all()

    for checkinRecord in checkinRecords:
        checkinRecord.quantity = newProductType.initialQuantity

    session.commit()


@bp.route('/deleteNewlyAddedStock', methods=("POST",))
@create_access_required
def deleteNewlyAddedStock():
    verificationRecordIdList = request.json

    session = getDbSession()

    verificationRecords = session.query(VerificationRecord)\
        .filter(VerificationRecord.id.in_(verificationRecordIdList))\
        .all()

    # loop through records to be deleted. If a stock item is a bulk product, remove the amount
    # that was checked in
    for i in range(len(verificationRecords)):
        verificationRecord = verificationRecords[i]
        stockItem = session.query(StockItem).filter(StockItem.id == verificationRecord.associatedStockItemId).first()
        checkinRecord = session.query(CheckInRecord)\
            .filter(CheckInRecord.id == verificationRecord.associatedCheckInRecord).first()
        productType = session.query(ProductType).filter(ProductType.id == stockItem.productType).first()
        if productType.tracksAllItemsOfProductType:
            stockItem.quantityRemaining -= checkinRecord.quantity
        if productType.tracksSpecificItems:
            session.delete(stockItem)
        session.delete(checkinRecord)
        session.delete(verificationRecord)

    session.commit()

    return make_response("WIP", 200)


@bp.route("/getStockCsvFile", methods=("GET",))
@login_required
def getStockCsvFile():
    stockData = getStockDataFromRequest()
    headingDictList = [
        {"heading": "Product Name", "dataName": "productName"},
        {"heading": "Quantity Remaining", "dataName": "quantityRemaining"},
        {"heading": "Expires?", "dataName": "canExpire"},
        {"heading": "Expiry Date", "dataName": "expiryDate"},
        {"heading": "Cost at Purchase", "dataName": "price"},
        {"heading": "Barcode", "dataName": "productBarcode"},
        {"heading": "Identifier", "dataName": "idNumber"},
    ]
    csvPath = writeDataToCsvFile(headingsDictList=headingDictList, dataDictList=stockData)

    return send_file(csvPath, as_attachment=True, download_name="StockInfo.csv", mimetype="text/csv")


@bp.route("/getStockOverviewCsvFile", methods=("GET",))
@login_required
def getStockOverviewCsvFile():
    stockOverviewData = getStockOverviewDataFromRequest()
    headingDictList = [
        {"heading": "Product Name", "dataName": "productName"},
        {"heading": "Quantity", "dataName": "stockAmount"},
        {"heading": "Bulk Item?", "dataName": "isBulk"},
        {"heading": "Descriptor 1", "dataName": "descriptor1"},
        {"heading": "Descriptor 2", "dataName": "descriptor2"},
        {"heading": "Descriptor 3", "dataName": "descriptor3"},
    ]
    csvPath = writeDataToCsvFile(headingsDictList=headingDictList, dataDictList=stockOverviewData)

    return send_file(csvPath, as_attachment=True, download_name="StockOverviewInfo.csv", mimetype="text/csv")



