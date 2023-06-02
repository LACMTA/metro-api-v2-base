# gtfs_rt.py: the database model for loading gtfs-realtime data to a database

import enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Float, MetaData,Enum
# from sqlalchemy.dialects.postgresql import ARRAY,JSON
from sqlalchemy.orm import relationship, backref
from geoalchemy2 import *

from config import Config
GTFSrtBase = declarative_base(metadata=MetaData(schema=Config.TARGET_DB_SCHEMA))

class VehicleStopStatus(enum.Enum):
    INCOMING_AT = 0
    STOPPED_AT = 1
    IN_TRANSIT_TO = 2

# classes for the GTFS-realtime data
# TripUpdate
# StopTimeUpdate
# VehiclePosition

class StopTimeUpdate(GTFSrtBase):
    __tablename__ = 'stop_time_updates'
    # oid = Column(Integer, )

    # TODO: Fill one from the other
    stop_sequence = Column(Integer,default='')
    stop_id = Column(String(10),primary_key=True)
    agency_id = Column(String)

    route_code = Column(String)
    start_time = Column(String)
    start_date = Column(String)
    direction_id = Column(Integer)
    
    # TODO: Add domain
    schedule_relationship = Column(String(9))
    # Link it to the TripUpdate
    trip_id = Column(String, ForeignKey('trip_updates.trip_id'))

class TripUpdate(GTFSrtBase):
    __tablename__ = 'trip_updates'
    # oid = Column(Integer, primary_key=True)

    # This replaces the TripDescriptor message
    # TODO: figure out the relations
    trip_id = Column(String(64), primary_key=True)
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
    stop_time_updates = relationship('StopTimeUpdate', backref=backref('trip_updates',lazy="joined"))
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


class VehiclePosition(GTFSrtBase):
    __tablename__ = "vehicle_position_updates"

    # Vehicle information
    current_stop_sequence = Column(Integer)
    current_status = Column(String)
    timestamp = Column(Integer)
    stop_id = Column(String)

    # Collapsed Vehicle.trip
    trip_id = Column(String)
    trip_start_date = Column(String)
    trip_route_id = Column(String)
    route_code = Column(String)
    # trip_direction_id = Column(Integer)

    # Collapsed Vehicle.Position
    position_latitude = Column(Float)
    position_longitude = Column(Float)
    geom = Column(Geometry('POINT', srid=4326))
    position_bearing = Column(Float)
    position_speed = Column(Float)

    # collapsed Vehicle.Vehicle
    vehicle_id = Column(String,primary_key=True)
    vehicle_label = Column(String)
    agency_id = Column(String)

    timestamp = Column(Integer)


# So one can loop over all classes to clear them for a new load (-o option)
AllClasses = (TripUpdate, StopTimeUpdate, VehiclePosition)
