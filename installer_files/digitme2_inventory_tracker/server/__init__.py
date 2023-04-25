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
import logging
import os
import sys

from flask import Flask

import db
import paths


def create_app():
    logging.basicConfig(filename=paths.logPath, level=logging.DEBUG, format='%(asctime)s %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    # create and configure the app
    app = Flask(__name__, instance_path=paths.instancePath)
    app.config.from_mapping(
        SECRET_KEY='change_this_key'
    )

    app.config.from_pyfile('config.py', silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    import db
    db.initApp(app)

    import scripts
    app.register_blueprint(scripts.bp)

    import auth
    app.register_blueprint(auth.bp)

    import overview
    app.register_blueprint(overview.bp)

    import users
    app.register_blueprint(users.bp)

    import stockManagement
    app.register_blueprint(stockManagement.bp)

    import productManagement
    app.register_blueprint(productManagement.bp)

    import jobs
    app.register_blueprint(jobs.bp)

    import files
    app.register_blueprint(files.bp)

    import bins
    app.register_blueprint(bins.bp)

    import checkingReasons
    app.register_blueprint(checkingReasons.bp)

    import api
    app.register_blueprint(api.bp)

    import systemSettings
    app.register_blueprint(systemSettings.bp)

    import backup
    app.register_blueprint(backup.bp)

    logging.info("created app")

    return app


app = create_app()


@app.teardown_request
def afterRequest(response):
    db.releaseDbLock()


if __name__ == "__main__":
    app.run()
