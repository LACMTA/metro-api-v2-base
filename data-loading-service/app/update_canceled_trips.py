import os
import pandas as pd
import json
from config import Config
from utils.ftp_helper import *
from utils.database_connector import *
from pathlib import Path

TARGET_FILE = "CancelledTripsRT.json"
REMOTEPATH = '/nextbus/prod/'
TARGET_FOLDER = 'data'
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
TARGET_PATH = os.path.join(CURRENT_DIRECTORY,TARGET_FOLDER)
LOCALPATH = os.path.realpath(TARGET_PATH)
# ftp_json_file_time = ''


from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
if "canceled_service" in tables:
    canceled_data_frame_from_database = pd.read_sql_query('select * from "canceled_service"',con=engine)
else:
    canceled_data_frame_from_database = pd.DataFrame()

def run_update():
    try:
        # logger.info('pulling CancelledTripsRT.json from FTP')
        print('pulling CancelledTripsRT.json from FTP')
        if connect_to_ftp(REMOTEPATH, Config.SERVER, Config.USERNAME, Config.PASS):
            get_file_from_ftp(TARGET_FILE, LOCALPATH)
        disconnect_from_ftp()
        target_json_path = Path(os.path.join(LOCALPATH,TARGET_FILE))
        load_canceled_service_into_db(target_json_path)
    except Exception as e:
        # logger.exception('FTP transfer failed: ' + str(e))
        print('FTP transfer failed: ' + str(e))
from sqlalchemy.orm import Session

def load_canceled_service_into_db(path_to_json_file):
    session = Session(bind=engine)
    try:
        with open(path_to_json_file) as json_file:
            opened_json_file = json.load(json_file)
        canceled_data_frame = pd.json_normalize(data=opened_json_file['CanceledService'])
        canceled_data_frame['trp_route'] = canceled_data_frame['trp_route'].str.replace(' ','')
        canceled_data_frame['dty_number'] = canceled_data_frame['dty_number'].str.replace(' ','')
        canceled_data_frame['LastUpdateDate'] = canceled_data_frame['LastUpdateDate'].str.split(';').str[0].str.replace('_',' ')

        canceled_data_frame_from_database = pd.read_sql_query('select * from "canceled_service"',con=session.bind)
        canceled_data_frame_from_database = canceled_data_frame_from_database.drop_duplicates(subset=['dpce_date','m_gtfs_trip_id'], keep='first')
        combined_df = pd.concat([canceled_data_frame_from_database,canceled_data_frame],ignore_index=True)
        combined_df.drop_duplicates(subset=['dpce_date','m_gtfs_trip_id'], keep='first')
        combined_df.to_sql('canceled_service',session.bind,index=False,if_exists="replace",schema=Config.TARGET_DB_SCHEMA)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()