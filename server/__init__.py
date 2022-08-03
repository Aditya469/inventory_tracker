import os

from flask import Flask, render_template


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    app.config.from_pyfile('config.py', silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.initApp(app)

    from . import scripts
    app.register_blueprint(scripts.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import overview
    app.register_blueprint(overview.bp)

    from . import users
    app.register_blueprint(users.bp)

    from . import stockManagement
    app.register_blueprint(stockManagement.bp)

    from . import productManagement
    app.register_blueprint(productManagement.bp)

    from . import jobs
    app.register_blueprint(jobs.bp)

    from . import files
    app.register_blueprint(files.bp)

    from . import bins
    app.register_blueprint(bins.bp)

    return app
