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

