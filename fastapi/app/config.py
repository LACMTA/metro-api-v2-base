import os
import versiontag
import logging
import git
from urllib.parse import urlparse, urlunparse
import asyncpg 
try:
    if os.path.isfile('app/app_secrets.py'):
        print('Loading secrets from secrets.py')
        from .app_secrets import load_secrets
        load_secrets()
except ModuleNotFoundError:
    logging.info('No secrets.py found, loading from environment variables')
    pass

def get_local_version_tag():
    parent_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
    g = git.cmd.Git(parent_directory)
    local_repo_details = g.describe('--tags')
    local_version_tag = local_repo_details.split('-')[0]
    return local_version_tag

def get_parent_folder_git_tag_version():
    online_tag = get_version_tag_from_online_github_repo()
    try:
        local_tag = get_local_version_tag()
        if local_tag != online_tag:
                return local_tag
        else:
            return online_tag        
    except Exception as e:
        logging.info('Error getting local version tag: ' + str(e))
        local_tag = '0.0.error '+ str(e)
        return online_tag

def get_version_tag_from_online_github_repo():
    try:
        g = git.cmd.Git()
        blob = g.ls_remote('https://github.com/LACMTA/metro-api-v2', tags=True)
        version_tag = blob.split('\n')[0].split('\t')[1].split('/')[2]
        return version_tag
    except Exception as e:
        logging.info('Error getting version tag from github: ' + str(e))
        return '0.0.error '+ str(e)

def get_pgbouncer_uri(original_uri):
    # Parse the original URI
    parsed = urlparse(original_uri)

    # Replace the hostname and port with the ones for PgBouncer
    pgbouncer_host = 'localhost'  # PgBouncer is running on the same machine
    pgbouncer_port = 6432  # Default PgBouncer port

    # Construct the new URI
    pgbouncer_uri = urlunparse(
        (parsed.scheme, f"{parsed.username}:{parsed.password}@{pgbouncer_host}:{pgbouncer_port}", parsed.path, parsed.params, parsed.query, parsed.fragment)
    )

    return pgbouncer_uri

class Config:
    BASE_URL = "https://api.metro.net"
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379')
    TARGET_DB_SCHEMA = "metro_api"
    API_DB_URI = get_pgbouncer_uri(os.environ.get('API_DB_URI'))
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
    CURRENT_API_VERSION = get_parent_folder_git_tag_version()
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