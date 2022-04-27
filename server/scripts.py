from flask import (
    Blueprint, render_template
)
from werkzeug.utils import secure_filename

from .auth import login_required

bp = Blueprint('scripts', __name__)


@bp.route('/scripts/<filename>',)
@login_required
def getFile(filename):
    filename = secure_filename("templates/scripts/" + filename)
    return render_template(filename)


