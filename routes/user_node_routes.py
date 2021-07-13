from controllers import signup, signin, test, get_active_contracts
import app
user_url_prefix = '/user'


def add_user_urls():
    # Get Methods
    app.app.add_url_rule(user_url_prefix + "/getFiles", view_func=get_active_contracts, methods=["GET"])
    # Post Methods
    app.app.add_url_rule(user_url_prefix + "/signup", view_func=signup, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/signin", view_func=signin, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/test", view_func=test, methods=["POST"])
