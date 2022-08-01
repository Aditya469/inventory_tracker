import decimal
import functools
import logging
import os
from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, request, make_response, jsonify, current_app,
	send_file
)
from sqlalchemy import select, func
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename, send_from_directory

from db import getDbSession
from dbSchema import Job, Settings, AssignedStock, CheckInRecord, CheckOutRecord, ProductType
import json
from auth import login_required
from qrCodeFunctions import convertDpiAndMmToPx, generateIdCard
bp = Blueprint('files', __name__)

@bp.route("/getFile/<filename>")
@login_required
def getFile(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(current_app.instance_path, filename)
    return send_file(filepath)

