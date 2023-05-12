import os
import logging
try:
    if os.path.isfile('app/secrets.py'):
        print('Loading secrets from secrets.py')
        from .secrets import load_secrets
        load_secrets()
except ModuleNotFoundError:
    logging.info('No secrets.py found, loading from environment variables')
    pass

class Config:
    BASE_URL = "https://api.metro.net"
    REDIS_URL = "redis://redis:6379"
    TARGET_DB_SCHEMA = "metro_api"
    DB_URI = os.environ.get('URI')
    SECRET_KEY = os.environ.get('HASH_KEY')
    ALGORITHM = os.environ.get('HASHING_ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES  = 30
    SWIFTLY_AUTH_KEY_BUS = os.environ.get('SWIFTLY_AUTH_KEY_BUS')
    SWIFTLY_AUTH_KEY_RAIL = os.environ.get('SWIFTLY_AUTH_KEY_RAIL')
    SERVER = os.environ.get('FTP_SERVER')
    USERNAME = os.environ.get('FTP_USERNAME')
    PASS = os.environ.get('FTP_PASS')
    REMOTEPATH = '/nextbus/prod/'
    DEBUG = True
    REPODIR = "/gtfs_rail"
    CURRENT_VERSION = "2.1.24"
    API_LAST_UPDATE_TIME = os.path.getmtime(r'app/main.py')
    LOGZIO_TOKEN = os.environ.get('LOGZIO_TOKEN')
    LOGZIO_URL = os.environ.get('LOGZIO_URL')
    RUNNING_ENV = os.environ.get('RUNNING_ENV')

    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_FROM = os.environ.get('MAIL_FROM')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_TLS = "True"
    MAIL_SSL = "False"
    USE_CREDENTIALS = "True"
    VALIDATE_CERTS = "True"