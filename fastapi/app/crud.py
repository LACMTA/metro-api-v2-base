import polyline
import ast 
from turtle import position
from typing import Type, Optional
from datetime import datetime,timedelta
from fastapi.encoders import jsonable_encoder
from sqlalchemy.future import select


from sqlalchemy.sql import text
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from fastapi_pagination.ext.sqlalchemy import paginate as paginate_sqlalchemy

from geoalchemy2 import functions,shape
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape

from shapely.geometry import Point, mapping
from shapely import geometry as geo
# from shapely import to_geojson
# from app import models

from . import models, schemas
from .config import Config
from .database import Session,get_db,get_async_db,async_engine
from .models import BaseModel
from .utils.log_helper import *
from .utils.email_helper import *
from .utils.db_helper import *
from .utils.geojson_helper import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

import aioredis
import pickle

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Type, Optional

from shapely.wkb import loads

from sqlalchemy import distinct
from sqlalchemy.orm import Session
from sqlalchemy.orm.decl_api import DeclarativeMeta

redis = aioredis.from_url(Config.REDIS_URL, socket_connect_timeout=5)
# import sqlalchemy

def asdict(obj):
    result = {}
    for c in sqlalchemy.inspect(obj).mapper.column_attrs:
        value = getattr(obj, c.key)
        if isinstance(value, WKBElement):
            # Convert WKBElement to WKT format
            value = str(to_shape(value))
        result[c.key] = str(value)
    return result

def get_all_data(db: Session, model, agency_id):
    this_data = db.query(model).filter(model.agency_id == agency_id).all()
    result = [asdict(d) for d in this_data]
    return result


async def get_data_redis(db, model, id_field, id_value):
    # Create a unique key for this id_value
    key = f'{model.__tablename__}:{id_value}'

    # Try to get data from Redis
    data = await redis.get(key)

    if data is None:
        # If data is not in Redis, get it from the database
        result = db.query(model).filter(getattr(model, id_field) == id_value).all()

        if not result:
            return None

        # Convert the result to JSON and store it in Redis
        data = json.dumps([{
            key: (mapping(loads(value.desc)) if key == 'geometry' else value) 
            for key, value in row.__dict__.items() 
            if not key.startswith('_sa_instance_state')
        } for row in result])
        await redis.set(key, data)
    else:
        # Parse the JSON-formatted string back into a Python data structure
        data = json.loads(data)

    # Ensure data is a list
    if not isinstance(data, list):
        data = [data]
    return data

def get_unique_keys(db: Session, model, agency_id, key_column=None):
    if key_column:
        this_data = db.query(distinct(model.__dict__[key_column])).filter(model.agency_id == agency_id).all()
        unique_keys = [getattr(row, key_column) for row in this_data]
    else:
        this_data = db.query(model).filter(model.agency_id == agency_id).all()
        unique_keys = [row.__dict__ for row in this_data]
    return unique_keys




####
async def get_vehicle_data_async(db: AsyncSession, agency_id: str, vehicle_id: str):
    result = await db.execute(select(models.VehiclePositions).where(models.VehiclePositions.agency_id == agency_id,models.VehiclePositions.vehicle_id == vehicle_id))
    data = result.scalars().one_or_none()
    return data

import pickle

async def get_data_async(async_session: Session, model: Type[DeclarativeMeta], agency_id: str, field_name: Optional[str] = None, field_value: Optional[str] = None):
    # Create a unique key for this query
    key = f"{model.__name__}:{agency_id}:{field_name}:{field_value}"

    # Try to get the result from Redis
    result = await redis.get(key)
    if result is not None:
        data = pickle.loads(result)
        if isinstance(data, model):
            # If the data is a SQLAlchemy model instance, convert it to a dict
            data = {c.key: getattr(data, c.key) for c in sqlalchemy.inspect(data).mapper.column_attrs}
        return data

    if field_name and field_value:
        stmt = select(model).where(getattr(model, field_name) == field_value, getattr(model, 'agency_id') == agency_id)
    else:
        stmt = select(model).where(getattr(model, 'agency_id') == agency_id)
    result = await async_session.execute(stmt)
    data = result.scalars().all()
    return [item.to_dict() for item in data]
    
async def get_all_data_async(async_session: Session, model: Type[BaseModel], agency_id: str):
    data = await get_data_async(async_session, model, agency_id)
    return data


async def get_list_data_async(db: Session, model: Type[DeclarativeMeta], field: str, agency_id: str):
    stmt = select(getattr(model, field)).where(model.agency_id == agency_id).distinct()
    result = await db.execute(stmt)
    data = result.scalars().all()
    return data

import logging

async def get_list_of_unique_values_async(session: AsyncSession, model, agency_id: str, field_name: str):
    """
    Get a list of unique values for a specific field in a model.
    """
    # Create a unique key for this query
    key = f"{model.__name__}:{agency_id}:{field_name}:unique_values"
    logging.info(f"Generated key: {key}")

    # Try to get the result from Redis
    result = await redis.get(key)
    if result is not None:
        logging.info("Found result in Redis")
        return pickle.loads(result)

    # Use reflection to get the field from the model
    field = getattr(model, field_name, None)
    if field is None:
        raise ValueError(f"{field_name} does not exist in {model.__name__}")

    # Query the database for all values of this field
    stmt = select(field).where(model.agency_id == agency_id)
    result = await session.execute(stmt)

    # Use a set to get unique values, skipping None values
    unique_values  = []
    for row in result:
        if row[0] is not None and row[0] not in unique_values:
            unique_values.append(row[0])

    logging.info(f"Unique values from database: {unique_values}")

    # Store the result in Redis
    await redis.set(key, pickle.dumps(unique_values))

    return unique_values

async def get_all_gtfs_rt_vehicle_positions_trip_data_async(async_db: AsyncSession, agency_id: str, geojson: bool):
    result = await async_db.execute(
        select([models.StopTimeUpdates, models.VehiclePosition, models.Stop, models.StopTimes])
        .where(
            and_(
                models.StopTimeUpdates.trip_id == models.VehiclePositions.trip_id,
                models.StopTimeUpdates.stop_id == models.Stops.stop_id,
                models.StopTimes.trip_id == models.VehiclePositions.trip_id,
                models.StopTimes.stop_sequence == models.VehiclePositions.current_stop_sequence,
                models.VehiclePositions.agency_id == agency_id
            )
        )
    )
    return result.scalars().all()


# stop_times utils
def get_stop_times_by_route_code(db, route_code: str,agency_id: str):
    if route_code == 'list':
        the_query = db.query(models.StopTimes).filter(models.StopTimes.agency_id == agency_id).distinct(models.StopTimes.route_code).all()
        result = []
        for row in the_query:
            result.append(row.route_code)
        return result
    elif route_code == 'all':
        the_query = paginate_sqlalchemy(db, select(models.StopTimes).filter(models.StopTimes.agency_id == agency_id))
        return the_query
    else:
        the_query = paginate_sqlalchemy(db, select(models.StopTimes).filter(models.StopTimes.route_code == route_code,models.StopTimes.agency_id == agency_id))
    return the_query

async def get_stop_times_by_trip_id(db, trip_id: str, agency_id: str):
    # Try to get the result from Redis first
    cache_key = f'stop_times:{trip_id}:{agency_id}'
    cached_result = await redis.get(cache_key)
    if cached_result is not None:
        return pickle.loads(cached_result)

    if trip_id == 'list':
        the_query = db.query(models.StopTimes).filter(models.StopTimes.agency_id == agency_id).distinct(models.StopTimes.trip_id).all()
        result = []
        for row in the_query:
            result.append(row.trip_id)
    elif trip_id == 'all':
        the_query = paginate_sqlalchemy(db, select(models.StopTimes).filter(models.StopTimes.agency_id == agency_id))
        result = the_query
    else:
        the_query = paginate_sqlalchemy(db, select(models.StopTimes).filter(models.StopTimes.trip_id == trip_id,models.StopTimes.agency_id == agency_id))
        result = the_query

    # If result is not empty, store it in Redis for future use
    if result:
        await redis.set(cache_key, pickle.dumps(result))

    return result

# def get_stop_times_by_trip_id_old(db, trip_id: str,agency_id: str):
#     the_query = db.query(models.StopTimes).filter(models.StopTimes.trip_id == trip_id,models.StopTimes.agency_id == agency_id).all()
#     # user_dict = models.User[username]route_code
#     # return schemas.UserInDB(**user_dict)
#     return the_query

def temp_solution(val):
    return True

def list_gtfs_rt_trips_by_field_name(db, field_name: str,agency_id: str):
    result = []
    if field_name == 'stop_id':
        the_query = db.query(getattr(models.StopTimeUpdates,field_name),models.StopTimeUpdates.agency_id).with_entities(getattr(models.StopTimeUpdates,field_name)).filter(models.StopTimeUpdates.agency_id == agency_id).all()
    else:
        the_query = db.query(getattr(models.TripUpdate,field_name),models.TripUpdate.agency_id).with_entities(getattr(models.TripUpdate,field_name)).filter(models.TripUpdate.agency_id == agency_id).all()
    
    for row in the_query:
        result.append(row[0])
    return result

def list_gtfs_rt_vehicle_positions_by_field_name(db, field_name: str,agency_id: str):
    the_query = db.query(getattr(models.VehiclePosition,field_name),models.VehiclePositions.agency_id).with_entities(getattr(models.VehiclePosition,field_name)).filter(models.VehiclePositions.agency_id == agency_id).all()
    result = []
    for row in the_query:
        result.append(row[0])
    return result

async def get_gtfs_rt_trips_by_field_name(db, field_name: str, field_value: str, agency_id: str):
    # Try to get the result from Redis first
    cache_key = f'trips:{field_name}:{field_value}:{agency_id}'
    cached_result = await redis.get(cache_key)
    if cached_result is not None:
        return pickle.loads(cached_result)

    if field_name == 'stop_id':
        the_query = db.query(models.TripUpdate).join(models.StopTimeUpdates).filter(getattr(models.StopTimeUpdates,field_name) == field_value,models.TripUpdate.agency_id == agency_id).all()
    else:
        the_query = db.query(models.TripUpdate).filter(getattr(models.TripUpdate,field_name) == field_value,models.TripUpdate.agency_id == agency_id).all()
        if len(the_query) == 0:
            the_query = db.query(models.TripUpdate).filter(getattr(models.TripUpdate,field_name) == field_value,models.TripUpdate.agency_id == agency_id).all()
            return the_query

    result = []
    if the_query:
        for row in the_query:
            new_row = trip_update_reformat(row)
            result.append(new_row)

    # If result is not empty, store it in Redis for future use
    if result:
        await redis.set(cache_key, pickle.dumps(result))

    return result

async def get_all_gtfs_rt_trips(db, agency_id: str):
    # Try to get the result from Redis first
    cache_key = f'trips:{agency_id}'
    cached_result = await redis.get(cache_key)
    if cached_result is not None:
        return pickle.loads(cached_result)

    the_query = db.query(models.TripUpdate).filter(models.TripUpdate.agency_id == agency_id).all()
    result = []
    for row in the_query:
        new_row = trip_update_reformat(row)
        result.append(new_row)

    # If result is not empty, store it in Redis for future use
    if result:
        await redis.set(cache_key, pickle.dumps(result))

    return result

async def get_all_gtfs_rt_vehicle_positions(db, agency_id: str, geojson: bool):
    try:
        # Try to get the result from Redis first
        cache_key = f'vehicle_positions:{agency_id}:{geojson}'
        cached_result = await redis.get(cache_key)
        if cached_result is not None:
            return pickle.loads(cached_result)

        the_query = db.query(models.VehiclePositions).filter(models.VehiclePositions.agency_id == agency_id)
        all_rows = await get_all_data(the_query)  # Use the utility function here

        result = []
        if geojson:
            this_json = {}
            count = 0
            features = []
            for row in all_rows:
                count += 1
                features.append(await vehicle_position_reformat(row, geojson))  # await the coroutine here
            this_json['metadata'] = {'count': count}
            this_json['metadata'] = {'title': 'Vehicle Positions'}
            this_json['type'] = "FeatureCollection"
            this_json['features'] = features
            result = this_json
        else:
            for row in all_rows:
                new_row = await vehicle_position_reformat(row, geojson)  # await the coroutine here
                result.append(new_row)

        # If result is not empty, store it in Redis for future use
        if result:
            await redis.set(cache_key, pickle.dumps(result))

        return result
    except Exception as e:
        return e

def get_gtfs_rt_vehicle_positions_by_field_name(db, field_name: str,field_value: str,geojson:bool,agency_id: str):
    if field_value is None:
        the_query = db.query(models.VehiclePositions).filter(models.VehiclePositions.agency_id == agency_id).all()
    the_query = db.query(models.VehiclePositions).filter(getattr(models.VehiclePositions,field_name) == field_value,models.VehiclePositions.agency_id == agency_id).all()
    result = []
    if geojson == True:
        this_json = {}
        count = 0
        features = []
        for row in the_query:
            count += 1
            features.append(vehicle_position_reformat(row,geojson))
        this_json['metadata'] = {'count': count}
        this_json['metadata'] = {'title': 'Vehicle Positions'}
        this_json['type'] = "FeatureCollection"
        this_json['features'] = features
        return this_json
    for row in the_query:
        new_row = vehicle_position_reformat(row,geojson)
        result.append(new_row)
    return result

def _async(db, agency_id: str, geojson: bool):
    # Query the database for vehicle positions
    vehicle_positions = db.query(models.VehiclePositions).filter(
        models.VehiclePositions.agency_id == agency_id).all()

    # If geojson is True, return the data in GeoJSON format
    if geojson:
        features = [vehicle_position_reformat(vp, geojson) for vp in vehicle_positions if vp.trip_id]
        return {
            'metadata': {'count': len(features), 'title': 'Vehicle Positions'},
            'type': "FeatureCollection",
            'features': features
        }

    # Otherwise, reformat the data and add additional information
    result = []
    for vp in vehicle_positions:
        if vp.trip_id:
            new_row = vehicle_position_reformat_for_trip_details(vp, geojson)
            stop_name_query = db.query(models.Stops.stop_name).filter(
                models.Stops.stop_id == new_row.stop_id,
                models.Stops.agency_id == agency_id).first()
            new_row.stop_name = stop_name_query['stop_name']

            stop_time_update_query = db.query(models.StopTimeUpdates).filter(
                models.StopTimeUpdates.trip_id == new_row.trip_id,
                models.StopTimeUpdates.stop_sequence == new_row.current_stop_sequence).first()

            if stop_time_update_query:
                new_row.trip_assigned = True
                new_row.upcoming_stop_time_update = upcoming_stop_time_reformat(stop_time_update_query)

                route_code_query = db.query(models.StopTimes.route_code).filter(
                    models.StopTimes.trip_id == new_row.trip_id,
                    models.StopTimes.stop_sequence == new_row.current_stop_sequence).first()
                destination_code_query = db.query(models.StopTimes.destination_code).filter(
                    models.StopTimes.trip_id == new_row.trip_id,
                    models.StopTimes.stop_sequence == new_row.current_stop_sequence).first()

                new_row.route_code = route_code_query['route_code'] if route_code_query else None
                new_row.destination_code = destination_code_query['destination_code'] if destination_code_query else None

                result.append(new_row)

    # Return a message if no vehicle positions are available
    if not result:
        return [{"message": "No Vehicle Positions available at this time"}]

    return result
import pickle
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
async def get_gtfs_rt_vehicle_positions_trip_data_by_route_code(session: AsyncSession, route_code: str, geojson:bool, agency_id:str):
    cache_key = f'trip_data:{route_code}:{agency_id}'
    cached_data = await redis.get(cache_key)
    if cached_data is not None:
        return pickle.loads(cached_data)
    stmt = (
        select(models.VehiclePositions, models.StopTimeUpdates).
        join(models.StopTimeUpdates, 
             and_(models.VehiclePositions.trip_id == models.StopTimeUpdates.trip_id,
                  models.VehiclePositions.current_stop_sequence == models.StopTimeUpdates.stop_sequence)).
        filter(
            models.VehiclePositions.route_code == route_code,
            models.VehiclePositions.agency_id == agency_id,
        )
    )

    result = await session.execute(stmt)
    vehicle_positions = result.scalars().all()

    if geojson:
        return convert_to_geojson(vehicle_positions)

    return vehicle_positions


async def get_gtfs_rt_vehicle_positions_trip_data_by_route_code_for_async(session,route_code: str, geojson:bool,agency_id:str):
    the_query = await session.execute(select(models.VehiclePositions).where(models.VehiclePositions.route_code == route_code,models.VehiclePositions.agency_id == agency_id).order_by(models.VehiclePositions.route_code))
    if geojson == True:
        this_json = {}
        count = 0
        features = []
        for row in the_query.scalars().all():
            count += 1
            new_geojson = vehicle_position_reformat_for_trip_details_for_async(row,geojson)
            if new_geojson['properties']['trip']['stop_id']:
                geojson_stop_id = new_geojson['properties']['trip']['stop_id']
                stop_name_query = await session.execute(select(models.Stops.stop_name).where(models.Stops.stop_id == geojson_stop_id,models.Stops.agency_id == agency_id))
                for row in stop_name_query.scalars().all():
                    new_geojson['properties']['stop_name'] = row
                if new_geojson['properties']['trip']['trip_id']:
                        geojson_trip_id = new_geojson['properties']['trip']['trip_id']
                        geojson_current_stop_sequence = new_geojson['properties']['trip']['current_stop_sequence']
                        upcoming_stop_time_update_query = await session.execute(select(models.StopTimeUpdates).where(models.StopTimeUpdates.trip_id == geojson_trip_id,models.StopTimeUpdates.stop_sequence == geojson_current_stop_sequence))
                        # new_geojson['properties']['trip_info']['upcoming_stop_time_update'] = upcoming_stop_time_update_query.scalar()
                            # new_geojson['properties']['trip_info']['upcoming_stop_time_update'] = row
                        upcoming_update = upcoming_stop_time_reformat_for_async(upcoming_stop_time_update_query.scalars().first())
                        if upcoming_update:
                            new_geojson['properties']['trip']['upcoming_stop_time_update'] = upcoming_update
                            trip_details_query = await session.execute(select(models.TripUpdate).where(models.TripUpdate.trip_id == geojson_trip_id))
                            new_geojson['properties']['trip']['direction_id'] = trip_details_query.scalar().direction_id                            
                        route_code_query = await session.execute(select(models.StopTimes.route_code).where(models.StopTimes.trip_id == geojson_trip_id,models.StopTimes.stop_sequence == geojson_current_stop_sequence))
                        destination_code_query = await session.execute(select(models.StopTimes.destination_code).where(models.StopTimes.trip_id == geojson_trip_id,models.StopTimes.stop_sequence == geojson_current_stop_sequence))
                        if route_code_query:
                            new_geojson['properties']['trip']['route_code'] = route_code_query.scalar()
                        if destination_code_query:
                            new_geojson['properties']['trip']['destination_code'] = destination_code_query.scalar()

            features.append(new_geojson)
        this_json['metadata'] = {'count': count}
        this_json['metadata'] = {'title': 'Vehicle Positions'}
        this_json['type'] = "FeatureCollection"
        this_json['features'] = features
        yield this_json
    else:
        result = []
        for row in the_query.scalars().all():
            new_row = vehicle_position_reformat_for_trip_details_for_async(row,geojson)
            if new_row['trip']['stop_id']:
                this_stop_id = new_row['trip']['stop_id']
                stop_name_query = await session.execute(select(models.Stops.stop_name).where(models.Stops.stop_id == this_stop_id,models.Stops.agency_id == agency_id))
                new_row['stop_name'] = stop_name_query.scalar()
                new_row_current_stop_sequence = new_row['trip']['current_stop_sequence']
                new_row_trip_id = new_row['trip']['trip_id']
                upcoming_stop_time_update_query = await session.execute(select(models.StopTimeUpdates).where(models.StopTimeUpdates.trip_id == new_row_trip_id,models.StopTimeUpdates.stop_sequence == new_row_current_stop_sequence))
                if upcoming_stop_time_update_query is not None:
                    new_row['trip_assigned'] = True
                    trip_details_query = await session.execute(select(models.TripUpdate).where(models.TripUpdate.trip_id == new_row_trip_id))
                    new_row['direction_id'] = trip_details_query.scalar().direction_id
                new_row['upcoming_stop_time_update'] = upcoming_stop_time_reformat(upcoming_stop_time_update_query.scalars().first())
                route_code_query = await session.execute(select(models.StopTimes.route_code).where(models.StopTimes.trip_id == new_row_trip_id,models.StopTimes.stop_sequence == new_row_current_stop_sequence))
                destination_code_query = await session.execute(select(models.StopTimes.destination_code).where(models.StopTimes.trip_id == new_row_trip_id,models.StopTimes.stop_sequence == new_row_current_stop_sequence))
                new_row['route_code'] = route_code_query.scalar()
                new_row['destination_code'] = destination_code_query.scalar()
                result.append(new_row)
        if result == []:
            message_object = [{'message': 'No vehicle data for this vehicle id: ' + str(route_code)}]
            yield message_object
        else:
            yield result

def get_distinct_stop_ids(the_query):
    stop_id_list = []
    for row in the_query:
        if row.stop_id not in stop_id_list:
            stop_id_list.append(row.stop_id)
    return stop_id_list

async def get_gtfs_rt_line_detail_updates_for_route_code(session,route_code: str, geojson:bool,agency_id:str):
    the_query = await session.execute(select(models.StopTimeUpdates).where(models.StopTimeUpdates.route_code == route_code,models.StopTimeUpdates.agency_id == agency_id))

    # function call to get list of distinct stop_ids from the_query results
    stop_id_list = get_distinct_stop_ids(the_query.scalars().all())

    # loop through list of distinct stop_ids to create a stop_list that has:
    # - stop_sequence (might be different in result rows)
    # - stop_name (from stops)
    # - stop_id
    # - lat
    # - long
    # - departure times (array of times from all result rows)
    # - arrival times (array of times from all result rows)


    # format the result as a geojson object
    if geojson == True:
        this_json = {}
        count = 0
        features = []
        for row in the_query.scalars().all():
            count += 1
            new_geojson = '' # function call to reformat to geojson

            # if new_geojson is valid (if at least 1 StopTimeUpdates exists), then do stuff

            features.append(new_geojson)
        this_json['metadata'] = {'count': count}
        this_json['metadata'] = {'title': 'Stops'}
        this_json['metadata'] = {'stop_list': stop_id_list}
        this_json['type'] = "FeatureCollection"
        this_json['features'] = features
        yield this_json
    else:
        result = []
        new_row = ''
        result.append(new_row)

        if result == []:
            message_object = [{'message': 'No vehicle data for this vehicle id: ' + str(route_code)}]
            yield message_object
        else:
            yield result

async def get_gtfs_rt_vehicle_positions_trip_data_redis(db, vehicle_id: str):
    # Create a unique key for this vehicle_id
    key = f'vehicle:{vehicle_id}'
    
    # Try to get data from Redis
    data = await redis.get(key)
    
    if data is None:
        # If data is not in Redis, get it from the database
        result = db.query(models.VehiclePositions).filter(models.VehiclePositions.vehicle_id == vehicle_id).all()
        
        if not result:
            return None
        
        # Convert the result to JSON and store it in Redis
        data = json.dumps([dict(row) for row in result])
        await redis.set(key, data)
    
    return data


async def get_gtfs_rt_vehicle_positions_trip_data(db, vehicle_id: str, geojson: bool, agency_id: str):
    # Try to get the result from Redis first
    cache_key = f'vehicle_positions:{vehicle_id}:{geojson}:{agency_id}'
    result = await redis.get(cache_key)
    if result is not None:
        return pickle.loads(result)

    result = []
    the_query = db.query(models.VehiclePositions).filter(models.VehiclePositions.vehicle_id == vehicle_id,models.VehiclePositions.agency_id == agency_id).all()
    if geojson == True:
        this_json = {}
        count = 0
        features = []
        for row in the_query:
            count += 1
            features.append(vehicle_position_reformat(row,geojson))
            if row.trip_id is None:
                message_object = [{'message': 'No trip data for this vehicle id: ' + str(vehicle_id)}]
                this_json['metadata'] = {'warning': message_object}
        this_json['metadata'] = {'count': count}
        this_json['metadata'] = {'title': 'Vehicle Positions'}
        this_json['type'] = "FeatureCollection"
        this_json['features'] = features
        if this_json:
            await redis.set(cache_key, pickle.dumps(this_json))

        return this_json
    for row in the_query:
        if row.trip_id is None:
            message_object = [{'message': 'No trip data for this vehicle id: ' + str(vehicle_id)}]
            return message_object
        new_row = vehicle_position_reformat_for_trip_details(row,geojson)
        stop_name_query = db.query(models.Stops.stop_name).filter(models.Stops.stop_id == new_row.stop_id,models.Stops.agency_id == agency_id).first()
        new_row.stop_name = stop_name_query[0]
        upcoming_stop_time_update_query = db.query(models.StopTimeUpdates).filter(models.StopTimeUpdates.trip_id == new_row.trip_id,models.StopTimeUpdates.stop_sequence == new_row.current_stop_sequence).first()
        if upcoming_stop_time_update_query is not None:
            new_row.trip_assigned = True
        new_row.upcoming_stop_time_update = upcoming_stop_time_reformat(upcoming_stop_time_update_query)
        route_code_query = db.query(models.StopTimes.route_code).filter(models.StopTimes.trip_id == new_row.trip_id,models.StopTimes.stop_sequence == new_row.current_stop_sequence).first()
        destination_code_query = db.query(models.StopTimes.destination_code).filter(models.StopTimes.trip_id == new_row.trip_id,models.StopTimes.stop_sequence == new_row.current_stop_sequence).first()
        new_row.route_code = route_code_query[0]
        new_row.destination_code = destination_code_query[0]
        result.append(new_row)
    if result == []:
        message_object = [{'message': 'No vehicle data for this vehicle id: ' + str(vehicle_id)}]
        return message_object
    else:
        if result:
            await redis.set(cache_key, pickle.dumps(result))

        return result
    
def get_gtfs_rt_trips_by_trip_id(db, trip_id: str,agency_id: str):
    the_query = db.query(models.TripUpdate).filter(models.TripUpdate.trip_id == trip_id,models.TripUpdate.agency_id == agency_id).all()
    result = []
    for row in the_query:
        new_row = trip_update_reformat(row)
        result.append(new_row)
    return result

    

def get_stops_id(db, stop_code: str,agency_id: str):
    result = []
    if stop_code == 'list':
        the_query = db.query(models.Stops).filter(models.Stops.agency_id == agency_id).all()
        for row in the_query:
            result.append(row.stop_code)
        return result
    elif stop_code == 'all':
        the_query = db.query(models.Stops).filter(models.Stops.agency_id == agency_id).all()
        for row in the_query:
            this_object = {}
            this_object['type'] = 'Feature' 
            this_object['geometry']= JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            del row.geometry
            this_object['properties'] = row
            result.append(this_object)
        return result
    else:
        the_query = db.query(models.Stops).filter(models.Stops.stop_code == stop_code,models.Stops.agency_id == agency_id).all()
        for row in the_query:
            this_object = {}
            this_object['type'] = 'Feature' 
            this_object['geometry']= JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            del row.geometry
            this_object['properties'] = row
            result.append(this_object)
    return result
    # user_dict = models.User[username]
    # return schemas.UserInDB(**user_dict)

def get_trips_data(db,trip_id: str,agency_id: str):
    if trip_id == 'list':
        the_query = db.query(models.Trips).filter(models.Trips.agency_id == agency_id).all()
        result = []
        for row in the_query:
            result.append(row.trip_id)
        return result
    elif trip_id == 'all':
        the_query = db.query(models.Trips).filter(models.Trips.agency_id == agency_id).all()
        return the_query
    else:
        the_query = db.query(models.Trips).filter(models.Trips.trip_id == trip_id,models.Trips.agency_id == agency_id).all()
    return the_query

def get_agency_data(db, tablename,agency_id):
    aliased_table = aliased(tablename)
    the_query = db.query(aliased_table).filter(getattr(aliased_table,'agency_id') == agency_id).all()
    return the_query

def get_shape_list(db,agency_id):
    the_query = db.query(models.Shapes).filter(models.Shapes.agency_id == agency_id).all()
    result = []
    for row in the_query:
        result.append(row.shape_id)
    return result

def get_shape_all(db,agency_id):
    the_query = db.query(models.Shapes).filter(models.Shapes.agency_id == agency_id).all()
    result = []
    # for row in the_query:
    #     result.append(row.shape_id)
    for row in the_query:
        this_object = {}
        this_object['type'] = 'Feature' 
        this_object['geometry']= JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
        del row.geometry
        this_object['properties'] = row
        result.append(this_object)
    return result

def get_trip_shapes_list(db,agency_id):
    the_query = db.query(models.TripShapes).filter(models.TripShapes.agency_id == agency_id).all()
    result = []
    for row in the_query:
        result.append(row.shape_id)
    return result

def get_trip_shapes_all(db,agency_id):
    the_query = db.query(models.TripShapes).filter(models.TripShapes.agency_id == agency_id).all()
    result = []
    for row in the_query:
        this_object = {}
        this_object['type'] = 'Feature' 
        this_object['geometry']= JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
        this_object['encoded_polyline'] = polyline.encode(this_object['geometry']['coordinates'],geojson=False)
        del row.geometry
        this_object['properties'] = row
        result.append(this_object)
    return result

def get_trip_shape(db,shape_id,agency_id):
    the_query = db.query(models.TripShapes).filter(models.TripShapes.shape_id == shape_id,models.TripShapes.agency_id== agency_id).all()
    for row in the_query:
        new_object = {}
        new_object['type'] = 'Feature' 
        this_object_geom = geo.mapping(shape.to_shape((row.geometry)))
        new_object['geometry']= JsonReturn(this_object_geom)
        new_object['encoded_polyline'] = polyline.encode(new_object['geometry']['coordinates'],geojson=False)
        properties = {}
        properties = {'shape_id': row.shape_id,'agency_id': row.agency_id}
        new_object['properties'] = properties
        return new_object

def get_shape_by_id(db,geojson,shape_id,agency_id):
    the_query = db.query(models.Shapes).filter(models.Shapes.shape_id == shape_id,models.Shapes.agency_id== agency_id).all()
    result = []
    if geojson:
        for row in the_query:
            new_object = {}
            new_object['type'] = 'Feature' 
            new_object['geometry']= JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            properties = {}
            properties = {'shape_id': row.shape_id,'agency_id': row.agency_id}
            new_object['properties'] = properties
            result.append(new_object)
        return result
    else:
        return the_query

def get_routes_by_route_id(db,route_id,agency_id):
    if route_id == 'list':
        the_query = db.query(models.Routes).filter(models.Routes.agency_id == agency_id).distinct(models.Routes.route_id).all()
        result = []
        for row in the_query:
            result.append(row.route_id)
        return result
    elif route_id == 'all':
        the_query = db.query(models.Routes).filter(models.Routes.agency_id == agency_id).all()
        return the_query
    else:
        the_query = db.query(models.Routes).filter(models.Routes.route_id == route_id,models.Routes.agency_id == agency_id).all()
        return the_query

async def get_route_overview_by_route_code_async(db, agency_id, route_code=None):
    if route_code is None or route_code.lower() == 'all':
        the_query = await db.query(models.RouteOverview).order_by(models.RouteOverview.route_code_padded).all()
        agency_schedule_data = {}
        for row in the_query:
            if row.agency_id in agency_schedule_data:
                agency_schedule_data[row.agency_id].append(row)
            else:
                agency_schedule_data[row.agency_id] = [row]
        return agency_schedule_data
    elif route_code == 'list':
        the_query = await db.query(models.RouteOverview).filter(models.RouteOverview.agency_id == agency_id).distinct(models.RouteOverview.route_code).all()
        result = []
        for row in the_query:
            result.append(row.route_code)
        return result    
    else:
        the_query = await db.query(models.RouteOverview).filter(models.RouteOverview.route_code == route_code,models.RouteOverview.agency_id == agency_id).all()
        if the_query:
            return the_query
        else:
            error_message = {'error': 'No route found for route code: ' + route_code}
            return error_message

def get_route_overview_by_route_code(db,route_code,agency_id):
    if agency_id.lower() == 'all':
        the_query = db.query(models.RouteOverview).order_by(models.RouteOverview.route_code_padded).all()
        agency_schedule_data = {}
        for row in the_query:
            if row.agency_id in agency_schedule_data:
                agency_schedule_data[row.agency_id].append(row)
            else:
                agency_schedule_data[row.agency_id] = [row]
        return agency_schedule_data
    if route_code == 'list':
        the_query = db.query(models.RouteOverview).filter(models.RouteOverview.agency_id == agency_id).distinct(models.RouteOverview.route_code).all()
        result = []
        for row in the_query:
            result.append(row.route_code)
        return result    
    elif route_code != 'all':
        the_query = db.query(models.RouteOverview).filter(models.RouteOverview.route_code == route_code,models.RouteOverview.agency_id == agency_id).all()
        if the_query:
            return the_query
        else:
            error_message = {'error': 'No route found for route code: ' + route_code}
            return error_message
    else:
        the_query = db.query(models.RouteOverview).filter(models.RouteOverview.agency_id == agency_id).all()
        return the_query      
      
def get_gtfs_route_stops_for_buses(db,route_code):
    the_query = db.query(models.RouteStops).filter(models.RouteStops.route_code == route_code,models.RouteStops.agency_id == 'LACMTA').all()
    result = []
    for row in the_query:
        new_object = {}
        new_object['route_id'] = row.route_id
        new_object['route_code'] = row.route_code
        new_object['stop_id'] = row.stop_id
        new_object['coordinates'] = row.coordinates
        result.append(new_object)
        # for 

    return the_query

def get_gtfs_route_stops(db,route_code,daytype,agency_id):
    result = []
    if daytype != 'all':
        the_query = db.query(models.RouteStops).filter(models.RouteStops.route_code == route_code,models.RouteStops.agency_id == agency_id,models.RouteStops.day_type == daytype).all()
        for row in the_query:
            new_object = {}
            new_object['route_id'] = row.route_id
            new_object['route_code'] = row.route_code
            new_object['stop_id'] = row.stop_id
            new_object['day_type'] = row.day_type
            new_object['agency_id'] = row.agency_id
            new_object['geojson'] = JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            new_object['stop_sequence'] = row.stop_sequence
            new_object['direction_id'] = row.direction_id
            new_object['stop_name'] = row.stop_name
            new_object['latitude'] = row.latitude
            new_object['longitude'] = row.longitude
            new_object['departure_times'] = ast.literal_eval(row.departure_times)
            result.append(new_object)
        return result
    else:
        the_query = db.query(models.RouteStops).filter(models.RouteStops.route_code == route_code,models.RouteStops.agency_id == agency_id).all()
        for row in the_query:
            new_object = {}
            new_object['route_id'] = row.route_id
            new_object['route_code'] = row.route_code
            new_object['stop_id'] = row.stop_id
            new_object['day_type'] = row.day_type
            new_object['agency_id'] = row.agency_id
            new_object['geojson'] = JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            new_object['stop_sequence'] = row.stop_sequence
            new_object['direction_id'] = row.direction_id
            new_object['stop_name'] = row.stop_name
            new_object['latitude'] = row.latitude
            new_object['longitude'] = row.longitude
            new_object['departure_times'] = ast.literal_eval(row.departure_times)
            result.append(new_object)
        return result


def get_gtfs_route_stops_grouped(db,route_code,agency_id):
    the_query = db.query(models.RouteStopsGrouped).filter(models.RouteStopsGrouped.route_code == route_code,models.RouteStopsGrouped.agency_id == agency_id).all()
    return the_query
# generic function to get the gtfs static data
def get_gtfs_static_data(db, tablename,column_name,query,agency_id):
    aliased_table = aliased(tablename)
    if query == 'list':
            the_query = db.query(aliased_table).filter(getattr(aliased_table,column_name) == query,getattr(aliased_table,'agency_id') == agency_id).all()
    else:
        the_query = db.query(aliased_table).filter(getattr(aliased_table,column_name) == query,getattr(aliased_table,'agency_id') == agency_id).all()
    return the_query

def get_calendar_data_by_id(db,service_id,agency_id):
    the_query = db.query(models.Calendar).filter(models.Calendar.service_id == service_id,models.Calendar.agency_id == agency_id).all()
    return the_query

def get_bus_stops_by_name(db, name: str):
    the_query = db.query(models.Stops).filter(models.Stops.stop_name.contains(name)).all()
    return the_query

def get_calendar_dates(db):
    the_query = db.query(models.CalendarDates).all()
    return the_query

## canceled trips
async def get_canceled_trips(db: AsyncSession, trp_route: str):
    if trp_route == 'all':
        stmt = select(models.CanceledServices).where(models.CanceledServices.trp_type == 'REG')
    else:
        stmt = select(models.CanceledServices).where(and_(models.CanceledServices.trp_route == trp_route, models.CanceledServices.trp_type == 'REG'))
    
    result = await db.execute(stmt)
    return result.scalars().all()
## go pass data
async def get_gopass_schools_combined_phone(db: AsyncSession, groupby_column='id'):
    the_query = await db.execute(text("SELECT "+groupby_column+", string_agg(distinct(phone), ' | ') AS phone_list FROM go_pass_schools GROUP  BY 1 order by "+groupby_column+" asc;"))  
    temp_array = []
    results_as_dict = the_query.mappings().all()
    return results_as_dict

async def get_gopass_schools(db: AsyncSession, show_missing: bool):
    if show_missing:
        stmt = select(models.GoPassSchools)
    else:
        stmt = select(models.GoPassSchools).where(models.GoPassSchools.school != None)
    
    result = await db.execute(stmt)
    return result.scalars().all()
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