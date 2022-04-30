from flask import Blueprint

from application.routes.auth import token_auth
from application.routes.resources import *


_DFL_MODEL_NAME_ = "Model"


models_bp = Blueprint('models', __name__,
                      url_prefix='/users/<user:username>/workspaces/<workspace:wname>/models')


@models_bp.post('/')
@models_bp.post('')
@token_auth.login_required
def create_model(username, wname):
    return add_new_resource(username, wname, _DFL_MODEL_NAME_)


@models_bp.get('/<name>/')
@models_bp.get('/<name>')
@token_auth.login_required
def build_model(username, wname, name):
    return build_resource(username, wname, _DFL_MODEL_NAME_, name)


@models_bp.delete('/<name>/')
@models_bp.delete('/<name>')
@token_auth.login_required
def delete_model(username, wname, name):
    return delete_resource(username, wname, _DFL_MODEL_NAME_, name)