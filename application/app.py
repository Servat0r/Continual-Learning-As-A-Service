from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from flask import Flask

from .config import *
from .database import db
from .utils import *
from .converters import *

_NAME = get_env('SERVER_NAME', 'SERVER')


def create_app(config_class=MongoConfig, use_logger=True):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    executor.init_app(app)
    linker.init_app(app)

    # Put HERE the custom converters!
    app.url_map.converters['user'] = UsernameConverter
    app.url_map.converters['workspace'] = WorkspaceExperimentConverter
    app.url_map.converters['resource'] = WorkspaceExperimentConverter
    app.url_map.converters['experiment'] = WorkspaceExperimentConverter
    app.url_map.converters['rpath'] = AllowedPathConverter

    from application.routes import blueprints

    for bp in blueprints:
        app.register_blueprint(bp)

    if not app.debug and not app.testing:

        os.makedirs('logs', exist_ok=True)
        os.makedirs(app.config["DATASET_ROOT_DIR"], exist_ok=True)

        if use_logger:
            file_handler = RotatingFileHandler(os.path.join('logs', 'auth_server.log'), maxBytes=10240,
                                               backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
        else:
            file_handler = None

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

        tp = [(attr, getattr(MongoConfig, attr)) for attr in dir(MongoConfig) if not attr.startswith('__')]
        conf_attr_str = ''
        for item in tp:
            name, value = item
            conf_attr_str += f"\n\t{name} = {value}"

        if use_logger:
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info("Changes made!")
            app.logger.info(f"{_NAME} startup")
            app.logger.info(f"Using '{get_device()}' device for training and evaluation")
            app.logger.info(f"Using '{app.config.get('EXECUTOR_TYPE')}' pool executor for experiments")
            app.logger.info(f"Using '{app.config.get('DATASET_ROOT_DIR')}' directory for common datasets")
            app.logger.info(f"Using class '{config_class.__name__}' as configuration class")
            app.logger.info(f"Configuration attributes: {conf_attr_str}")

    return app


__all__ = [
    'create_app',
]