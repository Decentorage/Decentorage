import datetime
import math
import random
import socket

import flask
import app
import json
import web3_library
from bson.objectid import ObjectId
from functools import wraps
from flask import abort, request, make_response
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
    storage_nodes = get_storage_nodes_collection()
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
        # if new heartbeat is in new interval, flag new last heartbeat = -2
        if new_last_heartbeat >= next_interval_start_datetime:
            new_last_heartbeat = -2
        
        node_last_heartbeat = storage_node["last_heartbeat"]
        if node_last_heartbeat == -1: # First heartbeat ever
            heartbeats = math.ceil((now - last_interval_start_datetime)/datetime.timedelta(minutes=10))
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
        # First heartbeat in new interval
        elif node_last_heartbeat == -2 or node_last_heartbeat < last_interval_start_datetime:
            heartbeats = 1
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
        elif node_last_heartbeat < now: # regular update
            heartbeats = int(storage_node["heartbeats"]) + 1
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
        else:
            abort(429, 'Heartbeat Ignored')
        # TODO: Check random storage node availability, New thread.
        storage_nodes.update_one(query, new_values)
        return flask.Response(status=200, response="Heartbeat successful.")


def random_checks():
    storage_nodes = app.database["storage_nodes"]
    files = app.database["files"]
    if not storage_nodes or not files:
        abort(500, "Database server error.")
    active_storage_nodes = storage_nodes.find({"is_terminated": False})

    counting_clone = active_storage_nodes.clone()
    storage_nodes_count = counting_clone.count()
    if storage_nodes_count != 0:
        random_index = random.randint(0, storage_nodes_count - 1)
        storage_node = active_storage_nodes[random_index]
        check_termination(storage_node, storage_nodes, files)

    uploaded_files = files.find({"done_uploading": True})

    counting_clone = uploaded_files.clone()
    uploaded_files_count = counting_clone.count()
    if uploaded_files_count != 0:
        random_index = random.randint(0, uploaded_files_count - 1)
        print("Print random index", random_index, uploaded_files_count)

    file = uploaded_files[random_index]
    check_regeneration(file, storage_nodes, files)


def send_audit(shard, ip_address, port):
    audits = shard["audits"]
    audits_number = len(audits)
    audit_idx = random.randint(0, audits_number - 1)
    salt = audits[audit_idx]["salt"]
    audit_hash = audits[audit_idx]["hash"]

    req = {"type": "audit", "salt": salt, "shard_id": shard["shard_id"]}
    req = json.dumps(req).encode('utf-8')

    try:
        # start tcp connection with storage node
        client_socket = socket.socket()
        client_socket.settimeout(2)
        client_socket.connect((ip_address, port))
        client_socket.sendall(req)
        result = client_socket.recv(1024).decode("utf-8")

        return result == audit_hash

    except socket.error:
        return False


def check_regeneration(file, storage_nodes, files):
    print(file["filename"])

    i = 0
    # loop on all segments and all shards.
    for segment in file["segments"]:
        number_of_active_shards = 0
        for shard in segment["shards"]:
            # If shard is not lost check termination for the storage node.
            if not shard["shard_lost"]:
                storage_node = storage_nodes.find_one({"username": shard["shard_node_username"]})
                send_audit(shard, storage_node["ip_address"], int(storage_node["port"]))
                is_terminated = check_termination(storage_node, storage_nodes, files)
                # If not terminated increment the number of active shards
                if not is_terminated:
                    number_of_active_shards += 1
        # if the number of active shards is less than minimum data shards needed therefore this segment is lost
        if number_of_active_shards < segment['k']:
            print("segment is lost")

        # if the number of extra shards is less than minimum number needed then regenerate this segment.
        if (number_of_active_shards - segment['k']) <= Configuration.minimum_regeneration_threshold:
            print("Regenerate")
            # TODO: Call regeneration for this segment in this file
            pass
        else:
            print("Segment#", i, "Not regenerated")
        i += 1


def check_termination(storage_node, storage_nodes, files=None):
    storage_availability = get_availability(storage_node)
    print(storage_node["username"], ":", storage_availability, "should be terminated:",
          storage_availability < Configuration.minimum_availability_threshold)
    if storage_availability > Configuration.minimum_availability_threshold:
        return False
    else:
        if not files:
            files = app.database['files']
        terminate_storage_node(storage_node, storage_nodes, files)
        return True


def terminate_storage_node(storage_node, storage_nodes, files):
    contract_addresses = []
    for active_contract in storage_node["active_contracts"]:
        contract_addresses.append(active_contract["contract_address"])
    storage_files = files.find({"contract": {"$in": contract_addresses}})
    for file in storage_files:
        segments = file["segments"]
        for segment_index, segment in enumerate(segments):
            shards = segment["shards"]
            for shard_index, shard in enumerate(shards):
                if shard["shard_node_username"] == storage_node["username"]:
                    shard["shard_lost"] = True
                shards[shard_index] = shard
            segments[segment_index]["shards"] = shards
        query = {"_id": ObjectId(file["_id"])}
        new_values = {"$set": {"segments": segments}}
        files.update_one(query, new_values)

    query = {"username": storage_node["username"]}
    new_values = {"$set": {"is_terminated": True, "available_space": 0, "active_contracts": []}}
    storage_nodes.update_one(query, new_values)


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

        if is_terminated_storage(user["username"]):
            abort(401, 'Storage is terminated.')

        return f(authorized_username=user['username'], *args, **kwargs)

    return decorated


def is_terminated_storage(username):
    """
    Check if storage is terminated.
    *Parameters:*
        - *username(string)*: holds the value of the username.
    *Returns:*
        -*True*: if the user is terminated.
        -*False*: if the user is not terminated.
    """
    try:
        users = app.database["storage_nodes"]
        query = {"username": username, "is_terminated": False}
        user = users.find_one(query)
        # Storage doesn't exit
        if not user:
            return True
        else:
            return False
    except:
        return True

# _________________________________ Withdraw handler functions _________________________________#


def get_percentage(heartbeats, full_heartbeats):
    percentage = heartbeats / full_heartbeats * 100
    return max(min(100, percentage), 0)


def get_active_contracts(authorized_username):
    storage_nodes = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, 'Database server error.')
    query = {"username": authorized_username}
    storage_node = storage_nodes.find_one(query)

    active_shards = []
    active_contracts = storage_node["active_contracts"]
    for contract in active_contracts:
        active_shards.append(contract["shard_id"])
    return active_shards


def get_availability(storage_node):
    last_heartbeat = storage_node["last_heartbeat"]
    heartbeats = storage_node["heartbeats"]
    if last_heartbeat == -1:     # New node
        return 100
    now = datetime.datetime.utcnow()
    years_since_epoch = now.year - decentorage_epoch.year
    months_since_epoch = now.month - decentorage_epoch.month
    last_interval_start_datetime = get_last_interval_start_datetime(now, years_since_epoch, months_since_epoch)
    if (now - last_interval_start_datetime) < datetime.timedelta(days=1):
        return 100
    next_interval_start_datetime = get_next_interval_start_datetime(now, years_since_epoch, months_since_epoch)
    full_availability_heartbeats = math.ceil((now - last_interval_start_datetime)/datetime.timedelta(minutes=10))

    if full_availability_heartbeats == 0:
        return 100
    
    heartbeats += 1     # Taking current slot into account
    availability = get_percentage(heartbeats, full_availability_heartbeats)
    if last_heartbeat == -2:    # transition state
        # First slot in new interval
        if now - last_interval_start_datetime <= datetime.timedelta(minutes=interheartbeat_minutes):
            return 100
        # Last slot in old interval
        elif next_interval_start_datetime - now <= datetime.timedelta(minutes=interheartbeat_minutes):
            return availability
        # new interval but not first slot
        else:
            return 0
    else:
        return availability


def get_contract_from_storage_node(active_contracts, shard_id):
    for index, active in enumerate(active_contracts):
        if active["shard_id"] == shard_id:
            return active, index
    return None


def storage_node_address_with_contract_nodes(contract, storage_address):
    contract_storage_nodes = web3_library.get_storage_nodes(contract)
    for address in contract_storage_nodes:
        if address == storage_address:
            return True
    return False


def withdraw_handler(authorized_username, shard_id):
    storage_nodes = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, 'Database server error.')
    query = {"username": authorized_username, "is_terminated": False}
    storage_node = storage_nodes.find_one(query)
    # secret_key = os.environ["m"]

    if storage_node:
        is_terminated = check_termination(storage_node, storage_nodes)
        if not is_terminated:
            availability = get_availability(storage_node)             # Availability in percentage [0, 100].
            # if availability above full payment threshold, the storage node get full payment
            if availability >= Configuration.full_payment_threshold:
                print("Storage: ", storage_node['username'], "full payment")
                availability = 100
            else:
                print("Storage: ", storage_node['username'], availability, " payment")

            storage_wallet_address = storage_node["wallet_address"]
            active_contracts = storage_node["active_contracts"]
            # get contract element from storage active contracts
            contract, contract_index = get_contract_from_storage_node(active_contracts, shard_id)
            # read contract details.
            contract_address = contract['contract_address']
            payments_count_left = contract['payments_count_left']
            payment = 0
            now = datetime.datetime.utcnow()
            next_payment_date = contract['next_payment_date']
            withdrawn = False
            # Calculate the payment amount the storage node will take
            while (next_payment_date < now) and (payments_count_left > 0):
                print("withdraw--")
                payment += availability * contract['payment_per_interval'] / 100
                payments_count_left -= 1
                next_payment_date = next_payment_date + datetime.timedelta(minutes=5)
                withdrawn = True
            if not withdrawn:
                return make_response("No payment available now.", 404)

            contract = web3_library.get_contract(contract_address)
            in_contract = storage_node_address_with_contract_nodes(contract, storage_wallet_address)
            print(availability, Configuration.minimum_availability_threshold, in_contract)
            if availability > Configuration.minimum_availability_threshold and in_contract:
                web3_library.pay_storage_node(contract, storage_wallet_address, payment)
                active_contracts[contract_index] = {
                    "shard_id": shard_id,
                    "contract_address": contract_address,
                    "next_payment_date": next_payment_date,
                    "payments_count_left": payments_count_left,
                    "payment_per_interval": contract['payment_per_interval']
                }
                query = {"username": authorized_username}
                new_values = {"$set": {"active_contracts": active_contracts}}
                storage_nodes.update_one(query, new_values)
            else:
                return make_response("availability is not good enough", 400)
    else:
        return make_response("Database error.", 500)


def get_availability_handler(authorized_username):
    storage_nodes = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, 'Database server error.')
    query = {"username": authorized_username}
    storage_node = storage_nodes.find_one(query)
    availability = get_availability(storage_node)
    return flask.Response(status=200, response=str(availability))


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

    # delete node
    # contract = web3_library.get_contract(contract_address)
    # before = web3_library.get_storage_nodes(contract)
    # web3_library.delete_node(contract, storage_address)
    # after = web3_library.get_storage_nodes(contract)
    # return flask.Response(status=200, response="storage nodes count before: " + str(len(before)) + '\n' + "storage nodes count after: " + str(len(after)))

    # swap node
    # contract = web3_library.get_contract(contract_address)
    # web3_library.add_node(contract, storage_address)
    # before = web3_library.get_storage_nodes(contract)
    # web3_library.swap_nodes(contract, storage_address, 0)
    # after = web3_library.get_storage_nodes(contract)
    # return flask.Response(status=200, response="storage nodes count before: " + str(
    #     len(before)) + '\n' + "storage nodes count after: " + str(len(after)))

    # user paying
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
    storage_nodes = get_storage_nodes_collection()
    if not storage_nodes:
        abort(500, 'Database server error.')
    query = {"username": authorized_username}
    new_values = {"$set": {"ip_address": ip_address, "port": port}}
    storage_nodes.update_one(query, new_values)
    return flask.Response(status=200, response="Connection updated.")


def storage_shard_done_uploading_handler(shard_id_original):
    files = app.database["files"]
    if not files:
        abort(500, "Database error.")
    shard_id = shard_id_original.encode('utf-8')
    shard_id = app.fernet.decrypt(shard_id).decode('utf-8')
    shard_id_split = shard_id.split("$DCNTRG$")
    document_id = shard_id_split[0]
    segment_no = int(shard_id_split[1])
    shard_no = int(shard_id_split[2])

    query = {"_id": ObjectId(document_id)}

    file = files.find_one(query)
    if not file:
        abort(404, "File not found.")

    segments = file["segments"]
    segment = segments[segment_no]
    shards = segment["shards"]
    shard = shards[shard_no]
    if shard["shard_id"] != shard_id_original:
        abort(500, "Database error.")

    done_uploading = shard["user_node_done"]
    # If user also signaled that the shard is done uploading then the shard is uploaded successfully otherwise only
    # storage signaled that the shard is uploaded
    if done_uploading:
        new_values = {
            "$set":
                {
                    "segments." + str(segment_no) + ".shards." + str(shard_no) + ".done_uploading": True,
                    "segments." + str(segment_no) + ".shards." + str(shard_no) + ".storage_node_done": True
                }
        }
    else:
        new_values = {
            "$set":
                {
                    "segments." + str(segment_no) + ".shards." + str(shard_no) + ".storage_node_done": True
                }
        }
    # Update file document
    files.update_one(query, new_values)
    return True


def get_storage_info_handler(username):
    storage_nodes = get_storage_nodes_collection()

    storage_node = storage_nodes.find_one({"username": username})
    response = []
    availability = get_availability(storage_node)
    for active_contract in storage_node['active_contracts']:
        payment_left = availability * active_contract['payment_per_interval'] * \
                       active_contract['payments_count_left'] / 100
        response.append({
            "shard_id": active_contract['shard_id'],
            "next_payment_date": active_contract['next_payment_date'],
            "payment_left": payment_left,
            "payment_per_interval": active_contract['payment_per_interval']
        })
    return availability, response
