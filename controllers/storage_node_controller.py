from flask import make_response, jsonify
from handlers import heartbeat_handler, add_storage, verify_storage, authorize_storage, withdraw_handler,\
    get_availability_handler, test_contract_handler, update_connection_handler, storage_shard_done_uploading_handler, \
    random_checks, get_active_contracts
from utils import create_token
from flask import request
import re


@authorize_storage
def heartbeat(authorized_username):
    return heartbeat_handler(authorized_username)


def storage_signup():
    try:
        username = request.json["username"]
        password = request.json["password"]
        wallet_address = request.json["wallet_address"]
        available_space = request.json["available_space"]
        if not re.match("^0x[a-fA-F0-9]{40}$", wallet_address):
            return make_response("Invalid Wallet Address.", 422)
        if username and password and wallet_address and available_space:
            username_already_exists = add_storage(username, password, wallet_address, available_space)
            if username_already_exists:
                return make_response("username already exits", 403)
            else:
                return make_response("success", 201)
        else:
            return make_response("missing parameters", 400)
    except:
        return make_response("missing parameters", 400)


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
            return make_response("missing values", 400)
    except:
        return make_response("missing parameters", 400)


def test():
    random_checks()
    return make_response("success", 200)


@authorize_storage
def withdraw(authorized_username):
    shard_id = request.json["shard_id"]
    if shard_id:
        return withdraw_handler(authorized_username, shard_id)
    else:
        return "shard id is missing from request body"


@authorize_storage
def active_contracts(authorized_username):
    shards = get_active_contracts(authorized_username)
    return make_response(jsonify({'shards': shards}), 200)

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


@authorize_storage
def update_connection(authorized_username):
    
    ip_address = request.json["ip_address"]
    if not isinstance(ip_address, str):
        return make_response("IP address must be a string.", 422)

    if not re.match("^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",ip_address):
        return make_response("Invalid IP address.", 422)
    
    port = request.json["port"]

    if not isinstance(port, str):
        return make_response("Port must be a string.", 422)
    if not re.match("^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$", port):
        return make_response("Invalid port number.", 422)

    return update_connection_handler(authorized_username, ip_address, port)


@authorize_storage
def storage_shard_done_uploading(authorized_username):
    try:
        shard_id = request.json["shard_id"]
        if not shard_id:
            return make_response("missing values.", 400)
        is_success = storage_shard_done_uploading_handler(shard_id)
        if is_success:
            return make_response("success", 200)
        else:
            return make_response("something went wrong", 400)
    except:
        return make_response("missing parameters", 400)
