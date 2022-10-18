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

import functools
import os

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, request, make_response, jsonify,
    current_app
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import delete, update

from dbSchema import CheckingReason, Settings
from qrCodeFunctions import convertDpiAndMmToPx, generateIdCard
from db import getDbSession, User
from auth import login_required, userHasAdminAccess, create_access_required

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
    dbSession.add(CheckingReason(reason=request.json.get("reason")))
    dbSession.commit()

    return make_response("New checking reason added", 200)


@bp.route('/deleteCheckingReason', methods=("POST",))
@create_access_required
def deleteCheckingReason():
    dbSession = getDbSession()
    reasonId = request.json.get("reasonId", default=None)
    if reasonId is None:
        return make_response("reasonId must be provided", 400)

    reason = dbSession.query(CheckingReason).filter(CheckingReason.id == reasonId).first()
    dbSession.delete(reason)
    dbSession.commit()

    return make_response("checking reason deleted", 200)



