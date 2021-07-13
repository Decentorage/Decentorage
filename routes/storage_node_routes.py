from controllers import heartbeat, signin, signup
import app
storage_url_prefix = '/storage'


def add_storage_urls():
    app.app.add_url_rule(storage_url_prefix + "/signup", view_func=signup, methods=["POST"])
    app.app.add_url_rule(storage_url_prefix + "/signin", view_func=signin, methods=["POST"])
    app.app.add_url_rule(storage_url_prefix + "/heartbeat", view_func=heartbeat, methods=["GET"])
