from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float,PrimaryKeyConstraint,JSON
from sqlalchemy.orm import class_mapper

from geoalchemy2 import *
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from shapely.geometry import mapping
from . import schemas

from .gtfs_models import *

from .database import Base

class BaseModel(Base):
    __abstract__ = True

    def to_dict(self):
        return {c.key: self.handle_type(c) for c in self.__table__.columns}

    def handle_type(self, column):
        data = getattr(self, column.key)
        if isinstance(data, WKBElement):
            return mapping(to_shape(data))
        return data

class Agency(Base):
    __tablename__ = "agency"
    agency_id = Column(String, primary_key=True, index=True)
    agency_name = Column(String)
    agency_url = Column(String)
    agency_timezone = Column(String)
    agency_lang = Column(String)
    agency_phone = Column(String)

class Calendar(Base):
    __tablename__ = "calendar"
    service_id = Column(String, primary_key=True, index=True)
    monday = Column(Integer)
    tuesday = Column(Integer)
    wednesday = Column(Integer)
    thursday = Column(Integer)
    friday = Column(Integer)
    saturday = Column(Integer)
    sunday = Column(Integer)
    start_date = Column(Integer)
    end_date = Column(Integer)
    agency_id = Column(String)

class CalendarDates(Base):
    __tablename__ = "calendar_dates"
    service_id = Column(String, primary_key=True, index=True)
    agency_id = Column(String)
    date = Column(String)
    exception_type = Column(Integer)
    agency_id = Column(String)

class StopTimes(Base):
    __tablename__ = "stop_times"
    arrival_time = Column(String)
    departure_time = Column(String)
    stop_id = Column(Integer, index=True)
    stop_sequence = Column(Integer,primary_key=True, index=True)
    stop_headsign = Column(String)
    pickup_type = Column(Integer)
    drop_off_type = Column(Integer)
    trip_id_event = Column(String,index=True)
    route_code = Column(Integer,index=True)
    destination_code = Column(String,index=True)
    timepoint = Column(Integer)
    bay_num = Column(Integer)
    agency_id = Column(String)
    trip_id = Column(Integer, primary_key=True,index=True)
    rider_usage_code = Column(Integer)

class Stops(Base):
    __tablename__ = "stops"
    stop_id = Column(Integer, primary_key=True, index=True)
    stop_code = Column(Integer)
    stop_name = Column(String)
    stop_desc = Column(String)
    stop_lat = Column(Float)
    stop_lon = Column(Float)
    geometry = Column(Geometry('POINT', srid=4326))
    stop_url = Column(String)
    location_type = Column(String)
    parent_station = Column(String)
    tpis_name = Column(String)
    agency_id = Column(String)


class Routes(Base):
    __tablename__ = "routes"
    route_id = Column(Integer, primary_key=True, index=True)
    route_short_name = Column(String)
    route_long_name = Column(String)
    route_desc = Column(String)
    route_type = Column(Integer)
    route_color = Column(String)
    route_text_color = Column(String)
    route_url = Column(String)
    agency_id = Column(String)

class RouteOverview(Base):
    __tablename__ = "route_overview"
    route_id = Column(Integer, primary_key=True, index=True)
    route_code = Column(String)
    route_code_padded= Column(Integer)
    route_short_name = Column(String)
    route_long_name = Column(String)
    route_desc = Column(String)
    route_type = Column(Integer)
    route_color = Column(String)
    route_text_color = Column(String)
    route_url = Column(String)
    agency_id = Column(String)
    line_id = Column(String)
    alt_id = Column(String)
    long_name = Column(String)
    description = Column(String)
    pdf_file_url = Column(String)
    pdf_file_link = Column(String)
    iconography_url = Column(String)
    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}
# route stops: route_id,stop_id,day_type,stop_sequence,direction_id,stop_name,coordinates,departure_times
class RouteStops(Base):
    __tablename__ = "route_stops"
    route_id = Column(String, primary_key=True)
    route_code = Column(String, index=True)
    day_type = Column(String,primary_key=True)
    stop_id = Column(Integer)
    stop_sequence = Column(Integer, primary_key=True)
    direction_id = Column(Integer, primary_key=True)
    stop_name = Column(String)
    geojson = Column(String)
    geometry = Column(Geometry('POINT', srid=4326))
    departure_times = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    agency_id = Column(String)

class RouteStopsGrouped(Base):
    __tablename__ = "route_stops_grouped"
    route_code = Column(String,primary_key=True, index=True)
    payload = Column(JSON)
    agency_id = Column(String)

class TripShapes(Base):
    __tablename__ = "trip_shapes"
    shape_id = Column(String, primary_key=True, index=True)
    geometry = Column(Geometry('LINESTRING', srid=4326))
    agency_id = Column(String)

class Shapes(Base):
    __tablename__ = "shapes"
    shape_id_sequence = Column(String, primary_key=True, index=True)
    shape_id = Column(String)
    shape_pt_lat = Column(Float)
    shape_pt_lon = Column(Float)
    geometry = Column(Geometry('POINT', srid=4326))
    shape_pt_sequence = Column(Integer)
    agency_id = Column(String)
    

class Trips(Base):
    __tablename__ = "trips"
    route_id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String)
    trip_id = Column(String, index=True)
    trip_headsign = Column(String)
    direction_id = Column(Integer, index=True)
    block_id = Column(Integer)
    shape_id = Column(String)
    trip_id_event = Column(String)
    agency_id = Column(String)
    
#### end gtfs static models

#### begin other models

class GoPassSchools(Base):
    __tablename__ = "go_pass_schools"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String)
    participating = Column(Boolean)
    school = Column(String)
    district = Column(String)
    address = Column(String)
    notes = Column(String)
    resolved = Column(Boolean)

class CanceledServices(Base):
    __tablename__ = "canceled_service"
    dpce_date = Column(String)
    dpce_assign_id = Column(String)
    dpce_block_disp = Column(String)
    pce_time_start = Column(String)
    pce_time_end = Column(String)
    pce_duration = Column(String)
    dpce_reason_canc = Column(String)
    pce_commentary = Column(String)
    trp_number = Column(String)
    trp_int_number = Column(String, primary_key=True, index=True)
    m_metro_export_trip_id = Column(String)
    m_gtfs_trip_id = Column(String)
    trp_route = Column(String)
    trp_direction = Column(String)
    trp_type = Column(String)
    stop_description_first = Column(String)
    trp_time_start = Column(String)
    trp_time_end = Column(String)
    stop_description_last = Column(String)
    trp_block = Column(String)
    trp_duration = Column(String)
    trp_distance = Column(String)
    dty_number = Column(String)
    pce_number = Column(String)
    dty_type = Column(String)
    oa_pce_orb_number = Column(String)
    blk_orb_number = Column(String)
    trp_time_start_hour = Column(String)
    CostCenter = Column(String)
    blk_garage = Column(String)
    LastUpdateDate = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    email_token = Column(String)
    api_token = Column(String)
    hashed_password = Column(String)
    is_email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)


### GTFS-RT models

# classes for the GTFS-realtime data
# TripUpdate
# StopTimeUpdate
# VehiclePosition

class TripUpdates(BaseModel):
    __tablename__ = 'trip_updates'
    # This replaces the TripDescriptor message
    # TODO: figure out the relations
    trip_id = Column(String(64),primary_key=True,index=True)
    route_id = Column(String(64))
    start_time = Column(String(8))
    start_date = Column(String(10))
    # Put in the string value not the enum
    # TODO: add a domain
    schedule_relationship = Column(String(9))
    direction_id = Column(Integer)

    agency_id = Column(String)
    # moved from the header, and reformatted as datetime
    timestamp = Column(Integer)
    stop_time_json = Column(String)
    stop_time_updates = relationship('StopTimeUpdates', backref=backref('trip_updates',lazy="joined"))


    class Config:
        schema_extra = {
            "definition": {
                "comment": 
                """
                # Metro's bus agency id is "LACMTA"
                # Metro's rail agency id is "LACMTA METRO
                """
            }
        }

class StopTimeUpdates(BaseModel):
    __tablename__ = 'stop_time_updates'
    stop_sequence = Column(Integer)
    stop_id = Column(String(10),primary_key=True,index=True)
    trip_id = Column(String, ForeignKey('trip_updates.trip_id'))
    arrival = Column(Integer)
    departure = Column(Integer)
    agency_id = Column(String)
    route_code = Column(String)
    start_time = Column(String)
    start_date = Column(String)
    direction_id = Column(Integer)
    vehicle_id = Column(String)
    schedule_relationship = Column(Integer)

class VehiclePositions(BaseModel):
    __tablename__ = "vehicle_position_updates"
    current_stop_sequence = Column(Integer)
    current_status = Column(String)
    timestamp = Column(Integer)
    stop_id = Column(String)
    trip_id = Column(String)
    trip_start_date = Column(String)
    trip_route_id = Column(String)
    route_code = Column(String)
    position_latitude = Column(Float)
    position_longitude = Column(Float)
    position_bearing = Column(Float)
    position_speed = Column(Float)
    geometry = Column(Geometry('POINT', srid=4326))
    vehicle_id = Column(String, primary_key=True)
    vehicle_label = Column(String)
    agency_id = Column(String)
    timestamp = Column(Integer)
# So one can loop over all classes to clear them for a new load (-o option)
GTFSRTSqlAlchemyModels = {
    schemas.TripUpdates: TripUpdates,
    schemas.StopTimeUpdates: StopTimeUpdates,
    schemas.VehiclePositions: VehiclePositions,
}
GTFSRTClasses = (TripUpdates, StopTimeUpdates, VehiclePositions)
