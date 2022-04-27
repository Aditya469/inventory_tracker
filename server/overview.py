from flask import (
    Blueprint, render_template
)
from werkzeug.utils import secure_filename

from .auth import login_required

bp = Blueprint('overview', __name__)


@bp.route('/overview')
@bp.route('/')
@login_required
def getOverview():

    return render_template("overview.html")


