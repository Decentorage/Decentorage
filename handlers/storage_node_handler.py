import datetime
import math
import app


#_________________________________ Check database functions _________________________________#
def get_storage_nodes_collection():
    if app.database:
        return app.database["storage_nodes"]
    else:
        return False

#_________________________________ Heartbeat handler functions _________________________________#

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
    storage_nodes  = get_storage_nodes_collection()
    if not storage_nodes:
        return "Database error."
    
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



#_________________________________ Withdraw handler functions _________________________________#


def get_percentage(hearbteats, full_heartbeats):
    percentage = hearbteats / full_heartbeats * 100
    return max(min(100, percentage), 0)


def get_availability(storage_node):
    last_heartbeat = storage_node["last_heartbeat"]
    heartbeats = storage_node["heartbeats"]
    if heartbeats == 0: # New node
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
        if now - last_interval_start_datetime <= datetime.timedelta(minutes=intraheartbeat_minutes): # First slot in new interval
            return 100
        elif next_interval_start_datetime - now <= datetime.timedelta(minutes=intraheartbeat_minutes): # Last slot in old interval
            return availability
        else: # new interval but not first slot
            return 0
    elif last_heartbeat == -1: # New node
        return 0
    else:
        return availability


def withdraw_handler(storage_node_number):
    storage_nodes  = get_storage_nodes_collection()
    if not storage_nodes:
        return "Database error."
    query = {"storage_node_id": int(storage_node_number)}
    storage_node = storage_nodes.find_one(query)
    if storage_node:
        availability = get_availability(storage_node) # Availability in percentage [0, 100].
        # TODO: write withdrawing functions
        if availability > 50:
            
    else:
        return "Database error."
