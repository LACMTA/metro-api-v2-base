# import data modules
from distutils.command.config import config
from typing import Union, List, Dict, Optional
from versiontag import get_version
import traceback
import sys
import http
import json
import requests
import csv
import os
import asyncio
import aioredis

import pytz
import time


from datetime import timedelta, date, datetime

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Query, WebSocket,WebSocketDisconnect
from fastapi import Path as FastAPIPath
# from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse,PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from sqlalchemy import false, distinct, inspect
from sqlalchemy.orm import aliased
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from collections import defaultdict


from pydantic import BaseModel, Json, ValidationError
import functools
import io
import yaml

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from starlette.requests import Request
from starlette.responses import Response





# from redis import asyncio as aioredis
from enum import Enum


# for OAuth2
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm

# from app.models import *
# from app.security import *

# Pagination
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.ext.sqlalchemy import paginate as paginate_sqlalchemy
from fastapi_pagination.links import Page
from datetime import datetime, timedelta

from .utils.log_helper import *

from .database import Session, AsyncSession, engine, session, get_db,get_async_db
from . import crud, models, security, schemas
from .config import Config
from pathlib import Path

from logzio.handler import LogzioHandler
import logging
import typing as t

SERVER_OVERLOAD_THRESHOLD = 1.2
### Pagination Parameter Options (deafult pagination count, default starting page, max_limit)
Page = Page.with_custom_options(
    size=Query(100, ge=1, le=500),
)

async def get_data(db: Session, key: str, fetch_func):
    # Get data from Redis
    data = await crud.redis_connection.get(key)
    if data is None:
        # If data is not in Redis, get it from the database
        data = fetch_func(db, key)
        if data is None:
            return None
        # Set data in Redis
        await crud.redis_connection.set(key, data)
    return data


class EndpointFilter(logging.Filter):
    def __init__(
        self,
        path: str,
        *args: t.Any,
        **kwargs: t.Any,
    ):
        super().__init__(*args, **kwargs)
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(self._path) == -1

class BlockRepeatedRequestsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests=100, block_duration=timedelta(minutes=5)):
        super().__init__(app)
        self.max_requests = max_requests
        self.block_duration = block_duration
        self.requests = defaultdict(int)
        self.last_request_time = defaultdict(datetime.now)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path

        if path.startswith("/agencies/lametro-rail/routes/") or path.startswith("/agencies/lametro"):
            if datetime.now() - self.last_request_time[client_ip] < self.block_duration:
                self.requests[client_ip] += 1
            else:
                self.requests[client_ip] = 1

            if self.requests[client_ip] > self.max_requests:
                return PlainTextResponse("Too many requests", status_code=429)

            self.last_request_time[client_ip] = datetime.now()

        try:
            response = await call_next(request)
        except HTTPException as exc:
            if exc.status_code == 404:  # Not Found
                self.requests[client_ip] += 1
            raise

        return response
    
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(EndpointFilter(path="/LACMTA/shapes/"))
uvicorn_logger.addFilter(EndpointFilter(path="/agencies/lametro/"))

UPDATE_INTERVAL = 300

TARGET_FILE = "CancelledTripsRT.json"
REMOTEPATH = '/nextbus/prod/'
PARENT_FOLDER = Path(__file__).parents[1]
TARGET_FOLDER = 'appdata'
TARGET_PATH = os.path.join(PARENT_FOLDER,TARGET_FOLDER)
TARGET_PATH_CALENDAR_JSON = os.path.join(TARGET_PATH,'calendar.json')
TARGET_PATH_CANCELED_JSON = os.path.join(TARGET_PATH,'CancelledTripsRT.json')
PATH_TO_CALENDAR_JSON = os.path.realpath(TARGET_PATH_CALENDAR_JSON)
PATH_TO_CANCELED_JSON = os.path.realpath(TARGET_PATH_CANCELED_JSON)

class AgencyIdEnum(str, Enum):
    LACMTA = "LACMTA"
    LACMTA_Rail = "LACMTA_Rail"

class AllAgencyIdEnum(Enum):
    LACMTA = "LACMTA"
    LACMTA_Rail = "LACMTA_Rail"
    all = "all"
class GoPassGroupEnum(str, Enum):
    ID = "id"
    SCHOOL = "school"

class TripUpdatesFieldsEnum(str, Enum):
    trip_id = "trip_id"
    route_id = "route_id"

class VehiclePositionsFieldsEnum(str, Enum):
    vehicle_id = "vehicle_id"
    trip_route_id = "trip_route_id"
    route_code = "route_code"
    stop_id = "stop_id"

class StopTimeUpdatesFieldsEnum(str, Enum):
    stop_id = "stop_id"
    trip_id = "trip_id"
    stop_sequence = "stop_sequence"

class DayTypesEnum(str, Enum):
    weekday = "weekday"
    saturday = "saturday"
    sunday = "sunday"
    no_type = "no_type"
    all = "all"

class FormatEnum(str, Enum):
    json = "json"
    geojson = "geojson"

class OperationEnum(str, Enum):
    all = 'all'
    list = 'list'
    id = 'id'


class IdTypeEnum(str, Enum):
    vehicle_id = "vehicle_id"
    trip_id = "trip_id"
    route_code = "route_code"
    stop_id = "stop_id"

class LogFilter(logging.Filter):
    def filter(self, record):
        record.app = "api.metro.net"
        record.env = Config.RUNNING_ENV
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit=100, interval=60):
        super().__init__(app)
        self.limit = limit
        self.interval = interval
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        request_times = self.requests[client_ip]
        request_times.append(time.time())

        # Remove requests older than the rate limit interval
        while request_times and request_times[0] < time.time() - self.interval:
            request_times.pop(0)

        if len(request_times) > self.limit:
            raise HTTPException(status_code=429, detail="Too Many Requests")

        response = await call_next(request)
        return response

tags_metadata = [
    {"name": "Real-Time data", "description": "Includes GTFS-RT data for Metro Rail and Metro Bus."},
    {"name": "Canceled Service Data", "description": "Canceled service data for Metro Bus and Metro Rail."},
    {"name": "Static data", "description": "GTFS Static data, including routes, stops, and schedules."},
    {"name": "Other data", "description": "Other data on an as-needed basis."},
    {"name": "User Methods", "description": "Methods for user authentication and authorization."},
]

inspector = inspect(engine)

from sqlalchemy import Table

app = FastAPI(openapi_tags=tags_metadata,docs_url="/")
app.add_middleware(RateLimitMiddleware, limit=100, interval=60)

# db = connect(host=''ort=0, timeout=None, source_address=None)


@app.exception_handler(Exception)
async def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    # Change here to LOGGER
    return JSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})

# templates = Jinja2Templates(directory="app/documentation")
# app.mount("/", StaticFiles(directory="app/documentation", html=True))
templates = Jinja2Templates(directory="app/frontend")
app.mount("/", StaticFiles(directory="app/frontend"))


###### Utility functions ######
from geojson import Point, Feature, FeatureCollection
from shapely import wkt

def to_geojson(data):
    features = []
    for item in data:
        # Create a Point from the 'geometry' coordinates
        geometry = Point(item['geometry']['coordinates'])
        # Exclude the 'geometry' key from the properties
        properties = {key: item[key] for key in item if key != 'geometry'}
        feature = Feature(geometry=geometry, properties=properties)
        features.append(feature)
    feature_collection = FeatureCollection(features)
    # Add metadata
    feature_collection['properties'] = {
        'count': len(features),
        'timestamp': datetime.now().isoformat()
    }
    return feature_collection

# code from https://fastapi-restful.netlify.app/user-guide/repeated-tasks/

def csv_to_json(csvFilePath, jsonFilePath):
    jsonArray = []
    headers = []
    header_row = next(csvFilePath)
    for column in header_row:
        headers.append(column)  
    for row in csvFilePath: 
        #add this python dict to json array
        the_data = {header_row[0]:row[0],
                    header_row[1]:row[1],
                    header_row[2]:row[2]}
        jsonArray.append(the_data)
  
    #convert python jsonArray to JSON String and write to file
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf: 
        jsonString = json.dumps(jsonArray, indent=4)
        jsonf.write(jsonString)
          
csvFilePath = r'data.csv'
jsonFilePath = r'appdata/calendar_dates.json'


lacmta_gtfs_rt_url = "https://lacmta.github.io/lacmta-gtfs/data/calendar_dates.txt"
response = requests.get(lacmta_gtfs_rt_url)

cr = csv.reader(response.text.splitlines())
# csv_to_json(cr,jsonFilePath)

app = FastAPI()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#### Helper functions ####

def get_columns_from_schema(schema):
    if schema == 'trip_updates':
        return schemas.TripUpdates.__fields__.keys()
    if schema == 'vehicle_position_updates':
        return schemas.VehiclePositions.__fields__.keys()


def standardize_string(input_string):
    return input_string.lower().replace(" ", "")

#### End Helper functions ####

####################
#  Begin Update Interval Settings
####################

REALTIME_UDPATE_INTERVAL = 9
STATIC_UDPATE_INTERVAL = 3600
CANCELED_UDPATE_INTERVAL = 3600
GO_PASS_UPDATE_INTERVAL = 3600


####################
#  Begin Routes
####################

#### Begin GTFS-RT Routes ####

@app.get("/{agency_id}/trip_updates", tags=["Real-Time data"])    
async def get_all_trip_updates(agency_id: AgencyIdEnum, async_db: AsyncSession = Depends(get_async_db)):
    """
    Get all trip updates.
    """
    model = models.TripUpdates
    data = await crud.get_all_data_async(async_db, model, agency_id.value)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return data

@app.get("/{agency_id}/trip_updates/{field}/{ids}", tags=["Real-Time data"])    
async def get_trip_updates_by_ids(agency_id: AgencyIdEnum, field: TripUpdatesFieldsEnum, ids: str, format: FormatEnum = Query(FormatEnum.json), async_db: AsyncSession = Depends(get_async_db)):
    """
    Get specific trip updates by IDs dependant on the `field` selected. IDs can be provided as a comma-separated list.
    """
    model = models.TripUpdates
    data = {}
    ids = ids.split(',')
    for id in ids:
        result = await crud.get_data_async(async_db, model, agency_id.value, field.value, id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Data not found for ID {id}")
        if format == FormatEnum.geojson:
            # Convert data to GeoJSON format
            result = to_geojson(result)
        data[id] = result
    return data

@app.get("/{agency_id}/trip_updates/{field}", tags=["Real-Time data"])     
async def get_list_of_field_values(agency_id: AgencyIdEnum, field: TripUpdatesFieldsEnum, async_db: AsyncSession = Depends(get_async_db)):
    """
    Get a list of all values for a specific field in the trip updates.
    """
    model = models.TripUpdates
    data = await crud.get_list_of_unique_values_async(async_db, model, agency_id.value, field.value)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return data

@app.get("/{agency_id}/vehicle_positions", tags=["Real-Time data"])    
async def get_all_vehicle_positions(agency_id: AgencyIdEnum, format: FormatEnum = Query(FormatEnum.json), async_db: AsyncSession = Depends(get_async_db)):
    """
    Get all vehicle positions updates.
    """
    model = models.VehiclePositions
    data = await crud.get_all_data_async(async_db, model, agency_id.value)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    if format == FormatEnum.geojson:
        # Convert data to GeoJSON format
        data = to_geojson(data)
    return data

@app.get("/{agency_id}/vehicle_positions/{field}/{ids}", tags=["Real-Time data"])
async def get_vehicle_positions_by_ids(agency_id: AgencyIdEnum, field: VehiclePositionsFieldsEnum, ids: str, format: FormatEnum = Query(FormatEnum.json), async_db: AsyncSession = Depends(get_async_db)):
    """
    Get specific vehicle position updates by IDs dependant on the `field` selected. IDs can be provided as a comma-separated list.
    """
    model = models.VehiclePositions
    data = {}
    ids = ids.split(',')
    for id in ids:
        result = await crud.get_data_async(async_db, model, agency_id.value, field.value, id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Data not found for ID {id}")
        if format == FormatEnum.geojson:
            # Convert data to GeoJSON format
            result = to_geojson(result)
        data[id] = result
    return data

@app.get("/{agency_id}/vehicle_positions/{field}", tags=["Real-Time data"])
async def get_list_of_field_values(agency_id: AgencyIdEnum, field: VehiclePositionsFieldsEnum, async_db: AsyncSession = Depends(get_async_db)):
    """
    Get a list of all values for a specific field in the vehicle positions updates.
    """
    model = models.VehiclePositions
    data = await crud.get_list_of_unique_values_async(async_db, model, agency_id.value, field.value)
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return data

import json
import asyncio
import aioredis

@app.websocket("/ws/{agency_id}/vehicle_positions")
async def websocket_endpoint(websocket: WebSocket, agency_id: str, async_db: AsyncSession = Depends(get_async_db)):
    await websocket.accept()

    channel = (await crud.redis_connection.subscribe('live_vehicle_positions'))[0]

    async def listen_to_redis():
        async for message in channel.iter(encoding='utf-8'):
            # Unserialize message with json before sending
            message_data = json.loads(message)
            await websocket.send_json(message_data)

    listen_task = asyncio.create_task(listen_to_redis())

    try:
        data = await asyncio.wait_for(crud.get_all_data_async(async_db, models.VehiclePositions, agency_id), timeout=120)
        if data is not None:
            # Serialize data with json before publishing
            data_json = json.dumps(data)
            await crud.redis_connection.publish('live_vehicle_positions', data_json)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out")
    except WebSocketDisconnect:
        # Handle the WebSocket disconnect event
        print("WebSocket disconnected")
    finally:
        listen_task.cancel()
        crud.redis_connection.unsubscribe('live_vehicle_positions')
        crud.redis_connection.close()
        await crud.redis_connection.wait_closed()
@app.websocket("/ws/{agency_id}/vehicle_positions/{field}/{ids}")
async def websocket_vehicle_positions_by_ids(websocket: WebSocket, agency_id: AgencyIdEnum, field: VehiclePositionsFieldsEnum, ids: str, async_db: AsyncSession = Depends(get_async_db)):
    await websocket.accept()
    model = models.VehiclePositions
    ids = ids.split(',')
    try:
        while True:
            data = {}
            for id in ids:
                try:
                    result = await asyncio.wait_for(crud.get_data_async(async_db, model, agency_id.value, field.value, id), timeout=120)
                    if result is not None:
                        data[id] = result
                        # Publish the received data to a Redis channel
                        await crud.redis_connection.publish('live_vehicle_positions_by_ids', data)
                except asyncio.TimeoutError:
                    raise HTTPException(status_code=408, detail="Request timed out")
            if data:
                await asyncio.sleep(5)
                # Subscribe to the Redis channel and send any received messages to the WebSocket client
                ch = await crud.redis_connection.subscribe('live_vehicle_positions_by_ids')
                while await ch.wait_message():
                    message = await ch.get()
                    await websocket.send_json(message)
                # Send a ping every 5 seconds
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        # Handle the WebSocket disconnect event
        print("WebSocket disconnected")

##### todo: Needs to be tested

@app.get("/{agency_id}/trip_detail/route_code/{route_code}",tags=["Real-Time data"])
async def get_trip_detail_by_route_code(agency_id: AgencyIdEnum, route_code: str, geojson:bool=False, db: AsyncSession = Depends(get_db)):
    result = await crud.get_gtfs_rt_vehicle_positions_trip_data_by_route_code(session=db, route_code=route_code, geojson=geojson, agency_id=agency_id.value)
    return result

@app.get("/{agency_id}/trip_detail/vehicle/{vehicle_id?}", tags=["Real-Time data"])
async def get_trip_detail_by_vehicle(agency_id: AgencyIdEnum, vehicle_id: Optional[str] = None, operation: OperationEnum = Depends(), geojson: bool = False, async_db: AsyncSession = Depends(get_async_db)):
    if operation == OperationEnum.ALL:
        result = await crud.get_all_data_async(async_db, models.VehiclePositions, operation.value)
        return result
    if vehicle_id:
        multiple_values = vehicle_id.split(',')
        if len(multiple_values) > 1:
            result_array = []
            for value in multiple_values:
                temp_result = await crud.get_data_async(async_db, models.VehiclePositions, 'vehicle_id', value)
                if len(temp_result) == 0:
                    temp_result = { "message": "field_value '" + value + "' not found in field_name '" + value + "'" }
                result_array.append(temp_result)
            return result_array
        else:
            result = await crud.get_data_async(async_db, models.VehiclePositions, 'vehicle_id', vehicle_id)
        return result
    return {"message": "No vehicle_id provided"}


@app.get("/{agency_id}/trip_detail/route/{route_code?}", tags=["Real-Time data"])
async def get_trip_detail_by_route(agency_id: AgencyIdEnum, route_code: Optional[OperationEnum] = None, geojson: bool = False, async_db: AsyncSession = Depends(get_async_db)):
    if route_code == OperationEnum.ALL:
        result = await crud.get_all_data_async(async_db, models.VehiclePositions, route_code.value)
        return result
    elif route_code:
        result = await crud.get_data_async(async_db, models.VehiclePositions, 'route_code', route_code.value)
        return result
    return {"message": "No route_code provided"}

###------------ End todo: Needs to be tested--------------

#### END GTFS-RT Routes ####


@app.get("/canceled_service_summary",tags=["Canceled Service Data"])
async def get_canceled_trip_summary(db: AsyncSession = Depends(get_async_db)):
    result = await crud.get_canceled_trips(db,'all')
    canceled_trips_summary = {}
    total_canceled_trips = 0
    canceled_trip_json = jsonable_encoder(result)
    if canceled_trip_json is None:
        return {"canceled_trips_summary": "",
                "total_canceled_trips": 0,
                "last_update": ""}
    else:
        for trip in canceled_trip_json:
            route_number = standardize_string(trip["trp_route"])
            if route_number:
                if route_number not in canceled_trips_summary:
                    canceled_trips_summary[route_number] = 1
                else:
                    canceled_trips_summary[route_number] += 1
                total_canceled_trips += 1
        update_time = canceled_trip_json[0]['LastUpdateDate']
        return {"canceled_trips_summary":canceled_trips_summary,
                "total_canceled_trips":total_canceled_trips,
                "last_updated":update_time}

@app.get("/canceled_service/line/{line}",tags=["Canceled Service Data"])
async def get_canceled_trip(db: Session = Depends(get_db),line: str = None):
    result = crud.get_canceled_trips(db,line)
    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

@app.get("/canceled_service/all",tags=["Canceled Service Data"])
async def get_canceled_trip(db: Session = Depends(get_db)):
    result = crud.get_canceled_trips(db,'all')
    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

### GTFS Static data ###
@app.get("/{agency_id}/route_stops/{route_code}",tags=["Static data"])
async def populate_route_stops(agency_id: AgencyIdEnum,route_code:str, daytype: DayTypesEnum = DayTypesEnum.all, db: Session = Depends(get_db)):
    result = crud.get_gtfs_route_stops(db,route_code,daytype.value,agency_id.value)
    json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

@app.get("/{agency_id}/route_stops_grouped/{route_code}",tags=["Static data"])
async def populate_route_stops_grouped(agency_id: AgencyIdEnum,route_code:str, db: Session = Depends(get_db)):
    result = crud.get_gtfs_route_stops_grouped(db,route_code,agency_id.value)
    json_compatible_item_data = jsonable_encoder(result[0])
    return JSONResponse(content=json_compatible_item_data)

@app.get("/calendar_dates",tags=["Static data"])
async def get_calendar_dates_from_db(db: Session = Depends(get_db)):
    result = crud.get_calendar_dates(db)
    calendar_dates = jsonable_encoder(result)
    return JSONResponse(content={"calendar_dates":calendar_dates})

@app.get("/{agency_id}/stop_times/route_code/{route_code}",tags=["Static data"],response_model=Page[schemas.StopTimes])
async def get_stop_times_by_route_code_and_agency(agency_id: AgencyIdEnum,route_code, db: Session = Depends(get_db)):
    result = crud.get_stop_times_by_route_code(db,route_code,agency_id.value)
    return result


@app.get("/{agency_id}/stop_times/trip_id/{trip_id}",tags=["Static data"],response_model=Page[schemas.StopTimes])
async def get_stop_times_by_trip_id_and_agency(agency_id: AgencyIdEnum,trip_id, db: Session = Depends(get_db)):
    result = crud.get_stop_times_by_trip_id(db,trip_id,agency_id.value)
    return result

@app.get("/{agency_id}/stops/{stop_id}",tags=["Static data"])
async def get_stops(agency_id: AgencyIdEnum,stop_id, db: Session = Depends(get_db)):
    result = crud.get_stops_id(db,stop_id,agency_id.value)
    return result

@app.get("/{agency_id}/trips/{trip_id}",tags=["Static data"])
async def get_bus_trips(agency_id: AgencyIdEnum,trip_id, db: Session = Depends(get_db)):
    result = crud.get_trips_data(db,trip_id,agency_id.value)
    return result

@app.get("/{agency_id}/shapes/{shape_id}",tags=["Static data"])
async def get_shapes(agency_id: AgencyIdEnum,shape_id, geojson: bool = False,db: Session = Depends(get_db)):
    if shape_id == "list":
        result = crud.get_trip_shapes_list(db,agency_id.value)
    else:
        result = crud.get_shape_by_id(db,geojson,shape_id,agency_id.value)
    return result

@app.get("/{agency_id}/trip_shapes/{shape_id}",tags=["Static data"])
async def get_trip_shapes(agency_id: AgencyIdEnum,shape_id, db: Session = Depends(get_db)):
    if shape_id == "all":
        result = crud.get_trip_shapes_all(db,agency_id.value)
    elif shape_id == "list":
        result = crud.get_trip_shapes_list(db,agency_id.value)
    else: 
        result = crud.get_trip_shape(db,shape_id,agency_id.value)
    return result

@app.get("/{agency_id}/calendar/{service_id}",tags=["Static data"])
async def get_calendar_list(agency_id: AgencyIdEnum,service_id, db: Session = Depends(get_db)):
    if service_id == "list":
        result = crud.get_calendar_list(db,agency_id.value)
    else:
        result = crud.get_gtfs_static_data(db,models.Calendar,'service_id',service_id,agency_id.value)
    return result


@app.get("/{agency_id}/calendar/{service_id}",tags=["Static data"])
async def get_calendar(agency_id: AgencyIdEnum,service_id, db: Session = Depends(get_db)):
    result = crud.get_calendar_data_by_id(db,models.Calendar,service_id,agency_id.value)
    return result

@app.get("/{agency_id}/routes/{route_id}",tags=["Static data"])
async def get_routes(agency_id: AgencyIdEnum,route_id, db: Session = Depends(get_db)):
    result = crud.get_routes_by_route_id(db,route_id,agency_id.value)
    return result

@app.get("/{agency_id}/route_overview", tags=["Static data"])
async def get_route_overview(agency_id: AllAgencyIdEnum, async_db: AsyncSession = Depends(get_async_db)):
    """
    Get route overview data for all routes.
    """
    model = models.RouteOverview
    if agency_id == AllAgencyIdEnum.all:
        results = []
        for agency in AllAgencyIdEnum:
            result = await crud.get_all_data_async(async_db, model, agency.value)
            if result is not None:
                results.append(result)
        if not results:
            raise HTTPException(status_code=404, detail="Data not found")
        return results
    else:
        result = await crud.get_all_data_async(async_db, model, agency_id.value)
        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")
        return result

@app.get("/{agency_id}/route_overview/{route_code}", tags=["Static data"])
async def get_route_overview_by_route_code(agency_id: AgencyIdEnum, route_code: str, async_db: AsyncSession = Depends(get_async_db)):
    """
    Get route overview data by route code.
    """
    model = models.RouteOverview
    if route_code.lower() == 'all':
        # Return all routes
        result = await crud.get_all_data_async(async_db, model, agency_id.value)
    elif route_code.lower() == 'list':
        # Return a list of route codes
        result = await crud.get_list_of_unique_values_async(async_db, model, 'route_code', agency_id.value)
    else:
        # Return data for a specific route code
        result = await crud.get_data_async(async_db, model, agency_id.value, 'route_code', route_code)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Data not found for route code {route_code}")
    return result

@app.get("/{agency_id}/agency/",tags=["Static data"])
async def get_agency(agency_id: AgencyIdEnum, db: Session = Depends(get_db)):
    result = crud.get_agency_data(db,models.Agency,agency_id.value)
    return result

#### END GTFS Static data endpoints ####
#### END Static data endpoints ####


#### Begin Other data endpoints ####

@app.get("/get_gopass_schools",tags=["Other data"])
async def get_gopass_schools(db: AsyncSession = Depends(get_async_db), show_missing: bool = False, combine_phone:bool = False, groupby_column:GoPassGroupEnum = None):
    if combine_phone == True:
        result = await crud.get_gopass_schools_combined_phone(db, groupby_column.value)
        return result
    else:
        result = await crud.get_gopass_schools(db, show_missing)
        json_compatible_item_data = jsonable_encoder(result)
    return JSONResponse(content=json_compatible_item_data)

@app.get("/time")
async def get_time():
    current_time = datetime.now()
    return {current_time}

# @app.get("/agencies/")
# async def root():


@app.get("/",response_class=HTMLResponse)
def index(request:Request):
    # return templates.TemplateResponse("index.html",context={"request":request})
    human_readable_default_update = None
    try:
        default_update = datetime.fromtimestamp(Config.API_LAST_UPDATE_TIME)
        default_update = default_update.astimezone(pytz.timezone("America/Los_Angeles"))
        human_readable_default_update = default_update.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        logger.exception(type(e).__name__ + ": " + str(e), exc_info=False)
    
    return templates.TemplateResponse("index.html", context= {"request": request,"current_api_version":Config.CURRENT_API_VERSION,"update_time":human_readable_default_update})

### Misc routes

# tokens

@app.get("/login",response_class=HTMLResponse,tags=["User Methods"])
def login(request:Request):
    return templates.TemplateResponse("login.html", context= {"request": request})


@app.get("/verify_email/{email_verification_token}", tags=["User Methods"])
async def verify_email_route(email_verification_token: str,db: Session = Depends(get_db)):
    
    if not crud.verify_email(email_verification_token,db):
        return False

    return "email verified"

@app.post("/token", response_model=schemas.Token,tags=["User Methods"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    user = crud.authenticate_user(form_data.username, form_data.password,db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/openapi.yaml', include_in_schema=False)
@functools.lru_cache()
def read_openapi_yaml() -> Response:
    openapi_json= app.openapi()
    openapi_json['servers'] = [{"url": "https://api.metro.net","description": "Production Server"},{"url": "https://dev-metro-api-v2.ofhq3vd1r7une.us-west-2.cs.amazonlightsail.com/","description": "Development Server"}]
    yaml_s = io.StringIO()
    yaml.dump(openapi_json, yaml_s)
    return Response(yaml_s.getvalue(), media_type='text/yaml')


# end tokens


@app.post("/users/", response_model=schemas.User,tags=["User Methods"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/{username}", response_model=schemas.User,tags=["User Methods"])
def read_user(username: str, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/routes", response_model=List[str])
async def get_all_routes():
    return [route.path for route in app.routes]

def setup_logging():
    try:
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_error_logger = logging.getLogger("uvicorn.error")
        logger = logging.getLogger("uvicorn.app")
        logzio_formatter = logging.Formatter("%(message)s")
        logzio_uvicorn_access_handler = LogzioHandler(Config.LOGZIO_TOKEN, 'uvicorn.access', 5, Config.LOGZIO_URL)
        logzio_uvicorn_access_handler.setLevel(logging.WARNING)
        logzio_uvicorn_access_handler.setFormatter(logzio_formatter)

        logzio_uvicorn_error_handler = LogzioHandler(Config.LOGZIO_TOKEN, 'uvicorn.error', 5, Config.LOGZIO_URL)
        logzio_uvicorn_error_handler.setLevel(logging.WARNING)
        logzio_uvicorn_error_handler.setFormatter(logzio_formatter)

        logzio_app_handler = LogzioHandler(Config.LOGZIO_TOKEN, 'fastapi.app', 5, Config.LOGZIO_URL)
        logzio_app_handler.setLevel(logging.WARNING)
        logzio_app_handler.setFormatter(logzio_formatter)

        uvicorn_access_logger.addHandler(logzio_uvicorn_access_handler)
        uvicorn_error_logger.addHandler(logzio_uvicorn_error_handler)
        logger.addHandler(logzio_app_handler)

        uvicorn_access_logger.addFilter(LogFilter())
        uvicorn_error_logger.addFilter(LogFilter())
        logger.addFilter(LogFilter())
    except Exception as e:
        print(f"Failed to set up logging: {e}")

class RedisNotConnected(Exception):
    """Raised when Redis is not connected"""
    pass
@app.on_event("startup")
async def startup_event():
    try:
        crud.redis_connection = crud.initialize_redis()
        setup_logging()
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        raise e
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
add_pagination(app)
