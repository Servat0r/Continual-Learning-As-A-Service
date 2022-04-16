"""
application package init.
"""
from __future__ import annotations
import logging
import os
from logging.handlers import SMTPHandler
from flask import Flask
from config import *
from .database import db
from .utils import *
from .log import *
from .converters import *
from .mongo_resources import *
from .models import *


_NAME = os.environ.get('SERVER_NAME') or 'SERVER'


def create_app(config_class=MongoConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Put HERE the custom converters!
    app.url_map.converters['user'] = UsernameConverter
    app.url_map.converters['workspace'] = WorkspaceExperimentConverter

    from application.users import bp as users_bp
    from application.auth import bp as auth_bp
    from application.workspaces import bp as workspace_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(workspace_bp)

    if not app.debug and not app.testing:

        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject=f'{_NAME} Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config['STD_FILESAVE_DIR']:
            os.makedirs(app.config['STD_FILESAVE_DIR'], exist_ok=True)

        os.makedirs('files', exist_ok=True)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info(f'{_NAME} startup')

    return app