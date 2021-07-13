from flask import request, jsonify, make_response
from handlers import add_user, verify_user, authorize, get_user_active_contracts, get_user_state
from utils import create_token


# __________________________ Unauthorized requests __________________ #

def signup():
    try:
        username = request.json["username"]
        password = request.json["password"]
        if username and password:
            username_already_exists = add_user(username, password)
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
            is_verified = verify_user(username, password)
            if is_verified:
                token = create_token(username, password)
                return make_response(jsonify({'token': token}), 200)
            else:
                return make_response("wrong password or username", 403)
        else:
            return make_response("missing parameters", 400)
    except:
        return make_response("Server error", 500)
# __________________________ Authorized requests __________________ #


@authorize
def get_state(authorized_username):
    state = get_user_state(authorized_username)
    return make_response(jsonify({'state': state}), 200)


@authorize
def get_active_contracts(authorized_username):
    files = get_user_active_contracts(authorized_username)
    return make_response(jsonify(files), 200)


@authorize
def test(authorized_username):
    print(authorized_username)
    return make_response("success", 201)
