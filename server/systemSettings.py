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
from datetime import datetime

from flask import (
	Blueprint, render_template, make_response, jsonify, request
)

from auth import admin_access_required, login_required
from db import getDbSession, close_db
from dbSchema import Settings
from emailNotification import sendEmail
from messages import getTestEmailMessage

bp = Blueprint('systemSettings', __name__)


@bp.teardown_request
def afterRequest(self):
	close_db()


@bp.route('/systemSettings')
@admin_access_required
def getSystemSettingsPage():
    return render_template("systemSettings.html")


@bp.route('/loadSettings')
@login_required
def getSystemSettings():
    settings = getDbSession().query(Settings).first()
    return make_response(jsonify(settings.toDict()), 200)


@bp.route('/saveSettings', methods=("POST",))
@admin_access_required
def saveSystemSettings():
    dbSession = getDbSession()
    settings = dbSession.query(Settings).filter(Settings.id == request.json.get("id")).first()

    if "stickerSheetPageHeight_mm" in request.json:
        settings.stickerSheetPageHeight_mm = request.json.get("stickerSheetPageHeight_mm")
    if "stickerSheetPageWidth_mm" in request.json:
        settings.stickerSheetPageWidth_mm = request.json.get("stickerSheetPageWidth_mm")
    if "stickerSheetStickersHeight_mm" in request.json:
        settings.stickerSheetStickersHeight_mm = request.json.get("stickerSheetStickersHeight_mm")
    if "stickerSheetStickersWidth_mm" in request.json:
        settings.stickerSheetStickersWidth_mm = request.json.get("stickerSheetStickersWidth_mm")
    if "stickerSheetDpi" in request.json:
        settings.stickerSheetDpi = request.json.get("stickerSheetDpi")
    if "stickerSheetRows" in request.json:
        settings.stickerSheetRows = request.json.get("stickerSheetRows")
    if "stickerSheetColumns" in request.json:
        settings.stickerSheetColumns = request.json.get("stickerSheetColumns")
    if "stickerPadding_mm" in request.json:
        settings.stickerPadding_mm = request.json.get("stickerPadding_mm")
    if "idCardHeight_mm" in request.json:
        settings.idCardHeight_mm = request.json.get("idCardHeight_mm")
    if "idCardWidth_mm" in request.json:
        settings.idCardWidth_mm = request.json.get("idCardWidth_mm")
    if "idCardDpi" in request.json:
        settings.idCardDpi = request.json.get("idCardDpi")
    if "idCardPadding_mm" in request.json:
        settings.idCardPadding_mm = request.json.get("idCardPadding_mm")
    if "displayIdCardName" in request.json:
        settings.displayIdCardName = request.json.get("displayIdCardName")
    if "displayJobIdCardName" in request.json:
        settings.displayJobIdCardName = request.json.get("displayJobIdCardName")
    if "idCardFontSize_px" in request.json:
        settings.idCardFontSize_px = request.json.get("idCardFontSize_px")
    if "displayBinIdCardName" in request.json:
        settings.displayBinIdCardName = request.json.get("displayBinIdCardName")
    if "emailSmtpServerName" in request.json:
        settings.emailSmtpServerName = request.json.get("emailSmtpServerName")
    if "emailSmtpServerPort" in request.json:
        settings.emailSmtpServerPort = request.json.get("emailSmtpServerPort")
    if "emailAccountName" in request.json:
        settings.emailAccountName = request.json.get("emailAccountName")
    if "emailAccountPassword" in request.json:
        settings.emailAccountPassword = request.json.get("emailAccountPassword")
    if "emailSecurityMethod" in request.json:
        settings.emailSecurityMethod = request.json.get("emailSecurityMethod")
    if "sendEmails" in request.json:
        settings.sendEmails = request.json.get("sendEmails")
    if "dbNumberOfBackups" in request.json:
        settings.dbNumberOfBackups = int(request.json.get("dbNumberOfBackups"))
    if "dbBackupAtTime" in request.json:
        if request.json.get("dbBackupAtTime") != "":
            settings.dbBackupAtTime = datetime.strptime(request.json.get("dbBackupAtTime"), "%H:%M").time()
    if "dbBackupOnMonday" in request.json:
        settings.dbBackupOnMonday = request.json.get("dbBackupOnMonday")
    if "dbBackupOnTuesday" in request.json:
        settings.dbBackupOnTuesday = request.json.get("dbBackupOnTuesday")
    if "dbBackupOnWednesday" in request.json:
        settings.dbBackupOnWednesday = request.json.get("dbBackupOnWednesday")
    if "dbBackupOnThursday" in request.json:
        settings.dbBackupOnThursday = request.json.get("dbBackupOnThursday")
    if "dbBackupOnFriday" in request.json:
        settings.dbBackupOnFriday = request.json.get("dbBackupOnFriday")
    if "dbBackupOnSaturday" in request.json:
        settings.dbBackupOnSaturday = request.json.get("dbBackupOnSaturday")
    if "dbBackupOnSunday" in request.json:
        settings.dbBackupOnSunday = request.json.get("dbBackupOnSunday")
    if "dbMakeBackups" in request.json:
        settings.dbMakeBackups = request.json.get("dbMakeBackups")
    if "stockLevelReorderCheckAtTime" in request.json:
        if request.json.get("stockLevelReorderCheckAtTime") != "":
            settings.stockLevelReorderCheckAtTime = datetime.strptime(request.json.get("stockLevelReorderCheckAtTime"), "%H:%M").time()
    if "stockCheckOnMonday" in request.json:
        settings.stockCheckOnMonday = request.json.get("stockCheckOnMonday")
    if "stockCheckOnTuesday" in request.json:
        settings.stockCheckOnTuesday = request.json.get("stockCheckOnTuesday")
    if "stockCheckOnWednesday" in request.json:
        settings.stockCheckOnWednesday = request.json.get("stockCheckOnWednesday")
    if "stockCheckOnThursday" in request.json:
        settings.stockCheckOnThursday = request.json.get("stockCheckOnThursday")
    if "stockCheckOnFriday" in request.json:
        settings.stockCheckOnFriday = request.json.get("stockCheckOnFriday")
    if "stockCheckOnSaturday" in request.json:
        settings.stockCheckOnSaturday = request.json.get("stockCheckOnSaturday")
    if "stockCheckOnSunday" in request.json:
        settings.stockCheckOnSunday = request.json.get("stockCheckOnSunday")

    dbSession.commit()

    return make_response("Settings updated", 200)


@bp.route("/sendTestEmail", methods=("POST",))
@admin_access_required
def sendTestEmail():
    message = getTestEmailMessage()
    recipient = request.json.get("testEmailRecipientAddress")
    sendEmail(receiverAddressList=[recipient], subject="DigitME2 Inventory Tracker Test Email", emailBody=message)
    return make_response("Test Email Sent", 200)
