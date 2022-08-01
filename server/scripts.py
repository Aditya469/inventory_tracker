from flask import (
    Blueprint, render_template, make_response
)
from werkzeug.utils import secure_filename

from .auth import login_required

bp = Blueprint('scripts', __name__)


@bp.route('/scripts/<filename>',)
@login_required
def getScriptFile(filename):
    filename = "scripts/" + secure_filename(filename)
    response = make_response(render_template(filename))
    response.mimetype = 'text/javascript'
    return response


