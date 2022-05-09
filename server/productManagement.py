from flask import (
    Blueprint, render_template
)
from werkzeug.utils import secure_filename

from .auth import login_required

bp = Blueprint('productManagement', __name__)


@bp.route('/productManagement')
@login_required
def getOverview():

    return render_template("overview.html")


