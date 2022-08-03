'''
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
'''

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
