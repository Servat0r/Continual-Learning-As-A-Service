from flask_httpauth import HTTPTokenAuth
from application.models import check_token, User
from application.errors.utils import make_error

token_auth = HTTPTokenAuth()


@token_auth.verify_token
def verify_token(token):
    return check_token(token)


@token_auth.error_handler
def token_auth_error(status):
    return make_error(status, 'Your authentication token is invalid or expired.')


def check_current_user_ownership(username: str):
    return User.check_ownership(username, token_auth.current_user())