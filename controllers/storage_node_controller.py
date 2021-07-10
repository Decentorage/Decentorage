from flask import request
from handlers import heartbeat_handler


def heartbeat(database):
    if request.args.get("storage_node"):
        storage_node_number = request.args.get("storage_node")
        return heartbeat_handler(storage_node_number, database)
    else:
        return "storage node parameter not provided in get request"
