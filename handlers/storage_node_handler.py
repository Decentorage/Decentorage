import datetime
import math
import app
# How many minutes between each heartbeat
intraheartbeat_minutes = 10
# How often does availability reset
resetting_months = 2
decentorage_epoch = datetime.datetime(2020,1,1) # Time at which intervals started


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

def heartbeat_handler(storage_node_number):
    if app.database:
        storage_nodes = app.database["storage_nodes"]
    else:
        return "database error"
    query = {"storage_node_id": int(storage_node_number)}
    storage_node = storage_nodes.find_one(query)
    
    if storage_node:
        now = datetime.datetime.utcnow()
        years_since_epoch = now.year - decentorage_epoch.year
        months_since_epoch = now.month - decentorage_epoch.month
        last_interval_start_datetime = get_last_interval_start_datetime(now, years_since_epoch, months_since_epoch)
        next_interval_start_datetime = get_next_interval_start_datetime(now, years_since_epoch, months_since_epoch)
        new_last_heartbeat = now - datetime.timedelta(minutes=now.minute % intraheartbeat_minutes - intraheartbeat_minutes,
                                                      seconds=now.second, microseconds=now.microsecond)
        print(now - datetime.timedelta(minutes=now.minute % intraheartbeat_minutes - 10 * intraheartbeat_minutes,
                                                      seconds=now.second, microseconds=now.microsecond))
        if new_last_heartbeat >= next_interval_start_datetime: # if new heartbeat is in new interval, flag new last heartbeat = -2
            new_last_heartbeat = -2
        
        node_last_heartbeat = storage_node["last_heartbeat"]
        if node_last_heartbeat == -1: # First heartbeat ever
            heartbeats = math.ceil((now - last_interval_start_datetime)/datetime.timedelta(minutes=10))
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
            storage_nodes.update_one(query, new_values)
            return "Heartbeat successful"
        elif node_last_heartbeat == -2 or node_last_heartbeat < last_interval_start_datetime: # First heartbeat in new interval
            heartbeats = 1
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
            storage_nodes.update_one(query, new_values)
            return "Heartbeat successful"
        elif node_last_heartbeat < now: # regular update
            heartbeats = int(storage_node["heartbeats"]) + 1
            new_values = {"$set": {"last_heartbeat": new_last_heartbeat, "heartbeats": heartbeats}}
            storage_nodes.update_one(query, new_values)
            return "Heartbeat successful"
        else:
            return "Heartbeat ignored"
