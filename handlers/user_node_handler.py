import bcrypt
import app
import jwt
from flask import abort, request
from functools import wraps
import datetime
from datetime import timedelta


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
        if user:
            if user['active_contracts']:
                return user['active_contracts']
            else:
                return []
        return False
    except:
        return False


def add_user(username, password):
    """
    Add user to the system
    When a user sign up for the first time this function hash the password given, then add user to database
    *Parameters:*
        - *username(string)*: holds the value of the username.
        - *password(string)*: holds the value of the password.
    *Returns:*
       - boolean value one indicates if the username already exists.
    """
    try:
        users = app.database["user"]
        query = {"username": username}
        user = users.find_one(query)
        if user:
            return True
        # Hash a password for the first time, with a randomly-generated salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users.insert_one({"username": username, "password": hashed_password.decode('utf-8'), 'requests': [],
                          'active_contracts': []})
        return False
    except:
        return True


def verify_user(username, password):
    """
    verify user. password is hashed.
    investigate whether the user is on the system or not
    *Parameters:*
        - *username(string)*: holds the value of the username.
        - *password(string)*: holds the value of the password.
    *Returns:*
        -*True*: if the user is on the system.
        -*False*: if the user is not on the system.
    """
    try:
        users = app.database["user"]
        query = {"username": username}
        user = users.find_one(query)
        # User doesn't exit
        if not user:
            return False
        else:
            # Check that an un-hashed password matches one that has previously been hashed
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return True
        return False
    except:
        return False


def create_token(username, password):
    """
    Generate token.
    Encode the payload (date of expiration, username) with the secret key.
    *Parameters:*
        -*username(string)*: holds the value of the username.
        -*password(string)*: holds the value of the password.
    *Returns:*
        -*Token*:the token created.
    """
    exp = datetime.datetime.utcnow() + timedelta(days=30)
    payload = {
        'username': username,
        'password': password,
        'exp': exp
    }
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token


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
