import os

from flask import Flask


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
    '''
    from . import scripts
    app.register_blueprint(scripts.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import overview
    app.register_blueprint(overview.bp)

    from . import users
    app.register_blueprint(users.bp)
    '''
    return app
