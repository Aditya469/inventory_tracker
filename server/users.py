import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, request, make_response, jsonify
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db, dict_factory
from .auth import login_required

bp = Blueprint('users', __name__)


@login_required
@bp.route('/manageUsers')
def manageUsers():
    if g.user['isAdmin'] and g.user['isAdmin'] == 1:
        return render_template('manageUsers.html')
    else:
        abort(403)


@login_required
@bp.route('/getUsers')
def getUsers():
    db = get_db()
    db.row_factory = dict_factory
    userData = db.execute("SELECT username, isAdmin FROM users ORDER BY username ASC").fetchall()
    return make_response(jsonify(userData), 200)


@login_required
@bp.route("/addUser", methods=("POST",))
def addUser():
    db = get_db()
    print(request.form)
    print(request.form['newUsername'])

    count = db.execute(
        "SELECT COUNT(*) FROM users WHERE username = ?",
        (request.form['newUsername'],)
    ).fetchone()[0]

    if count != 0:
        return make_response("username already exists", 400)

    db.execute(
        "INSERT INTO users(username, password, isAdmin) VALUES (?, ?, ?)",
        (request.form['newUsername'],
         generate_password_hash(request.form['newPassword']),
         request.form["isAdmin"])
    )
    db.commit()

    users = db.execute

    return getUsers()


@login_required
@bp.route("/deleteUser", methods=("POST",))
def deleteUser():
    db = get_db()
    db.execute("DELETE FROM users WHERE username = ?", (request.form["username"],))
    db.commit()

    return getUsers()


@login_required
@bp.route("/resetPassword", methods=("POST",))
def resetPassword():
    db = get_db()
    db.execute(
        "UPDATE users SET password=? WHERE username=?",
        (generate_password_hash("password"), request.form["username"])
    )
    db.commit()

    return make_response("password reset", 200)


@login_required
@bp.route("/changePassword", methods=("GET", "POST"))
def changePassword():
    if request.method == "GET":
        return render_template("changePassword.html")
    else:
        db = get_db()
        currentHashedPassword = db.execute(
            "SELECT password FROM users WHERE username = ?", (session['username'],)
        ).fetchone()[0]

        if not check_password_hash(currentHashedPassword, request.form["currentPassword"]):
            return make_response("Current password incorrect", 400)

        db.execute(
            "UPDATE users SET password=? WHERE username=?",
            (generate_password_hash(request.form["newPassword"]), session['username'])
        )
        db.commit()

        return make_response("password updated", 200)
