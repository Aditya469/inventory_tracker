import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, request, make_response, jsonify
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import delete, update
from .db import getDbSession, User
from .auth import login_required

bp = Blueprint('users', __name__)


@login_required
@bp.route('/manageUsers')
def manageUsers():
    if g.user.isAdmin:
        return render_template('manageUsers.html')
    else:
        abort(403)


@login_required
@bp.route('/getUsers')
def getUsers():
    dbSession = getDbSession()
    userData = dbSession.query(User.username, User.isAdmin).order_by(User.username.asc()).all()
    list = [user._asdict() for user in userData]
    return make_response(jsonify(list), 200)


@login_required
@bp.route("/addUser", methods=("POST",))
def addUser():
    dbSession = getDbSession()

    if dbSession.query(User).filter(User.username == request.form['newUsername']).count() > 0:
        return make_response("username already exists", 400)

    newUser = User(
        username=request.form['newUsername'],
        passwordHash=generate_password_hash(request.form['newPassword']),
        isAdmin=request.form["isAdmin"] == "true"
    )

    dbSession.add(newUser)
    dbSession.commit()

    return make_response("New user added", 200)


@login_required
@bp.route("/deleteUser", methods=("POST",))
def deleteUser():
    dbSession = getDbSession()
    stmt = delete(User).where(User.username == request.form["username"])
    dbSession.execute(stmt)
    dbSession.commit()

    return make_response("User deleted", 200)


@login_required
@bp.route("/resetPassword", methods=("POST",))
def resetPassword():
    dbSession = getDbSession()

    stmt = update(User)\
        .where(User.username == request.form["username"])\
        .values(passwordHash=generate_password_hash("password"))
    dbSession.execute(stmt)
    dbSession.commit()

    return make_response("password reset", 200)


@login_required
@bp.route("/changePassword", methods=("GET", "POST"))
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
