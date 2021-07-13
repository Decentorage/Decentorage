from controllers import heartbeat, withdraw
import app
storage_url_prefix = '/storage'


def add_storage_urls():
    app.app.add_url_rule(storage_url_prefix + "/heartbeat", view_func=heartbeat, methods=["GET"])
    app.app.add_url_rule(storage_url_prefix + "/withdraw", view_func=withdraw, methods=["GET"])

