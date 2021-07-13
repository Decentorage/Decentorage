from controllers import heartbeat, withdraw, storage_signin, storage_signup
import app

storage_url_prefix = '/storage'


def add_storage_urls():
    # Get Methods
    app.app.add_url_rule(storage_url_prefix + "/heartbeat", view_func=heartbeat, methods=["GET"])
    app.app.add_url_rule(storage_url_prefix + "/withdraw", view_func=withdraw, methods=["GET"])
    # Post Methods
    app.app.add_url_rule(storage_url_prefix + "/signup", view_func=storage_signup, methods=["POST"])
    app.app.add_url_rule(storage_url_prefix + "/signin", view_func=storage_signin, methods=["POST"])
    # app.app.add_url_rule(storage_url_prefix + "/auditResponse", methods=["POST"])  # result
    # app.app.add_url_rule(storage_url_prefix + "/clientConnectionPort", methods=["POST"])  # port, communication port
    # app.app.add_url_rule(storage_url_prefix + "/publicIpChange", methods=["POST"])  # decentorage port, ip_address
