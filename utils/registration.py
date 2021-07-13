import bcrypt
import app
import datetime
from datetime import timedelta
import jwt


def registration_add_user(username, password, user_type):
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
        if user_type == "user":
            users = app.database["user"]
        else:
            users = app.database["storage_nodes"]
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


def registration_verify_user(username, password, user_type):
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
        if user_type == "user":
            users = app.database["user"]
        else:
            users = app.database["storage_nodes"]
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
