from controllers import signup
import app
user_url_prefix = '/user'


def add_user_urls():
    app.app.add_url_rule(user_url_prefix + "/signup", view_func=signup, methods=["POST"])
