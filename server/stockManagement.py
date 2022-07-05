from flask import (
    Blueprint, current_app, make_response, render_template, send_file, jsonify, request
)
from werkzeug.utils import secure_filename
import datetime
from auth import login_required
from db import getDbSession, Settings
from qrCodeFunctions import convertDpiAndMmToPx, generateItemIdQrCodeSheets
from dbSchema import StockItem, ProductType, AssignedStock, CheckInRecord, VerificationRecord

from sqlalchemy import select, delete, func, or_, update

bp = Blueprint('stockManagement', __name__)


@bp.route('/viewStock')
@login_required
def getStockPage():

    return render_template("viewStock.html")


@bp.route('/getIdStickerSheet/<int:idQty>')
@login_required
def getItemStickerSheet(idQty):
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
    return send_file(f"{current_app.instance_path}/stickers.png")


@bp.route('/getStock')
@login_required
def getStock():
    session = getDbSession()
    stmt = select(
        StockItem.id,
        StockItem.idNumber,
        ProductType.canExpire,
        StockItem.expiryDate,
        StockItem.quantityRemaining,
        StockItem.price,
        ProductType.productName,
        ProductType.barcode
    ).join(ProductType, StockItem.productType == ProductType.id)

    # selection criteria...
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
        if request.args.get("searchByProductTypeName", type=bool, default=False):
            stmt = stmt.where(ProductType.productName.ilike(searchTerm))
        if request.args.get("searchByIdNumber", type=bool, default=False):
            stmt = stmt.where(StockItem.idNumber.ilike(searchTerm))
        if request.args.get("searchByBarcode", type=bool, default=False):
            stmt = stmt.where(ProductType.barcode.ilike(searchTerm))

    if "canExpire" in request.args:
        if request.args.get("canExpire", type=bool):
            stmt = stmt.where(ProductType.canExpire == True)
        else:
            stmt = stmt.where(ProductType.canExpire == False)

    if "expiryDateStart" in request.args:
        expRangeStartDate = datetime.datetime.strptime(request.args.get("expiryDateStart"), "%Y-%m-%d")
        stmt = stmt.where(StockItem.expiryDate >= expRangeStartDate)

    if "expiryDateEnd" in request.args:
        expRangeEndDate = datetime.datetime.strptime(request.args.get("expiryDateEnd"), "%Y-%m-%d")\
            .replace(hour=11, minute=59)
        stmt = stmt.where(StockItem.expiryDate <= expRangeEndDate)

    if "priceRangeStart" in request.args:
        stmt.where(StockItem.price >= request.args.get("priceRangeStart"))

    if "priceRangeEnd" in request.args:
        stmt.where(StockItem.price <= request.args.get("priceRangeEnd"))

    # ... and ordering
    if "sortBy" in request.args:
        if request.args.get("sortby") == "expiryDate":
            stmt = stmt.order_by(StockItem.expiryDate)
        elif request.args.get("sortBy") == "productName":
            stmt = stmt.order_by(ProductType.productName)
        # etc...
    else:
        stmt = stmt.order_by(StockItem.addedTimestamp)

    results = session.execute(stmt).all()

    stockList = []
    for row in results:
        stockList.append({
            "id": row[0],
            "idNumber": row[1],
            "canExpire": row[2],
            "expiryDate": row[3],
            "quantityRemaining": row[4],
            "price": row[5],
            "productName": row[6],
            "productBarcode": row[7]
        })
    return make_response(jsonify(stockList), 200)


@bp.route('/getStock/<int:stockId>')
@login_required
def getStockItemById(stockId):
    session = getDbSession()
    stockItem = session.query(StockItem).filter(StockItem.id == stockId).scalar()
    if stockItem:
        return make_response(jsonify(stockItem.toDict()), 200)
    else:
        return make_response("No such item", 404)


@bp.route('/getStockOverview')
@login_required
def getStockOverview():
    overviewType = request.args.get('overviewType', default='totalStock')

    if overviewType == "totalStock":
        stockList = getStockOverviewTotals()
    elif overviewType == "availableStock":
        stockList = getAvailableStockTotals()
    elif overviewType == "nearExpiry":
        stockList = getStockNearExpiry()
    elif overviewType == "expired":
        stockList = getExpiredStock()

    return make_response(jsonify(stockList), 200)


def getStockOverviewTotals():
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
            "stockAmount": row[6]
        }
        for row in result
    ]

    return productList


def getAvailableStockTotals():
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
        stockDict[productId] = stockDict[productId] - assignedQty

    # then update the product list
    for product in productList:
        if product['productId'] in stockDict:
            product['stockAmount'] = stockDict[product['productId']]
        else:
            product['stockAmount'] = None

    return productList


def getStockNearExpiry():
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
            "addedTimestamp": row[6],
            "stockAmount": row[7]
        }
        for row in result
    ]

    return productList


def getExpiredStock():
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
            "addedTimestamp": row[6],
            "stockAmount": row[7]
        }
        for row in result
    ]

    return productList


@bp.route('/editStockItem', methods=("POST",))
@login_required
def updateStock():
    if "id" not in request.args:
        return make_response("stockItem id not provided", 400)

    session = getDbSession()
    stockItem = session.query(StockItem).filter(StockItem.id == request.args.get("id")).first()

    if "productType" in request.args:
        stockItem.productType = request.args.get("productType")

    if "expiryDate" in request.args:
        expdate = datetime.datetime.strptime(request.args.get("expiryDate", "%Y-%m-%d")).date()
        stockItem.expiryDate = expdate

    if "canExpire" in request.args and request.args.get("canExpire") == "True":
        stockItem.canExpire = True
    elif "canExpire" in request.args and request.args.get("canExpire") == "False":
        stockItem.canExpire = False

    if "quantityRemaining" in request.args:
        stockItem.quantityRemaining = request.args.get("quantityRemaining", type=float)

    if "price" in request.args:
        stockItem.price = request.args.get("price")

    session.commit()

    return make_response("Changes saved", 200)


@bp.route('/deleteStockItem')
@login_required
def deleteStockItem():
    if "id" not in request.args:
        return make_response("stockItem id not provided", 400)

    session = getDbSession()
    stockItem = session.query(StockItem).filter(StockItem.id == request.args.get("id")).first()
    session.delete(stockItem)
    session.commit()

    return make_response("stock deleted", 200)


@bp.route('/deleteMultipleStockItems')
@login_required
def deleteMultipleStockItems():
    if "idList" not in request.args:
        return make_response("stockItem id list not provided", 400)

    session = getDbSession()
    stmt = delete(StockItem).where(StockItem.id.in_(request.args.get("idList")))
    session.execute(stmt)
    session.commit()

    return make_response("stock deleted", 200)


@bp.route('/getNewlyAddedStock')
@login_required
def getNewlyAddedStock():
    session = getDbSession()
    # TODO: implement this using verificationRecords to pull in bulk stock
    # newly added stock list includes product name, stock item id number, quantity added.
    # as always, a text search is available.
    if "searchTerm" in request.args:
        searchTerm = "%" + request.args.get("searchTerm") + "%"
    else:
        searchTerm = "%"

    unverifiedRecords = session.query(
            VerificationRecord.id,
            StockItem.id,
            StockItem.productType,
            ProductType.productName,
            CheckInRecord.id,
            CheckInRecord.quantityCheckedIn
        )\
        .filter(VerificationRecord.isVerified == False)\
        .filter(ProductType.productName.ilike(searchTerm))\
        .join(StockItem, StockItem.id == VerificationRecord.associatedStockItemId) \
        .join(ProductType, ProductType.id == StockItem.productType) \
        .join(CheckInRecord, CheckInRecord.id == VerificationRecord.associatedCheckInRecord)\
        .all()

    results = []
    for row in unverifiedRecords:
        results.append({
            "verificationRecordId": row[0],
            "stockItemId": row[1],
            "productName": row[3],
            "checkInRecordId": row[4],
            "quantityCheckedIn": row[5]
        })

    return make_response(jsonify(results), 200)


@bp.route('/verifyAllNewStock')
@login_required
def verifyAllNewStock():
    session = getDbSession()
    session.execute(update(VerificationRecord).where(VerificationRecord.isVerified==False).values(isVerified=True))
    session.commit()

    return make_response("done", 200)