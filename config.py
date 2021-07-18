import os


class BaseConfig:
    SERVER_PATH = 'http://127.0.0.1:5000/'
    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    SECRET_KEY = os.environ['SECRET_KEY']
    CODE_KEY = 'decentorageCode'
    MAIL_USERNAME = 'no-reply@decentorage.tech'
    MAIL_PASSWORD = ''
    FRONT_END_ROOT = 'http://www.decentorage.tech'
    SHARD_ID_KEY = os.environ["SHARD_ID_KEY"]


class DevelopmentConfig(BaseConfig):
    DATABASE_URI =  os.environ['MONGODB_DEV_URI']
    DATABASE_NAME = os.environ['MONGODB_DEV_NAME']
    ENV = 'development'
    DEBUG = True


class ProductionConfig(BaseConfig):
    ENV = 'production'
    DEBUG = False
    DATABASE_URI = os.environ['MONGODB_PROD_URI']
    DATABASE_NAME = os.environ['MONGODB_PROD_NAME']