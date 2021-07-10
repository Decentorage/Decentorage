from controllers import heartbeat
import app
storage_url_prefix = '/storage'


def add_storage_urls():
    app.app.add_url_rule(storage_url_prefix + "/heartbeat", view_func=heartbeat, methods=["GET"])
