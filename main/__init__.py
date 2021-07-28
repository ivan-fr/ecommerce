import os

from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_pyfile('./config.py')

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
