from flask import request, jsonify, make_response
from handlers import add_user, verify_user, authorize_user, get_user_active_contracts, get_user_state,\
    create_file_handler
from utils import create_token
import json
import random


# __________________________ Unauthorized requests __________________ #

def user_signup():
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
    if get_user_state(authorized_username) != '2':
        return make_response("No contract requests available.", 403)
    response = create_file_handler(authorized_username, json.loads(request.json))
    if response:
        return make_response("File created successfully", 201)


@authorize_user
def get_price():
    # TODO: Implement proper price equation.
    download_count = request.json["download_count"]
    duration_in_months = request.json["duration_in_months"]
    file_size = request.json["file_size"]
    price_per_storage = file_size / 1099511627776
    price_per_download = price_per_storage * 1.8
    admin_fees = 0.01 * price_per_storage
    return admin_fees + price_per_storage * duration_in_months + price_per_download * download_count
