from controllers import heartbeat, withdraw, storage_signin, storage_signup, get_availability, test_contract, \
    update_connection, storage_shard_done_uploading, test, active_contracts
import app

storage_url_prefix = '/storage'


def add_storage_urls():
    # Get Methods
    app.app.add_url_rule(storage_url_prefix + "/heartbeat", view_func=heartbeat, methods=["GET"])
    app.app.add_url_rule(storage_url_prefix + "/availability", view_func=get_availability, methods=["GET"])
    app.app.add_url_rule(storage_url_prefix + "/test", view_func=test_contract, methods=["GET"])
    app.app.add_url_rule(storage_url_prefix + "/test2", view_func=test, methods=["GET"])
    app.app.add_url_rule(storage_url_prefix + "/activeContracts", view_func=active_contracts, methods=["GET"])

    # Post Methods
    app.app.add_url_rule(storage_url_prefix + "/signup", view_func=storage_signup, methods=["POST"])
    app.app.add_url_rule(storage_url_prefix + "/signin", view_func=storage_signin, methods=["POST"])
    app.app.add_url_rule(storage_url_prefix + "/withdraw", view_func=withdraw, methods=["POST"])
    app.app.add_url_rule(storage_url_prefix + "/updateConnection", view_func=update_connection, methods=["POST"])
    app.app.add_url_rule(storage_url_prefix + "/shardDoneUploading", view_func=storage_shard_done_uploading,
                         methods=["POST"])
    # app.app.add_url_rule(storage_url_prefix + "/auditResponse", methods=["POST"])  # result
    # app.app.add_url_rule(storage_url_prefix + "/clientConnectionPort", methods=["POST"])  # port, communication port
    # app.app.add_url_rule(storage_url_prefix + "/publicIpChange", methods=["POST"])  # decentorage port, ip_address
