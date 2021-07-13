from flask import request
from handlers import heartbeat_handler, withdraw_handler


def heartbeat():
    if request.args.get("storage_node"):
        storage_node_number = request.args.get("storage_node")
        return heartbeat_handler(storage_node_number)
    else:
        return "storage node parameter not provided in get request"


def withdraw():
    if request.args.get("storage_node"):
        storage_node_number = request.args.get("storage_node")
        return withdraw_handler(storage_node_number)
    else:
        return "storage node parameter not provided in get request"
