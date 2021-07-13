from flask import make_response, jsonify
from handlers import heartbeat_handler, add_storage, verify_storage, authorize_storage, withdraw_handler
from utils import create_token
from flask import request


def heartbeat():
    if request.args.get("storage_node"):
        storage_node_number = request.args.get("storage_node")
        return heartbeat_handler(storage_node_number)
    else:
        return "storage node parameter not provided in get request"


def signup():
    try:
        username = request.json["username"]
        password = request.json["password"]
        if username and password:
            username_already_exists = add_storage(username, password)
            if username_already_exists:
                return make_response("username already exits", 403)
            else:
                return make_response("success", 201)
        else:
            return make_response("missing parameters", 400)
    except:
        return make_response("Server error", 500)


def signin():
    try:
        username = request.json["username"]
        password = request.json["password"]
        if username and password:
            is_verified = verify_storage(username, password)
            if is_verified:
                token = create_token(username, password)
                return make_response(jsonify({'token': token}), 200)
            else:
                return make_response("wrong password or username", 403)
        else:
            return make_response("missing parameters", 400)
    except:
        return make_response("Server error", 500)


@authorize_storage
def test(authorized_username):
    print(authorized_username)
    return make_response("success", 201)


def withdraw():
    if request.args.get("storage_node"):
        storage_node_number = request.args.get("storage_node")
        return withdraw_handler(storage_node_number)
    else:
        return "storage node parameter not provided in get request"
