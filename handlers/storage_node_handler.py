import datetime
import math

import flask
import app
import web3_library
import os
#_________________________________ Check database functions _________________________________#
from functools import wraps
from flask import abort, request
import jwt
from utils import registration_verify_user, registration_add_user, Configuration
# _________________________________ Check database functions _________________________________#

def get_storage_nodes_collection():
    if app.database:
        return app.database["storage_nodes"]
    else:
        return False
# _________________________________ Heartbeat handler functions _________________________________#


# How many minutes between each heartbeat
interheartbeat_minutes = Configuration.interheartbeat_minutes
resetting_months = Configuration.resetting_months
decentorage_epoch = Configuration.decentorage_epoch
# 


def get_last_interval_start_datetime(now, years_since_epoch, months_since_epoch):
    months_since_last_interval = (years_since_epoch * 12 + months_since_epoch) % resetting_months
    last_interval_start_year = now.year + math.floor((now.month - months_since_last_interval)/12)
    last_interval_start_month = (now.month - months_since_last_interval) % 12
    if last_interval_start_month == 0:
        last_interval_start_month = 12
    return datetime.datetime(last_interval_start_year,last_interval_start_month,1)


def get_next_interval_start_datetime(now, years_since_epoch, months_since_epoch):
    months_until_next_interval = resetting_months - (years_since_epoch * 12 + months_since_epoch) % resetting_months
    next_interval_start_year = now.year + math.floor((now.month + months_until_next_interval)/12)
    next_interval_start_month = (now.month + months_until_next_interval) % 12
    if next_interval_start_month == 0:
        next_interval_start_month = 12
    return datetime.datetime(next_interval_start_year,next_interval_start_month,1)


def heartbeat_handler(authorized_username):
    storage_nodes  = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, "Database server error.")

    query = {"username": authorized_username}
    storage_node = storage_nodes.find_one(query)
    
    if storage_node:
        now = datetime.datetime.utcnow()
        years_since_epoch = now.year - decentorage_epoch.year
        months_since_epoch = now.month - decentorage_epoch.month
        last_interval_start_datetime = get_last_interval_start_datetime(now, years_since_epoch, months_since_epoch)
        next_interval_start_datetime = get_next_interval_start_datetime(now, years_since_epoch, months_since_epoch)
        new_last_heartbeat = now - datetime.timedelta(minutes=now.minute % interheartbeat_minutes - interheartbeat_minutes,
                                                      seconds=now.second, microseconds=now.microsecond)
        if new_last_heartbeat >= next_interval_start_datetime: # if new heartbeat is in new interval, flag new last heartbeat = -2
            new_last_heartbeat = -2
        
        node_last_heartbeat = storage_node["last_heartbeat"]
        if node_last_heartbeat == -1: # First heartbeat ever
            heartbeats = math.ceil((now - last_interval_start_datetime)/datetime.timedelta(minutes=10))
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
            storage_nodes.update_one(query, new_values)
            return flask.Response(status=200, response="Heartbeat successful.")
        elif node_last_heartbeat == -2 or node_last_heartbeat < last_interval_start_datetime: # First heartbeat in new interval
            heartbeats = 1
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
            storage_nodes.update_one(query, new_values)
            return flask.Response(status=200, response="Heartbeat successful.")
        elif node_last_heartbeat < now: # regular update
            heartbeats = int(storage_node["heartbeats"]) + 1
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
            storage_nodes.update_one(query, new_values)
            return flask.Response(status=200, response="Heartbeat successful.")
        else:
            abort(429, 'Heartbeat Ignored')

# _________________________________ Registrations _________________________________#


def add_storage(username, password, wallet_address, available_space):
    extra_info = {'wallet_address': wallet_address, 'available_space': available_space}
    return registration_add_user(username, password, "storage", extra_info)


def verify_storage(username, password):
    return registration_verify_user(username, password, "storage")


def authorize_storage(f):
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

        if not verify_storage(user['username'], user['password']):
            abort(401, 'No authorized user found.')

        return f(authorized_username=user['username'], *args, **kwargs)

    return decorated

# _________________________________ Withdraw handler functions _________________________________#


def get_percentage(heartbeats, full_heartbeats):
    percentage = heartbeats / full_heartbeats * 100
    return max(min(100, percentage), 0)


def get_availability(storage_node):
    last_heartbeat = storage_node["last_heartbeat"]
    heartbeats = storage_node["heartbeats"]
    if heartbeats == 0:     # New node
        return 0
    now = datetime.datetime.utcnow()
    years_since_epoch = now.year - decentorage_epoch.year
    months_since_epoch = now.month - decentorage_epoch.month
    last_interval_start_datetime = get_last_interval_start_datetime(now,years_since_epoch,months_since_epoch)
    next_interval_start_datetime = get_next_interval_start_datetime(now,years_since_epoch,months_since_epoch)
    full_availability_heartbeats = math.ceil((now - last_interval_start_datetime)/datetime.timedelta(minutes=10))
    if full_availability_heartbeats == 0:
        return 100
    
    heartbeats += 1 # Taking current slot into account
    availability = get_percentage(heartbeats, full_availability_heartbeats)
    if last_heartbeat == -2: # transition state
        # First slot in new interval
        if now - last_interval_start_datetime <= datetime.timedelta(minutes=interheartbeat_minutes):
            return 100
        # Last slot in old interval
        elif next_interval_start_datetime - now <= datetime.timedelta(minutes=interheartbeat_minutes):
            return availability
        # new interval but not first slot
        else:
            return 0
    elif last_heartbeat == -1:  # New node
        return 0
    else:
        return availability


def get_contract_address_from_storage_node(active_contracts, shard_id):
    for active in active_contracts:
        if active["shard_id"] == shard_id:
            return active["contract_address"]


def storage_node_address_with_contract_nodes(contract, storage_address):
    contract_storage_nodes = web3_library.get_storage_nodes(contract)
    for address in contract_storage_nodes:
        if address == storage_address:
            return True
    return False


# TODO: the function not tested yet should be tested later
def withdraw_handler(authorized_username, shard_id):
    storage_nodes  = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, 'Database server error.')
    query = {"username": authorized_username}
    storage_node = storage_nodes.find_one(query)
    # secret_key = os.environ["m"]
    if storage_node:
        availability = get_availability(storage_node)   # Availability in percentage [0, 100].
        # TODO: calculate payment based on availability
        payment = availability
        storage_wallet_address = storage_node["wallet_address"]
        active_contracts = storage_node["active_contracts"]
        contract_address = get_contract_address_from_storage_node(active_contracts, shard_id)
        contract = web3_library.get_contract(contract_address)
        in_contract = storage_node_address_with_contract_nodes(contract, storage_wallet_address)
        # TODO: check for payment date before transfer the money
        if availability > Configuration.minimum_availability and in_contract:
            web3_library.pay_storage_node(contract, storage_wallet_address, payment)
        else:
            return "availability is not good enough"
    else:
        return "Database error."


def get_availability_handler(authorized_username):
    storage_nodes  = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, 'Database server error.')
    query = {"username": authorized_username}
    storage_node = storage_nodes.find_one(query)
    availability = get_availability(storage_node)
    return flask.Response(status=200,response=str(availability))


def test_contract_handler(pay_limit, contract_address, storage_address):
    return "this is test contract handler"
    # create new contract
    # contract = web3_library.create_contract(pay_limit)
    # return flask.Response(status=200, response="contract address: " + str(contract.address) + '\ndecentorage address: ' + str(web3_library.get_decentorage(contract)))

    # get an existing contract
    # contract = web3_library.get_contract(contract_address)
    # return flask.Response(status=200, response="contract address: " + str(contract.address))

    # add new node
    # contract = web3_library.get_contract(contract_address)
    # web3_library.add_node(contract, storage_address)
    # storage_nodes = web3_library.get_storage_nodes(contract)
    # return flask.Response(status=200, response="storage node address: " + str(storage_nodes[0]))

    # delete node contract = web3_library.get_contract(contract_address) before = web3_library.get_storage_nodes(
    # contract) web3_library.delete_node(contract, storage_address) after = web3_library.get_storage_nodes(contract)
    # return flask.Response(status=200, response="storage nodes count before: " + str(len(before)) + '\n' + "storage
    # nodes count after: " + str(len(after)))

    # swap node
    # contract = web3_library.get_contract(contract_address)
    # web3_library.add_node(contract, storage_address)
    # before = web3_library.get_storage_nodes(contract)
    # web3_library.swap_nodes(contract, storage_address, 0)
    # after = web3_library.get_storage_nodes(contract)
    # return flask.Response(status=200, response="storage nodes count before: " + str(
    #     len(before)) + '\n' + "storage nodes count after: " + str(len(after)))

    # pay storage node
    # contract = web3_library.get_contract(contract_address)
    # balance_before = web3_library.get_balance(contract)
    # web3_library.user_pay(contract)
    # balance_after = web3_library.get_balance(contract)
    # return flask.Response(status=200, response="contract balance before = " + str(balance_before) + "\ncontract balance before = " + str(balance_after))

    # user address
    # contract = web3_library.get_contract(contract_address)
    # address = web3_library.get_web_user(contract)
    # return flask.Response(status=200, response="web user address = " + address)

    # decentorage address
    # contract = web3_library.get_contract(contract_address)
    # address = web3_library.get_decentorage(contract)
    # return flask.Response(status=200, response="decentorage address = " + address)

    # pay storage node
    # contract = web3_library.get_contract(contract_address)
    # balance_before = web3_library.get_balance(contract)
    # web3_library.pay_storage_node(contract, storage_address, 100)
    # balance_after = web3_library.get_balance(contract)
    # return flask.Response(status=200, response="contract balance before = " + str(
    #     balance_before) + "\ncontract balance before = " + str(balance_after))

    # terminate contract
    # contract = web3_library.get_contract(contract_address)
    # balance_before = web3_library.get_balance(contract)
    # web3_library.terminate(contract)
    # balance_after = web3_library.get_balance(contract)
    # return flask.Response(status=200, response="contract balance before = " + str(
    #     balance_before) + "\ncontract balance before = " + str(balance_after))


    # _________________________________ Connection handler functions _________________________________#


def update_connection_handler(authorized_username, ip_address, port):
    storage_nodes  = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, 'Database server error.')
    query = {"username": authorized_username}
    new_values = {"$set": {"ip_address": ip_address, "port": port}}
    storage_nodes.update_one(query, new_values)
    return flask.Response(status=200, response="Connection updated.")

