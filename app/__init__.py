from flask import Flask


def create_app():
    app = flask(__name__)

    from .routes import main
    app.register_bluerprint(main)


    return app
    