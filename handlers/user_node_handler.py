from flask.helpers import make_response
from flask.json import jsonify
import app
import jwt
from flask import abort, request
from functools import wraps
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

    # TODO create empty contract
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
        "contract": "",
        "username": authorized_username,
        "done_uploading": False,
        "paid": False
        }
    _id = files.insert_one(query).inserted_id
    segments_list = []
    for segment_no, segment in enumerate(new_file_segments):
        # k and m values should be checked for violations
        total_shards =  segment["m"]
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
    
    # TODO check if contract is paid
    contract = file["contract"]
    # Assuming payment successful
    paid = True
    if not paid:
        abort(403, "Contract is not paid yet.")
    
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
                # TODO check if node is alive
                fail = False
                if fail:
                    if index_unused < size_unused:
                        unordered_possible_storage_nodes_indices[j], unused_possible_storage_nodes_indices[index_unused], index = \
                            unused_possible_storage_nodes_indices[index_unused], unordered_possible_storage_nodes_indices[j],\
                                 unused_possible_storage_nodes_indices[index_unused]
                    else:
                        continue
                # Shared authentication key for communication
                shared_authentication_key = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
                # TODO send authentication key, inform storage node, and get port
                port = "4500"
                # Storage node update
                shard_id = segments[i]["shards"][unassigned_shards-1]["shard_id"]
                current_storage_node = possible_storage_nodes[index]        # ...
                storage_node_username = current_storage_node["username"]
                ip_address = "12.12.12.12"                   # TODO: current_storage_node["ip_address"]
                new_available_space = current_storage_node["available_space"] - shard_size
                new_contracts_entry = {'active_contracts': {"shard_id": shard_id, "contract_address": contract}}
                query = {"username": storage_node_username}
                new_values = {"$set": {"available_space": new_available_space}, "$push": new_contracts_entry}
                storage_nodes.update_one(query, new_values)
                # File update
                segments[i]["shards"][unassigned_shards-1]["shard_id"] = shard_id
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
        new_values = {"$set": {"pending_contract_paid": True}}
        user_nodes.update_one(query, new_values)
        return make_response("Contract payment successful", 200)
    else:
        return make_response("Failed to assign storage nodes", 400)
