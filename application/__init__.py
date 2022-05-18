"""
application package init.
"""
from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from flask import Flask
from .config import *
from .database import db
from .errors import *
from .utils import *
from .converters import *
from .data_managing import *
from .models import *
from .mongo import *


_NAME = get_env('SERVER_NAME', 'SERVER')

BaseDataManager.create()


def create_app(config_class=MongoConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    executor.init_app(app)

    # Put HERE the custom converters!
    app.url_map.converters['user'] = UsernameConverter
    app.url_map.converters['workspace'] = WorkspaceExperimentConverter
    app.url_map.converters['resource'] = WorkspaceExperimentConverter
    app.url_map.converters['experiment'] = WorkspaceExperimentConverter

    from application.routes import blueprints

    for bp in blueprints:
        app.register_blueprint(bp)

    if not app.debug and not app.testing:

        os.makedirs('logs', exist_ok=True)

        file_handler = RotatingFileHandler(os.path.join('logs', 'auth_server.log'), maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)

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

        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info(f"{_NAME} startup")
        app.logger.info(f"Using '{get_device()}' device for training and evaluation")

    return app