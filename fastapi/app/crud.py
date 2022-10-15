from typing import Optional
from datetime import datetime,timedelta

from sqlalchemy.orm import Session

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import aliased
from sqlalchemy import and_

from app import gtfs_models

from . import models, schemas,gtfs_models
from .config import Config
from .database import Session,get_db
from .utils.log_helper import *
from .utils.email_helper import *
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# stop_times utils
def get_stop_times_by_route_code(db, route_code: int,agency_id: str):
    the_query = db.query(models.StopTimes).filter(models.StopTimes.route_code == route_code,models.StopTimes.agency_id == agency_id).all()
    # user_dict = models.User[username]
    # return schemas.UserInDB(**user_dict)
    return the_query

def get_stop_times_by_trip_id(db, trip_id: str,agency_id: str):
    the_query = db.query(models.StopTimes).filter(models.StopTimes.trip_id == trip_id,models.StopTimes.agency_id == agency_id).all()
    # user_dict = models.User[username]route_code
    # return schemas.UserInDB(**user_dict)
    return the_query

def temp_solution(val):
    return True

def get_gtfs_rt_trips_by_trip_id(db, trip_id: str,agency_id: str):
    the_query = db.query(gtfs_models.TripUpdate).join(gtfs_models.StopTimeUpdate).filter(gtfs_models.TripUpdate.trip_id == trip_id,gtfs_models.TripUpdate.agency_id == agency_id).all()
    for row in the_query:
        temp_solution(row.stop_time_updates)
    return the_query

def get_gtfs_rt_trip_updates_all(db, agency_id:str):
    the_query = db.query(gtfs_models.TripUpdate).join(gtfs_models.StopTimeUpdate).filter(gtfs_models.TripUpdate.agency_id == agency_id).all()
    for row in the_query:
        temp_solution(row.stop_time_updates)
    return the_query

def get_gtfs_rt_stop_times_by_trip_id(db, trip_id: str,agency_id: str):
    if trip_id is None:
        the_query = db.query(gtfs_models.StopTimeUpdate).filter(gtfs_models.StopTimeUpdate.agency_id == agency_id).all()
    else:
        the_query = db.query(gtfs_models.StopTimeUpdate).filter(gtfs_models.StopTimeUpdate.trip_id == trip_id,gtfs_models.StopTimeUpdate.agency_id == agency_id).all()
    return the_query
    
def get_gtfs_rt_vehicle_positions_by_vehicle_id(db, vehicle_id: str,agency_id: str):
    if vehicle_id is None:
        the_query = db.query(gtfs_models.VehiclePosition).filter(gtfs_models.VehiclePosition.agency_id == agency_id).all()
    else:
        the_query = db.query(gtfs_models.VehiclePosition).filter(gtfs_models.VehiclePosition.vehicle_id == vehicle_id,gtfs_models.VehiclePosition.agency_id == agency_id).all()
    return the_query

def get_bus_stops(db, stop_code: int,agency_id: str):
    the_query = db.query(models.Stops).filter(models.Stops.stop_code == stop_code,models.Stops.agency_id == agency_id).all()
    # user_dict = models.User[username]
    # return schemas.UserInDB(**user_dict)
    return the_query

# generic function to get the gtfs data
def get_gtfs_data(db, tablename,column_name,query,agency_id):
    aliased_table = aliased(tablename)
    the_query = db.query(aliased_table).filter(getattr(aliased_table,column_name) == query,getattr(aliased_table,'agency_id') == agency_id).all()
    return the_query
    
def get_bus_stops_by_name(db, name: str):
    the_query = db.query(models.Stops).filter(models.Stops.stop_name.contains(name)).all()
    return the_query

def get_calendar_dates(db):
    the_query = db.query(models.CalendarDates).all()
    return the_query

## canceled trips

def get_canceled_trips(db, trp_route: str):
    if trp_route == 'all':
        the_query = db.query(models.CanceledServices).filter(models.CanceledServices.trp_type == 'REG').all()
        return the_query
    else:
        the_query = db.query(models.CanceledServices).filter(and_(models.CanceledServices.trp_route == trp_route),(models.CanceledServices.trp_type == 'REG')).all()
        return the_query

## go pass data
def get_gopass_schools(db, show_missing: bool):
    if show_missing == True:
        the_query = db.query(models.GoPassSchools).query(models.GoPassSchools).all()
        return the_query
    else:
        the_query = db.query(models.GoPassSchools).filter(models.GoPassSchools.school != None).all()
        return the_query

# email verification utils

def verify_email(payload,db: Session):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(payload, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        email_address: str = payload.get("sub")
        if email_address is None:
            raise credentials_exception
        token_data = schemas.EmailVerifyToken(email_address=email_address)
        email_to_activate = activate_email(db, email=token_data.email_address)
        if email_to_activate == False:
            return {"Message": "Email already verified"}
        user_api_token = email_to_activate.api_token
        response = {"Message": "Email is now verified","API_TOKEN": user_api_token}
        print("[verify_email] response: "+str(response))
        return response
    except JWTError:
        raise credentials_exception

def create_email_verification_token(email_address, expires_delta: Optional[timedelta] = None):
    print("[create_access_token]"+str())
    data = {"sub": email_address}
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        default_expiration_time = 60 # 60 minutes
        expire = datetime.utcnow() + timedelta(minutes=default_expiration_time)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt

def activate_email(db, email: str):
    the_query = db.query(models.User).filter(models.User.email == email).first()
    if the_query.is_email_verified == True:
        return False
    the_query.is_active = True
    the_query.is_email_verified = True
    payload = {"sub": the_query.username}
    the_query.api_token = create_api_token(payload)
    db.commit()
    db.refresh(the_query)    
    return the_query

# API Token utils
def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        email_address: str = payload.get("sub")
        if email_address is None:
            raise credentials_exception
        token_data = schemas.APIToken(email_address=email_address)
        return token_data
    except JWTError:
        raise credentials_exception

# passwords utils
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# user utils
def get_user(db, username: str):
    the_query = db.query(models.User).filter(models.User.username == username).first()
    # user_dict = models.User[username]
    # return schemas.UserInDB(**user_dict)
    return the_query

async def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def authenticate_user(username: str, password: str, db: Session):
    user = get_user(db, username)
    if not user:
        return False
    print("[crud]: "+str(verify_password(password, user.hashed_password)))
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt

def create_api_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = 0
    else:
        expire = 0
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    email_token = create_email_verification_token(user.email)
    send_verification_email_to_user(user.email, user.username,email_token)
    db_user = models.User(username=user.username,email=user.email, email_token=email_token,hashed_password=hashed_password,is_email_verified=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def send_verification_email_to_user(destination_email,username,email_verification_token):
    email_config = {"MAIL_SERVER":Config.MAIL_SERVER,"MAIL_PORT":587,"MAIL_USERNAME":Config.MAIL_USERNAME,"MAIL_PASSWORD":Config.MAIL_PASSWORD}

    message_in_txt = "Hi "+username+",\n\n"+"Please click on the link below to verify your email address.\n\n"+Config.BASE_URL+"/verify_email/"+email_verification_token+"\n\n"+"Thanks,\n"+"Metro API v2"
    message_in_html = "<p>Hi "+username+",</p><p>Please click on the link below to verify your email address.</p><p><a href=\""+Config.BASE_URL+"/api/verify_email/"+email_verification_token+"\">Verify Email</a></p><p>Thanks,</p><p>Metro API v2</p>"

    email_payload = {
        "email_subject": "Metro API v2 - Verify your email address",
        "email_message_txt": message_in_txt,
        "email_message_html": message_in_html
    }

    login_and_send_email(email_config, destination_email, email_payload)