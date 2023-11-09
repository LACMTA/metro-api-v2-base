# gtfsrdb.py: load gtfs-realtime data to a database

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Float, MetaData
from sqlalchemy.orm import relationship, backref

from geoalchemy2 import *
# from sqlalchemy.dialects.postgresql import JSON
from .config import Config
from .database import Base

GTFSrtBase = declarative_base(metadata=MetaData(schema=Config.TARGET_DB_SCHEMA))

# classes for the GTFS-realtime data
# TripUpdate
# StopTimeUpdate
# VehiclePosition

class TripUpdate(GTFSrtBase):
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

class StopTimeUpdate(GTFSrtBase):
    __tablename__ = 'stop_time_updates'
    # oid = Column(Integer, )

    # TODO: Fill one from the other
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

    # TODO: Add domain
    schedule_relationship = Column(Integer)
    
    # Link it to the TripUpdate
    # trip_id = Column(Integer,)

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
    # trip_direction_id = Column(Integer)
    route_code = Column(String)
    
    # Collapsed Vehicle.Position
    position_latitude = Column(Float)
    position_longitude = Column(Float)
    position_bearing = Column(Float)
    position_speed = Column(Float)
    geometry = Column(Geometry('POINT', srid=4326))

    # collapsed Vehicle.Vehicle
    vehicle_id = Column(String,primary_key=True,index=True)
    vehicle_label = Column(String)

    agency_id = Column(String)
    timestamp = Column(Integer)
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if getattr(self, c.name) is not None}
# So one can loop over all classes to clear them for a new load (-o option)
AllClasses = (TripUpdate, StopTimeUpdate, VehiclePosition)
