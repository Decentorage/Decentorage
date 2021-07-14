import app
import jwt
from flask import abort, request
from functools import wraps
from utils import registration_verify_user, registration_add_user


# _________________________________ PLACEHOLDER _________________________________#
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


def authorize_user(f):
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


# _________________________________ Upload requests handler _________________________________#


def create_file_handler(authorized_username, new_file):
    if not all(parameter in new_file for parameter in ("segments", "segments_count", "download_count",
                                                       "file_size", "filename", "duration_in_months")):
        abort(400, "Invalid json object")
    new_file_segments = new_file["segments"]
    for segment in new_file_segments:
        if not all(parameter in segment for parameter in ("k", "m", "shard_size")):
            abort(400, "Invalid json object")
    filename = new_file['filename']

    # TODO create empty contract
    files = app.database["files"]
    users = app.database["user"]
    if not files:
        abort(500, "Database error.")
    query = {
        'username': authorized_username,
        'filename': filename
    }
    file = files.find_one(query)
    if file:
        abort(409, "Duplicate Files.")
    query = {
        "filename": new_file["filename"],
        "segments_count": new_file["segments_count"],
        "file_size": new_file["file_size"],
        "download_count": new_file["download_count"],
        "duration_in_months": new_file["duration_in_months"],
        "contract": "",
        "username": authorized_username,
        "done_uploading": False
        }
    _id = files.insert_one(query).inserted_id
    segments_list = []
    for segment_no, segment in enumerate(new_file_segments):
        # k and m values should be checked for violations
        total_shards = segment["k"] + segment["m"]
        shard_list = []
        for i in range(total_shards):
            shard_id = str(_id) + "$DCNTRG$" + str(segment_no) + "$DCNTRG$" + str(i)
            shard_id = shard_id.encode('utf-8')
            shard_id = app.fernet.encrypt(shard_id).decode('utf-8')
            shard_list.append(
                {
                    "shard_id": shard_id,
                    "shard_node_username": "",
                    "done_uploading": False
                }
            )
        segments_list.append({
            "k": segment["k"],
            "m": segment["m"],
            "shard_size": segment["shard_size"],
            "shards": shard_list
        })
    query = {"_id": _id}
    newvalues = {"$set": {"segments": segments_list}}
    files.update_one(query, newvalues)
    return True
    

    
    

    

