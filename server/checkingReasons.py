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

from flask import (
    Blueprint, render_template, request, make_response, jsonify
)

from auth import login_required, create_access_required
from db import getDbSession
from dbSchema import CheckingReason

bp = Blueprint('checkingReasons', __name__)


@bp.route('/manageCheckingReasons')
@login_required
def manageCheckingReasons():
    return render_template('manageCheckingReasons.html')


@bp.route('/getCheckingReasons')
@login_required
def getCheckingReasons():
    dbSession = getDbSession()
    reasons = dbSession.query(CheckingReason).order_by(CheckingReason.reason.asc()).all()
    reasonList = [reason.toDict() for reason in reasons]
    return make_response(jsonify(reasonList), 200)


@bp.route('/createCheckingReason', methods=("POST",))
@create_access_required
def createCheckingReason():
    if "reason" not in request.json:
        return make_response("reason must be defined", 400)

    dbSession = getDbSession()
    existingReason = dbSession.query(CheckingReason).filter(CheckingReason.reason==request.json.get("reason")).first()
    if existingReason is not None:
        return make_response(f"{request.json.get('reason')} already exists", 400)

    dbSession.add(CheckingReason(reason=request.json.get("reason")))
    dbSession.commit()

    return make_response("New checking reason added", 200)


@bp.route('/deleteCheckingReason', methods=("POST",))
@create_access_required
def deleteCheckingReason():
    dbSession = getDbSession()
    if "reasonId" not in request.json:
        return make_response("reasonId must be provided", 400)
    reasonId = request.json["reasonId"]

    reason = dbSession.query(CheckingReason).filter(CheckingReason.id == reasonId).first()
    dbSession.delete(reason)
    dbSession.commit()

    return make_response("checking reason deleted", 200)



