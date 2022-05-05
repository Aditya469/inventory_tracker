from flask import (
    Blueprint, current_app, make_response, render_template, send_file
)
from werkzeug.utils import secure_filename

from .auth import login_required
from .db import getDbSession, Setting
from .qrCodeFunctions import convertDpiAndMmToPx, generateItemIdQrCodeSheets

bp = Blueprint('stockManagement', __name__)


@bp.route('/viewStock')
@login_required
def getStockPage():

    return render_template("viewStock.html")


@bp.route('/getIdStickerSheet/<int:idQty>')
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
