from controllers import signup, signin
import app
user_url_prefix = '/user'


def add_user_urls():
    app.app.add_url_rule(user_url_prefix + "/signup", view_func=signup, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/signin", view_func=signin, methods=["POST"])
