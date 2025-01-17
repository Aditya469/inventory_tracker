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

import os

from flask import (
    Blueprint, render_template, request, make_response, jsonify,
    current_app, send_file
)
from werkzeug.exceptions import abort

from auth import login_required, create_access_required
from db import getDbSession, close_db
from dbSchema import Bin, Settings
from qrCodeFunctions import convertDpiAndMmToPx, generateIdCard

bp = Blueprint('bins', __name__)


@bp.teardown_request
def afterRequest(self):
	close_db()


@bp.route('/manageBins')
@login_required
def manageBins():
    return render_template('manageBins.html')


@bp.route('/getBins')
@login_required
def getBins():
    dbSession = getDbSession()
    bins = dbSession.query(Bin).filter(Bin.locationName != "undefined location").order_by(Bin.locationName).all()
    list = [bin.toDict() for bin in bins]
    return make_response(jsonify(list), 200)


@bp.route('/createBin', methods=("POST",))
@create_access_required
def createBin():
    if "locationName" not in request.json:
        return make_response("locationName must be defined", 400)

    dbSession = getDbSession()
    if dbSession.query(Bin).filter(Bin.locationName == request.json['locationName']).first() is not None:
        return make_response("A bin with that name already exists", 400)
    newBin = Bin()
    dbSession.add(newBin)
    dbSession.flush()
    newBin.idString = f"bin_{newBin.id}"
    newBin.locationName = request.json["locationName"].strip()

    dbSession.commit()

    return make_response("New bin added", 200)


@bp.route('/deleteBin/<binId>', methods=("POST",))
@create_access_required
def deleteBin(binId):
    dbSession = getDbSession()
    bin = dbSession.query(Bin).filter(Bin.id == binId).first()
    if not bin:
        return make_response("no such bin id", 400)

    dbSession.delete(bin)
    dbSession.commit()

    return make_response("bin deleted", 200)


@bp.route("/getBinIdCard")
@login_required
def getBinIdCard():
    binId = request.args.get("binId", default=None)
    if binId is None:
        return make_response("binId must be provided", 400)

    dbSession = getDbSession()
    bin = dbSession.query(Bin).filter(Bin.id == binId).first()

    if bin is None:
        return make_response("invalid binId", 400)

    idCard = generateIdCard(idString=bin.idString, label=bin.locationName, labelFontSize=30, totalWidth=600, totalHeight=200)
    qrCodePath = os.path.join(current_app.instance_path, "bin_qr_code.png")
    idCard.save(qrCodePath)

    return send_file(qrCodePath, as_attachment=True, download_name=f"{bin.locationName} ID card.png")
