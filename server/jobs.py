import functools

from flask import (
	Blueprint, flash, g, redirect, render_template, request, session, url_for, request, make_response, jsonify
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from db import getDbSession, User
from auth import login_required

bp = Blueprint('jobs', __name__)


@bp.route("/createJob", method=("POST",))
@login_required
def createJob():
	return make_response("", 200)


@bp.route("/getJobs")
@login_required
def getJobs():
	return make_response(jsonify([]),  200)
