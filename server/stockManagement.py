from flask import (
    Blueprint, current_app, make_response, render_template, send_file, jsonify, request
)
from werkzeug.utils import secure_filename
import datetime
from auth import login_required
from db import getDbSession, Setting
from qrCodeFunctions import convertDpiAndMmToPx, generateItemIdQrCodeSheets
from dbSchema import StockItem

from sqlalchemy import select, delete

bp = Blueprint('stockManagement', __name__)


@bp.route('/viewStock')
@login_required
def getStockPage():

    return render_template("viewStock.html")


@bp.route('/getIdStickerSheet/<int:idQty>')
@login_required
def getItemStickerSheet(idQty):
    dbSession = getDbSession()
    pageWidth_mm = dbSession.query(Setting.value).filter(Setting.name == "stickerSheetPageWidth_mm").first()[0]
    pageHeight_mm = dbSession.query(Setting.value).filter(Setting.name == "stickerSheetPageHeight_mm").first()[0]
    stickerAreaWidth_mm = dbSession.query(Setting.value).filter(Setting.name == "stickerSheetStickersWidth_mm").first()[0]
    stickerAreaHeight_mm = dbSession.query(Setting.value).filter(Setting.name == "stickerSheetStickersHeight_mm").first()[0]
    stickerPadding_mm = dbSession.query(Setting.value).filter(Setting.name == "stickerPadding_mm").first()[0]
    stickerSheetDpi = dbSession.query(Setting.value).filter(Setting.name == "stickerSheetDpi").first()[0]

    pageWidthPx = convertDpiAndMmToPx(length_mm=int(pageWidth_mm), DPI=int(stickerSheetDpi))
    pageHeightPx = convertDpiAndMmToPx(length_mm=int(pageHeight_mm), DPI=int(stickerSheetDpi))
    stickerAreaWidthPx = convertDpiAndMmToPx(length_mm=int(stickerAreaWidth_mm), DPI=int(stickerSheetDpi))
    stickerAreaHeightPx = convertDpiAndMmToPx(length_mm=int(stickerAreaHeight_mm), DPI=int(stickerSheetDpi))
    stickerPaddingPx = convertDpiAndMmToPx(length_mm=int(stickerPadding_mm), DPI=int(stickerSheetDpi))


    stickerRows = int(dbSession.query(Setting.value).filter(Setting.name == "stickerSheetRows").first()[0])
    stickerColumns = int(dbSession.query(Setting.value).filter(Setting.name == "stickerSheetColumns").first()[0])

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
    stmt = select(StockItem)

    results = session.execute(stmt).scalars().all()

    # add selection criteria here

    return make_response(jsonify([row.toDict() for row in results]), 200)


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
    # stockItemsList = session.query(StockItem)\
    #     .filter(StockItem.isVerified == False)\
    #     .order(StockItem.productType.asc())\
    #     .scalars()\
    #     .all()
    #
    # stockList = [stockItem.toDict() for stockItem in stockItemsList]
    # return make_response(jsonify(stockList), 200)


@bp.route('/verifyAllNewStock')