import app
import jwt
from flask import abort, request
from functools import wraps
from utils import registration_verify_user, registration_add_user


def get_user_active_contracts(username):
    """
        get user active contracts
        *Parameters:*
            - *username(string)*: holds the value of the username.
        *Returns:*
           - List of active contracts of a specific user.
    """
    try:
        users = app.database["user"]
        query = {"username": username}
        user = users.find_one(query)
        if user['active_contracts']:
            return user['active_contracts']
        else:
            return []
    except:
        return []


def add_user(username, password):
    return registration_add_user(username, password, "user")


def verify_user(username, password):
    return registration_verify_user(username, password, "user")


def get_user_state(username):
    try:
        users = app.database["user"]
        query = {"username": username}
        user = users.find_one(query)
        # State 1: there is a pending contract instance
        if user['request']:
            return '1'
        # State 2: no pending contract instance and there is money to initiate request
        elif user['available_request_count'] > 0:
            return '2'
        # State 3: no pending contract instance and no money to initiate request
        else:
            return '3'
    except:
        return '3'


def authorize(f):
    """
    Token verification Decorator. This decorator validate the token passed in the header with the endpoint.
    *Returns:*
        -*Error Response,401*: if the token is not given in the header, expired or invalid.
                                Or the user is not on the system.
        -*Username*:if the token is valid it allows the access and return the username of the user.
    """

    @wraps(f)  # pragma:no cover
    def decorated(*args, **kwargs):
        token = None
        user = None
        if 'TOKEN' in request.headers:
            token = request.headers['TOKEN']

        if not token:
            abort(401, 'Token is missing.')

        try:
            user = jwt.decode(token, app.secret_key, algorithms=['HS256'])

        except jwt.ExpiredSignatureError:
            abort(401, 'Signature expired. Please log in again.')

        except jwt.InvalidTokenError:
            abort(401, 'Invalid token. Please log in again.')

        if not verify_user(user['username'], user['password']):
            abort(401, 'No authorized user found.')

        return f(authorized_username=user['username'], *args, **kwargs)

    return decorated
