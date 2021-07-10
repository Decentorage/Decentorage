import datetime
import app
# How many minutes between each heartbeat
blocking_minutes = 10
heartbeat_gap = datetime.timedelta(minutes=blocking_minutes)


def heartbeat_handler(storage_node_number):
    now = datetime.datetime.utcnow()
    if app.database:
        storage_nodes = app.database["storage_nodes"]
    else:
        return "database error"
    query = {"storage_node_id": int(storage_node_number)}
    storage_node = storage_nodes.find_one(query)
    if storage_node:
        if storage_node["last_heartbeat"] < now or storage_node["last_heartbeat"] == 0:
            new_last_heartbeat = now - datetime.timedelta(minutes=now.minute % blocking_minutes,
                                                          seconds=now.second,
                                                          microseconds=now.microsecond) + heartbeat_gap
            heartbeats = int(storage_node["heartbeats"]) + 1
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
            storage_nodes.update_one(query, new_values)
            return "Heartbeat successful"
        else:
            return "Heartbeat ignored"
