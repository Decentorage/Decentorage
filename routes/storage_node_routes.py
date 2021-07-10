from controllers import heartbeat
storage_url_prefix = '/storage'


def add_storage_urls(app, database):
    app.add_url_rule(storage_url_prefix + "/heartbeat", view_func=lambda: heartbeat(database))
