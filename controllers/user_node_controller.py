from flask import request, jsonify, make_response
from handlers import add_user, verify_user, authorize_user, get_user_active_contracts, get_user_state,\
    create_file_handler, get_file_info_handler, pay_contract_handler, calculate_price, start_download_handler,\
        get_contract_handler, file_done_uploading_handler, user_shard_done_uploading_handler, verify_transaction_handler
from utils import create_token
import json
import os


# __________________________ Unauthorized requests __________________ #

def user_signup():
    try:
        print(request.json)
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


def user_signin():
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


@authorize_user
def get_state(authorized_username):
    state = get_user_state(authorized_username)
    return make_response(jsonify({'state': state}), 200)


@authorize_user
def get_active_contracts(authorized_username):
    files = get_user_active_contracts(authorized_username)
    return make_response(jsonify(files), 200)


@authorize_user
def create_file(authorized_username):
    if get_user_state(authorized_username) != '3':
        return make_response("No contract requests available.", 403)
    response = create_file_handler(authorized_username, json.loads(request.json))
    if response:
        return make_response("File created successfully", 201)


@authorize_user
def get_price(authorized_username):
    download_count = int(request.args.get("download_count"))
    duration_in_months = int(request.args.get("duration_in_months"))
    file_size = int(request.args.get("file_size"))
    price = calculate_price(download_count, duration_in_months, file_size)
    return make_response(jsonify({'price': price}), 200)


@authorize_user
def get_file_info(authorized_username):
    return get_file_info_handler(authorized_username)


@authorize_user
def pay_contract(authorized_username):
    return pay_contract_handler(authorized_username)


@authorize_user
def get_decentorage_wallet_address(authorized_username):
    return make_response(jsonify({'decentorage_wallet_address': os.environ["ADDRESS"]}), 200)


@authorize_user
def start_download(authorized_username):
    filename = request.json["filename"]
    return start_download_handler(authorized_username, filename)


@authorize_user
def get_contract(authorized_username):
    return get_contract_handler(authorized_username)


@authorize_user
def file_done_uploading(authorized_username):
    response = file_done_uploading_handler(authorized_username)
    if response:
        return make_response("success", 200)
    else:
        return make_response("Database error", 500)


@authorize_user
def user_shard_done_uploading(authorized_username):
    shard_id = request.json["shard_id"]
    audits = request.json["audits"]
    if not audits or not shard_id:
        return make_response("Invalid json object.", 400)
    return user_shard_done_uploading_handler(authorized_username, shard_id, audits)


@authorize_user
def verify_transaction(authorized_username):
    transaction = request.json["transactionHash"]
    return verify_transaction_handler(authorized_username, transaction)
