from controllers import signup, signin, test
import app
user_url_prefix = '/user'


def add_user_urls():
    app.app.add_url_rule(user_url_prefix + "/signup", view_func=signup, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/signin", view_func=signin, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/test", view_func=test, methods=["POST"])
