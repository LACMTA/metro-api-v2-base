from typing import Optional,get_type_hints, Type
from pydantic import BaseModel, Json, ValidationError,validator

from .config import Config

from enum import Enum

def create_model_fields_enum(model: Type[BaseModel]) -> Type[Enum]:
    # Create a new Enum class
    class ModelFieldsEnum(str, Enum):
        # Get the field names from the model
        fields = {f: f for f in get_type_hints(model).keys()}

        # Create an Enum member for each field
        for field in fields:
            locals()[field] = field

    # Return the new Enum class
    return ModelFieldsEnum

class Agency(BaseModel):
    agency_id: str
    agency_name: str
    agency_url: str
    agency_timezone: str
    agency_lang: str
    agency_phone: str

class Calendar(BaseModel):
    service_id: str
    monday: int
    tuesday: int
    wednesday: int
    thursday: int
    friday: int
    saturday: int
    sunday: int
    start_date: int
    end_date: int
    agency_id: str
class CalendarDates(BaseModel):
    service_id: str
    date: str
    exception_type: int
    agency_id: str
    
class CanceledServiceData(BaseModel):
    gtfs_trip_id: str
    trip_route: str
    stop_description_first: str
    stop_description_last: str
    trip_time_start: str
    trip_time_end: str
    trip_direction: str
    agency_id: str

class StopTimes(BaseModel):
    trip_id: str
    arrival_time: str
    departure_time: str
    stop_id: int
    stop_sequence: int
    stop_headsign: str
    pickup_type: int
    drop_off_type: int
    trip_id_event: str
    route_code: int
    destination_code: str
    timepoint: int
    bay_num: int
    agency_id: str
    rider_usage_code: int

class Stops(BaseModel):
    stop_id: int
    stop_code: int
    stop_name: str
    stop_desc: str
    stop_lat: float
    stop_lon: float
    stop_url: str
    location_type: str
    parent_station: str
    tpis_name: str
    agency_id: str
    geometry: str

class Routes(BaseModel):
    route_id: int
    route_short_name: str
    route_long_name: str
    route_desc: str
    route_type: int
    agency_id: str

class RouteStops(BaseModel):
    route_code: str
    route_id: str
    stop_id: int
    day_type: str
    stop_sequence: int
    direction_id: int
    stop_name: str
    geojson: Json
    agency_id: str
    departure_times: str
    latitude: float
    longitude: float
    geometry: str

class RouteStopsGrouped(BaseModel):
    route_code: str
    payload: Json
    agency_id: str

class TripShapes(BaseModel):
    shape_id: str
    geometry: str
    agency_id: str
    
class Shapes(BaseModel):
    shape_id: str
    shape_pt_lat: float
    shape_pt_lon: float
    shape_pt_sequence: int
    agency_id: str
    geometry: str
    shape_id_sequence: str

class StopTimeUpdates(BaseModel):
    stop_sequence: int
    trip_id: str
    stop_id: str
    arrival_time: str
    departure_time: str
    schedule_relationship: str
    agency_id: str
    class Config:
        orm_mode = True
    # oid: int
    # trip_update_id: int

class Trips(BaseModel):
    route_id: int
    service_id: str
    trip_id: str
    trip_headsign: str
    direction_id: int
    block_id: int
    shape_id: str
    trip_id_event: str
    agency_id: str

class TripUpdates(BaseModel):
    trip_id: str
    route_id: str
    start_time: str
    start_date: str
    schedule_relationship: str
    direction_id: int
    timestamp: int
    agency_id: str
    stop_time_json: Json
    stop_time_updates: StopTimeUpdates
    class Config:
        orm_mode = True
class VehiclePositions(BaseModel):
    current_stop_sequence: int
    current_status: str
    timestamp: int
    stop_id: str
    trip_id: str
    trip_start_date: str
    trip_route_id: str
    route_code: str

    position_latitude: float
    position_longitude: float
    position_bearing: float
    position_speed: float

    direction_id: int

    vehicle_id: str
    vehicle_label: str
    id: int
    agency_id: str
    timestamp: int
    geometry: str

class GoPassSchools(BaseModel):
    phone: str
    participating: bool
    school: str
    district: str
    address: str
    notes: str
    resolved: bool

class CanceledServices(BaseModel):
    dpce_date: str
    dpce_assign_id: str
    dpce_block_disp: str
    pce_time_start: str
    pce_time_end: str
    pce_duration: str
    dpce_reason_canc: str
    pce_commentary: str
    trp_number: str
    trp_int_number: str
    m_metro_export_trip_id: str
    m_gtfs_trip_id: str
    trp_route: str
    trp_direction: str
    trp_type: str
    stop_description_first: str
    trp_time_start: str
    trp_time_end: str
    stop_description_last: str
    trp_block: str
    trp_duration: str
    trp_distance: str
    dty_number: str
    pce_number: str
    dty_type: str
    oa_pce_orb_number: str
    blk_orb_number: str
    trp_time_start_hour: str
    CostCenter: str
    blk_garage: str
    LastUpdateDate: str




class EmailVerifyToken(BaseModel):
    email_address: str
    # email_token: str
    # token_type: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    username: str
    password: str
    # email_token: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: str

