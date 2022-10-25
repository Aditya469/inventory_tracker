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
	Blueprint, render_template, session, request, make_response, jsonify,
	current_app, send_file
)
from sqlalchemy import delete, update
from werkzeug.security import check_password_hash, generate_password_hash

from auth import admin_access_required
from db import getDbSession, User
from qrCodeFunctions import generateIdCard

bp = Blueprint('users', __name__)


@bp.route('/manageUsers')
@admin_access_required
def manageUsers():
    return render_template('manageUsers.html')


@bp.route('/getUsers')
@admin_access_required
def getUsers():
    dbSession = getDbSession()
    users = dbSession.query(User).order_by(User.username.asc()).filter(User.username == "admin").all()
    users += dbSession.query(User).order_by(User.username.asc()).filter(User.username != "admin").all()
    userList = [user.toDict() for user in users]
    for i in range(len(userList)):
        userList[i].pop("passwordHash")
    return make_response(jsonify(userList), 200)


@bp.route("/addUser", methods=("POST",))
@admin_access_required
def addUser():
    dbSession = getDbSession()

    if dbSession.query(User).filter(User.username == request.form['newUsername']).count() > 0:
        return make_response("username already exists", 400)

    newUser = User(
        username=request.form['newUsername'],
        passwordHash=generate_password_hash(request.form['newPassword']),
        accessLevel=request.form["accessLevel"],
        emailAddress=request.form["emailAddress"],
        receiveStockNotifications=request.form["receiveStockNotifications"] == "true",
        receiveDbStatusNotifications=request.form["receiveDbStatusNotifications"] == "true"
    )

    if "newUserId" in request.form:
        newUser.idString = request.form["newUserId"]
    else:
        newUser.idString = "user_" + request.form['newUsername']

    dbSession.add(newUser)
    dbSession.commit()

    return make_response("New user added", 200)


@bp.route("/deleteUser", methods=("POST",))
@admin_access_required
def deleteUser():
    dbSession = getDbSession()
    stmt = delete(User).where(User.username == request.form["username"])
    dbSession.execute(stmt)
    dbSession.commit()

    return make_response("User deleted", 200)


@bp.route("/resetPassword", methods=("POST",))
@admin_access_required
def resetPassword():
    dbSession = getDbSession()

    stmt = update(User)\
        .where(User.username == request.form["username"])\
        .values(passwordHash=generate_password_hash("password"))
    dbSession.execute(stmt)
    dbSession.commit()

    return make_response("password reset", 200)


@bp.route("/changePassword", methods=("GET", "POST"))
@admin_access_required
def changePassword():
    if request.method == "GET":
        return render_template("changePassword.html")
    else:
        dbSession = getDbSession()
        currentHashedPassword = dbSession.query(User.passwordHash).filter(User.username == session['username']).scalar()

        if not check_password_hash(currentHashedPassword, request.form["currentPassword"]):
            return make_response("Current password incorrect", 400)

        stmt = update(User)\
            .where(User.username == session['username'])\
            .values(passwordHash=generate_password_hash(request.form["newPassword"]))
        dbSession.execute(stmt)
        dbSession.commit()

        return make_response("password updated", 200)


@bp.route("/updateUser", methods=("POST",))
@admin_access_required
def updateUser():
    dbSession = getDbSession()

    user = dbSession.query(User).filter(User.username == request.json["username"]).first()
    user.accessLevel = request.json["accessLevel"]
    user.receiveStockNotifications = request.json["receiveStockNotifications"]
    user.receiveDbStatusNotifications = request.json["receiveDbStatusNotifications"]
    user.emailAddress = request.json["emailAddress"]


    dbSession.commit()

    return make_response("changes saved", 200)


@bp.route("/getUserIdCard/<username>")
@admin_access_required
def getUserIdCard(username):
    dbSession = getDbSession()
    userIdString = dbSession.query(User.idString).filter(User.username == username).first()[0]
    idCard = generateIdCard(idString=userIdString, label=username, labelFontSize=30, totalWidth=400, totalHeight=200)
    filepath = os.path.join(current_app.instance_path, "user_id.png")
    idCard.save(filepath)

    return send_file(filepath, as_attachment=True, download_name=f"{username} ID card.png")