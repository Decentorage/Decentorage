import socket

from flask.helpers import make_response
from flask.json import jsonify
import app
import json
import jwt
from flask import abort, request
from functools import wraps

import web3_library
from utils import registration_verify_user, registration_add_user
import random
import string


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
        users = app.database["user_nodes"]
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


def check_connection(node, shard_id, shared_authentication_key, shard_size):
    decentorage_port = node["port"]
    ip_address = node["ip_address"]

    port = 0
    req = {'type': 'upload',
           'port': 0,
           'shard_id': shard_id,
           'auth': shared_authentication_key,
           'size': shard_size}

    req = json.dumps(req).encode('utf-8')
    try:
        # start tcp connection with storage node
        client_socket = socket.socket()
        client_socket.connect((ip_address, decentorage_port))
        client_socket.sendall(req)
        port = int(client_socket.recv(1024).decode("utf-8"))
        return port

    except socket.error:
        return port

    client_socket.close()


def verify_user(username, password):
    return registration_verify_user(username, password, "user")


def get_user_state(username):
    try:
        users = app.database["user_nodes"]
        query = {"username": username}
        user = users.find_one(query)
        # State 1: there is a pending contract paid
        if user['pending_contract_paid']:
            return '1'
        # State 2: there is a pending contract but not paid
        elif user['pending_contract']:
            return '2'
        # State 3: no pending contract instance and there is seeds
        elif user['seeds'] > 0:
            return '3'
        # State 4: no pending contract instance and no seeds
        else:
            return '4'
    except:
        return '4'


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

    pay_limit = calculate_price(new_file["download_count"], new_file["duration_in_months"], new_file["file_size"])
    contract = web3_library.create_contract(pay_limit - 1)
    files = app.database["files"]
    users = app.database["user_nodes"]
    if not files or not users:
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
        "contract": contract.address,
        "username": authorized_username,
        "done_uploading": False,
        "paid": False,
        "price": pay_limit
        }
    _id = files.insert_one(query).inserted_id
    segments_list = []
    for segment_no, segment in enumerate(new_file_segments):
        # k and m values should be checked for violations
        total_shards = segment["m"]
        shard_list = []
        for i in range(total_shards):
            shard_id = str(_id) + "$DCNTRG$" + str(segment_no) + "$DCNTRG$" + str(i)
            shard_id = shard_id.encode('utf-8')
            shard_id = app.fernet.encrypt(shard_id).decode('utf-8')
            shard_list.append(
                {
                    "shard_id": shard_id,
                    "shard_node_username": "",
                    "done_uploading": False,
                    "shard_lost": False,
                    "user_node_done": False,
                    "storage_node_done": False
                }
            )
        segments_list.append({
            "k": segment["k"],
            "m": segment["m"],
            "shard_size": segment["shard_size"],
            "shards": shard_list
        })
    query = {"_id": _id}
    new_values = {"$set": {"segments": segments_list}}
    files.update_one(query, new_values)
    query = {'username': authorized_username}
    new_values = {"$set": {"pending_contract": True}, "$inc": {"seeds": -1}}
    users.update_one(query, new_values)
    return True


def get_file_info_handler(authorized_username):
    files = app.database["files"]
    if not files:
        abort(500, "Database error.")

    query = {"username": authorized_username, "done_uploading": False}
    file = files.find_one(query)
    if not file:
        abort(404, "There is no file being uploaded.")

    response = {"file_size":file["file_size"], "segments": file["segments"]}
    return make_response(jsonify(response), 200)


def pay_contract_handler(authorized_username):
    files = app.database["files"]
    if not files:
        abort(500, "Database error.")

    query = {"username": authorized_username, "done_uploading": False, "paid": False}
    file = files.find_one(query)
    if not file:
        abort(404, "There is no unpaid file being uploaded.")

    contract = file["contract"]
    # file_price = file["price"]
    # payment_contract = web3_library.get_contract(contract)
    # payment_contract_balance = web3_library.get_balance(payment_contract)
    # if payment_contract_balance >= file_price:
    #     paid = True
    # else:
    #     paid = False
    # if not paid:
    #     abort(403, "Contract is not paid yet.")
    
    storage_nodes = app.database["storage_nodes"]
    segments = file["segments"]
    
    for i, segment in enumerate(segments):
        total_shards = segment["m"]
        unassigned_shards = total_shards
        shard_size = segment["shard_size"]
        available_space_query = {"available_space": {"$gt": shard_size}}
        retry_count = 100
        while unassigned_shards > 0 and retry_count > 0:
            possible_storage_nodes = storage_nodes.find(available_space_query)
            # possible_storage_nodes_count = storage_nodes.count_documents(available_space_query)
            counting_clone = possible_storage_nodes.clone()
            possible_storage_nodes_count = counting_clone.count()
            if possible_storage_nodes_count == 0:
                abort(500, "No storage nodes available")

            unordered_possible_storage_nodes_indices = list(range(0, possible_storage_nodes_count))
            random.shuffle(unordered_possible_storage_nodes_indices)
            unused_possible_storage_nodes_indices = unordered_possible_storage_nodes_indices[unassigned_shards:]
            size_unused = len(unused_possible_storage_nodes_indices)
            index_unused = 0


            del unordered_possible_storage_nodes_indices[unassigned_shards:]
            for j, index in enumerate(unordered_possible_storage_nodes_indices):
                shard_id = segments[i]["shards"][unassigned_shards-1]["shard_id"]
                shared_authentication_key = ''.join(
                    random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))

                # TODO check if node is alive
                fail = False
                port = check_connection(possible_storage_nodes[index], shard_id, shared_authentication_key, shard_size)
                while not port:
                    if index_unused < size_unused:
                        index = unused_possible_storage_nodes_indices[index_unused]
                        index_unused += 1
                        port = check_connection(possible_storage_nodes[index], shard_id, shared_authentication_key,
                                                shard_size)

                    else:
                        fail = True
                        break
                if fail:
                    continue
                # Shared authentication key for communication
                # TODO send authentication key, inform storage node, and get portclientSocket = socket.socket()

                # Storage node update
                current_storage_node = possible_storage_nodes[index]        # ...
                storage_node_username = current_storage_node["username"]
                ip_address = current_storage_node["ip_address"]

                new_available_space = current_storage_node["available_space"] - shard_size
                new_contracts_entry = {'active_contracts': {"shard_id": shard_id, "contract_address": contract}}
                query = {"username": storage_node_username}
                new_values = {"$set": {"available_space": new_available_space}, "$push": new_contracts_entry}
                storage_nodes.update_one(query, new_values)
                # File update
                segments[i]["shards"][unassigned_shards-1]["ip_address"] = ip_address
                segments[i]["shards"][unassigned_shards-1]["port"] = port
                segments[i]["shards"][unassigned_shards-1]["shard_node_username"] = storage_node_username
                segments[i]["shards"][unassigned_shards-1]["shared_authentication_key"] = shared_authentication_key

                unassigned_shards -= 1
            retry_count -= 1
    # TODO: Mark that this file is paid
    if retry_count != 0:
        query = {"username": authorized_username, "done_uploading": False, "paid": False}
        new_values = {"$set": {"segments": segments, "paid": True}}
        files.update_one(query, new_values)
        user_nodes = app.database["user_nodes"]
        query = {"username": authorized_username}
        new_values = {"$set": {"pending_contract_paid": True}}
        user_nodes.update_one(query, new_values)
        return make_response("Contract payment successful", 200)
    else:
        return make_response("Failed to assign storage nodes", 400)


def calculate_price(download_count, duration_in_months, file_size):
    price_per_storage = file_size / 1099511627776
    price_per_download = price_per_storage * 1.8
    admin_fees = 0.01 * price_per_storage
    price = admin_fees + price_per_storage * duration_in_months + price_per_download * download_count
    if price < 0.25:
        price = 0.25
    return price
# _________________________________ Contract Handlers _________________________________#

def get_contract_handler(authorized_username):
    files = app.database["files"]
    if not files:
        abort(500, "Database error.")
    query = {"username": authorized_username, "paid": False}
    file = files.find_one(query)    
    if not file:
        abort(404, "No unpaid contracts")
    response = {"contract_addresss":file["contract"], "filename": file["filename"], "price": file["price"]}
    return make_response(jsonify(response), 200)

# _________________________________ Download Handlers _________________________________#

def get_port():
    return 50505 # TODO


def start_download_handler(authorized_username, filename):
    files = app.database["files"]
    storage_nodes = app.database["storage_nodes"]
    if not files or not storage_nodes:
        abort(500, "Database error.")
    query = {"username": authorized_username, "filename": filename}
    file = files.find_one(query)
    if not file:
        abort(404, "File not found.")
    if file["download_count"] < 1:
        abort(405, "Your ran out of downloads.")
    if not file["done_uploading"]:
        abort(404, "File is not fully uploaded yet.")
    segments = file["segments"]
    segments_to_return = []
    for seg_no, segment in enumerate(segments):
        shards_to_return = []
        shards = segment["shards"]
        total_shards_needed = segment["k"]
        temporarily_inactive = 0
        shards_acquired = 0
        for sh_no, shard in enumerate(shards):
            if shards_acquired == total_shards_needed:
                break
            if shard["shard_lost"]:
                continue
            # TODO try to open a port on storage_node to receive data
            query = {"username":shard["shard_node_username"]}
            storage_node = storage_nodes.find_one(query)
            ip_address = storage_node["ip_address"]
            decentorage_port = storage_node["port"]
            port = get_port()
            if port == 0:
                temporarily_inactive += 1
                continue

            shard_id = shard["shard_id"]
            shard_id = shard_id.encode('utf-8')
            shard_id = app.fernet.decrypt(shard_id).decode('utf-8')
            shard_id_splitted = shard_id.split("$DCNTRG$")
            segment_no = shard_id_splitted[1]
            shard_no = shard_id_splitted[2]
            if int(segment_no) != seg_no or int(shard_no) != sh_no:
                abort(500, "Database error.")
            shards_to_return.append({"ip_address":ip_address, "port":port, "segment_no": segment_no, "shard_no": shard_no})
            shards_acquired += 1

        if shards_acquired < total_shards_needed:
            missing_shards = total_shards_needed - shards_acquired
            if missing_shards <= temporarily_inactive:
                abort(424, "File is temporary unavailable")
            else:
                abort(500, "File is lost.")
        segments_to_return.append(shards_to_return)
    return make_response(jsonify({'segments': segments_to_return},200))

    # TODO create a function to decrement doownload_count when file download ends

def file_done_uploading_handler():
    pass

def shard_done_uploading_handler(authorized_username, shard_id_original, audits):
    files = app.database["files"]
    if not files:
        abort(500, "Database error.")
    if not audits or not shard_id_original:
        abort(400, "Invalid json object")
    query = {"username": authorized_username, "done_uploading": False}
    file = files.find_one(query)
    if not file:
        abort(404, "File not found.")
 
    shard_id = shard_id_original.encode('utf-8')
    shard_id = app.fernet.decrypt(shard_id).decode('utf-8')
    shard_id_splitted = shard_id.split("$DCNTRG$")
    segment_no = shard_id_splitted[1]
    shard_no = shard_id_splitted[2]
    segments = file["segments"]
    segment = segments[segment_no]
    shards = segment["shards"]
    shard = shards[shard_no]
    if shard["shard_id"] != shard_id_original:
        abort(500, "Database error.")
    done_uploading = shard["storage_node_done"]
    if done_uploading:
        new_values = {
                    "$set": 
                    {
                        "segments."+str(segment_no)+".shards."+str(shard_no)+".done_uploading": True,
                        "segments."+str(segment_no)+".shards."+str(shard_no)+".user_node_done": True,
                        "segments."+str(segment_no)+".shards."+str(shard_no)+".audits": audits,
                    }
                }
    else:
        new_values = {
                    "$set": 
                    {
                        "segments."+str(segment_no)+".shards."+str(shard_no)+".user_node_done": True,
                        "segments."+str(segment_no)+".shards."+str(shard_no)+".audits": audits,
                    }
                }
    files.update_one(query, new_values)

    return make_response("Sucessfull.", 200)