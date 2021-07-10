from flask import Flask
import pymongo
import config
from routes import add_storage_urls
#####################################
app = Flask(__name__)
database = None


def initialize(env):
    """
        Loads the app configuration from the config.py, registers the api namespaces,
        and initializes the database.
        *Parameters:*
            - *env (string)*: The environment in which the server is running for configurations
        *Returns:*
            - *True*: If the database connection was successful.
            - *False*: Otherwise. The response of the database connection attempt is also printed.
    """
    # Initializing configuration
    if env == 'prod':
        app.config.from_object(config.ProductionConfig)
        return True
    elif env == 'dev':
        app.config.from_object(config.DevelopmentConfig)
        return True

    else:
        print("Invalid environment")
        return False


def run(env):
    global database
    """
            Attempts to initialize the app, and runs it if the initialization was successful.
    """
    if initialize(env):
        # Initialize database
        database_uri = app.config['DATABASE_URI']
        database_name = app.config['DATABASE_NAME']
        client = pymongo.MongoClient(database_uri)
        database = client[database_name]
        # Add routes
        add_storage_urls(app, database)
        app.run(host="0.0.0.0")
