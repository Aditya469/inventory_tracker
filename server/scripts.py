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
	Blueprint, render_template, make_response
)
from werkzeug.utils import secure_filename

from auth import login_required
from db import close_db

bp = Blueprint('scripts', __name__)

@bp.teardown_request
def afterRequest(self):
	close_db()

@bp.route('/scripts/<filename>',)
@login_required
def getScriptFile(filename):
    filename = "scripts/" + secure_filename(filename)
    response = make_response(render_template(filename))
    response.mimetype = 'text/javascript'
    return response


