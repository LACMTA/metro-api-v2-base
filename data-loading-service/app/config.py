import os
import logging
import versiontag
import git

try:
    if os.path.isfile('app/app_secrets.py'):
        print('Loading secrets from secrets.py')
        from app_secrets import load_secrets  # Changed from relative to absolute import
        load_secrets()
except ModuleNotFoundError:
    logging.info('No secrets.py found, loading from environment variables')
    pass

def get_parent_folder_git_tag_version():
    full_version_tag = versiontag.get_version(pypi=True)
    if full_version_tag is None:
        get_version_tag_from_online_github_repo()
    else:
        if len(full_version_tag.split('.')) > 2:
            short_version_tag = full_version_tag.rsplit('.', 1)[0]
            return short_version_tag    
        else:
            return full_version_tag

def get_version_tag_from_online_github_repo():
    try:
        g = git.cmd.Git()
        blob = g.ls_remote('https://github.com/LACMTA/metro-api-v2', tags=True)
        version_tag = blob.split('\n')[0].split('\t')[1].split('/')[2]
        return version_tag
    except Exception as e:
        logging.info('Error getting version tag from github: ' + str(e))
        return '0.0.error '+ str(e)


def set_db_schema():
    try:
        current_environment = os.environ.get('RUNNING_ENV')
        if current_environment == 'prod':
            return 'metro_api'
        else:
            return 'metro_api_dev'
    except Exception as e:
        print('Error setting db schema: ' + str(e))


class Config:
    BASE_URL = "https://api.metro.net"
    TARGET_DB_SCHEMA = set_db_schema()
    API_DB_URI = os.environ.get('API_DB_URI')
    SECRET_KEY = os.environ.get('HASH_KEY')
    ALGORITHM = os.environ.get('HASHING_ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES  = 30
    SWIFTLY_AUTH_KEY_BUS = os.environ.get('SWIFTLY_AUTH_KEY_BUS')
    SWIFTLY_AUTH_KEY_RAIL = os.environ.get('SWIFTLY_AUTH_KEY_RAIL')
    SERVER = os.environ.get('FTP_SERVER')
    USERNAME = os.environ.get('FTP_USERNAME')
    ENVIRONMENT = os.environ.get('FTP_USERNAME')
    PASS = os.environ.get('FTP_PASS')
    REMOTEPATH = '/nextbus/prod/'
    DEBUG = True
    REPODIR = "/gtfs_rail"
    CURRENT_API_VERSION = get_parent_folder_git_tag_version()
    # API_LAST_UPDATE_TIME = os.path.getmtime(r'main.py')
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