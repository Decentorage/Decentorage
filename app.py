from flask import Flask, request
import pymongo
import config
from routes import add_storage_urls, add_user_urls
from cryptography.fernet import Fernet

#####################################
app = Flask(__name__)
database = None
secret_key = None
fernet = None


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
    elif env == 'dev':
        app.config.from_object(config.DevelopmentConfig)
    else:
        print("Invalid environment")
        return False
    return True


def run(env):
    global database, secret_key, fernet
    """
            Attempts to initialize the app, and runs it if the initialization was successful.
    """
    if initialize(env):
        # Initialize database
        database_uri = app.config['DATABASE_URI']
        database_name = app.config['DATABASE_NAME']
        client = pymongo.MongoClient(database_uri)
        database = client[database_name]
        secret_key = app.config['SECRET_KEY']
        shard_id_key = str.encode(app.config['SHARD_ID_KEY'])
        fernet = Fernet(shard_id_key)
        # Add routes
        add_storage_urls()
        add_user_urls()
        app.run(host="0.0.0.0", port=5000)


@app.after_request
def inject_cors_headers(response):
    #if 'Origin' in request.headers:
    #    response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
    #else:
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Methods', 'DELETE, GET, HEAD, OPTIONS, POST, PUT, PATCH')
    response.headers.add('Access-Control-Allow-Headers', 'Origin, Content-Type, User-Agent, Content-Range, Token, Code')
    response.headers.add('Access-Control-Expose-Headers', 'DAV, content-length, Allow')
    return response
