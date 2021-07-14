from flask import make_response, jsonify
from handlers import heartbeat_handler, add_storage, verify_storage, authorize_storage, withdraw_handler, get_availability_handler, test_contract_handler
from utils import create_token
from flask import request



@authorize_storage
def heartbeat(authorized_username):
    return heartbeat_handler(authorized_username)


def storage_signup():
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


def storage_signin():
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


@authorize_storage
def withdraw(authorized_username):
    shard_id = request.json["shard_id"]
    if shard_id:
        return withdraw_handler(authorized_username, shard_id)
    else:
        return "shard id is missing from request body"


@authorize_storage
def get_availability(authorized_username):
    return get_availability_handler(authorized_username)


def test_contract():
    pay_limit = request.args.get("pay_limit")
    contract_address = request.args.get("contract_address")
    storage_address = request.args.get("storage_address")
    if pay_limit and contract_address and storage_address:
        return test_contract_handler(pay_limit, contract_address, storage_address)
    else:
        return make_response("missing parameters", 400)
    return test_contract_handler()
