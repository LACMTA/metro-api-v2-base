import json
import pandas as pd
import numpy as np
from geoalchemy2 import functions,shape
from shapely.geometry import Point
from shapely import geometry as geo
class JsonReturn(dict):
    def __str__(self):
        # data = list(self.items())
        # array = np.array(data)
        # df = pd.DataFrame(array)
        # return df.to_json(self)
        return json.dumps(self)


def trip_update_reformat(row):
    result_row = {}
    result_row['id'] = row.trip_id
    trip_update = {}    
    trip_update['timestamp'] = row.timestamp

    trip = {}
    row.trip_assigned = False
    if row.trip_id:
        trip['trip_id'] = row.trip_id
        row.trip_assigned = True
    if row.start_time:
        trip['start_time'] = row.start_time
    if row.start_date:
        trip['start_date'] = row.start_date
    trip['schedule_relationship'] = get_readable_schedule_relationship(row.schedule_relationship)
    if row.route_id:
        trip['route_id'] = row.route_id
    if row.direction_id:
        trip['direction_id'] = row.direction_id
    trip_update['trip'] = trip

    stop_time_updates = []
    
    if row.stop_time_json:
        clean_stop_time_json = row.stop_time_json.replace("'", '"')
        for stop_time in json.loads(clean_stop_time_json):
            this_stop_time = {}
            if stop_time['stop_sequence']:
                this_stop_time['stop_sequence'] = stop_time['stop_sequence']
            if stop_time['arrival']:
                arrival = {}
                arrival['time'] = stop_time['arrival']
                this_stop_time['arrival'] = arrival
            if stop_time['departure']:
                departure = {}
                departure['time'] = stop_time['departure']
                this_stop_time['departure'] = departure
                this_stop_time['departure']['time'] = stop_time['departure']
            if stop_time['schedule_relationship']:
                this_stop_time['schedule_relationship'] = get_readable_schedule_relationship(stop_time['schedule_relationship'])
            if stop_time['stop_id']:
                this_stop_time['stop_id'] = stop_time['stop_id']
            stop_time_updates.append(this_stop_time)
    trip_update['stop_time_updates'] = stop_time_updates
    result_row['trip_update'] = trip_update
    return result_row

def vehicle_position_reformat(row,geojson=False):
        trip_info = {}
        vehicle_info = {}
        position_info = {}
        geojson_row = {}
        properties = {}
        row.current_status = get_readable_status(row.current_status)
        if row.trip_id:
            trip_info['trip_id'] = row.trip_id
            del row.trip_id
        if row.trip_route_id:
            trip_info['route_id'] = row.trip_route_id
            del row.trip_route_id
        if row.trip_start_date:
            trip_info['trip_start_date'] = row.trip_start_date
            del row.trip_start_date      
        if row.vehicle_id:
            vehicle_info['vehicle_id'] = row.vehicle_id
            del row.vehicle_id
        if row.vehicle_label:
            vehicle_info['vehicle_label'] = row.vehicle_label
            del row.vehicle_label
        if row.position_latitude:
            position_info['latitude'] = row.position_latitude
            del row.position_latitude
        if row.position_longitude:
            position_info['longitude'] = row.position_longitude
            del row.position_longitude
        if row.position_bearing:
            position_info['bearing'] = row.position_bearing
            del row.position_bearing
        if row.timestamp:
            position_info['timestamp'] = row.timestamp
            del row.timestamp
        if row.position_speed:
            position_info['speed'] = row.position_speed
            del row.position_speed
        if row.geometry:
            try:
                row.geometry = JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            except:
                row.geometry = [row.position_longitude,row.position_latitude]
        if geojson == True:
            geojson_row['type'] = 'Feature'
            if row.geometry:
                try:
                    geojson_row['geometry'] = row.geometry
                except:
                    geojson_row['geometry'] = [row.position_longitude,row.position_latitude]
                geojson_row['lineString'] = convert_geometry_to_line_string(row.geometry)
            properties['trip'] = trip_info
            properties['vehicle'] = vehicle_info
            properties['position'] = position_info
            properties['current_status'] = row.current_status
            geojson_row['properties'] = properties
            return geojson_row
        row.trip = trip_info
        row.vehicle = vehicle_info
        row.position = position_info

        return row
def convert_geometry_to_line_string(geometry):
    if geometry:
        if geometry['type'] == 'Point':
            return Point(geometry['coordinates']).wkt
        if geometry['type'] == 'LineString':
            return geo.LineString(geometry['coordinates']).wkt
        if geometry['type'] == 'MultiLineString':
            return geo.MultiLineString(geometry['coordinates']).wkt

def vehicle_position_reformat_for_trip_details(row,geojson=False):
        trip_info = {}
        position_info = {}

        geojson_row = {}
        properties = {}
        row.current_status = get_readable_status(row.current_status)
        row.trip_assigned = False
        # if row.trip_id:
        #     row.trip_assigned = True
        if row.trip_route_id:
            del row.trip_route_id 
        if row.vehicle_id:
            del row.vehicle_id
        if row.position_latitude:
            position_info['latitude'] = row.position_latitude
            del row.position_latitude
        if row.position_longitude:
            position_info['longitude'] = row.position_longitude
            del row.position_longitude
        if row.position_bearing:
            del row.position_bearing
        if row.position_speed:
            del row.position_speed
        if row.geometry:
            try:
                row.geometry = JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            except:
                row.geometry = None

        if geojson == True:
            geojson_row['type'] = 'Feature'
            if row.geometry:
                geojson_row['geometry'] = row.geometry
                geojson_row['lineString'] = convert_geometry_to_line_string(row.geometry)
            properties['trip'] = trip_info
            properties['position'] = position_info
            properties['current_status'] = row.current_status
            geojson_row['properties'] = properties
            return geojson_row
        # row.trip = trip_info
        row.position = position_info
        return row

def vehicle_position_reformat_for_trip_details_for_async(row,geojson=False):
        new_row = {}
        trip_info = {}
        position_info = {}
        geojson_row = {}
        properties = {}
        if hasattr(row, 'current_status'):
            new_row['current_status'] = get_readable_status(row.current_status)
        trip_info['trip_assigned'] = False
        
        if hasattr(row, 'trip_id'):
            trip_info['trip_assigned'] = True
            trip_info['trip_id'] = row.trip_id
            trip_info['trip_start_date'] = row.trip_start_date
            trip_info['current_stop_sequence'] = row.current_stop_sequence
            # trip_info['direction_id'] = row.direction_id

        if row.trip_route_id:
            trip_info['trip_route_id'] = row.trip_route_id 
        if row.vehicle_id:
            new_row['vehicle_id'] = row.vehicle_id
        if row.stop_id:
            trip_info['stop_id'] = row.stop_id
        if row.timestamp:
            position_info['timestamp'] = row.timestamp
        if row.position_latitude:
            position_info['latitude'] = row.position_latitude
        if row.position_longitude:
            position_info['longitude'] = row.position_longitude
        if row.position_bearing:
            position_info['position_bearing'] = row.position_bearing
        if row.position_speed:
            new_row['position_speed'] = row.position_speed
        if row.stop_id:
            new_row['stop_id'] = row.stop_id
        if row.geometry:
            try:
                new_row['geometry'] = JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
            except:
                new_row['geometry'] = [row.position_longitude,row.position_latitude]

        if geojson == True:
            geojson_row['type'] = 'Feature'
            if row.geometry:
                geojson_row['geometry'] = JsonReturn(geo.mapping(shape.to_shape((row.geometry))))
                geojson_row['lineString'] = convert_geometry_to_line_string(row.geometry)
            if hasattr(row, 'trip_id'):
                properties['trip'] = trip_info
                properties['trip']['trip_id'] = trip_info['trip_id']
                properties['trip']['current_stop_sequence'] = trip_info['current_stop_sequence']
                properties['trip']['vehicle_id'] = new_row['vehicle_id']

            geojson_row['properties'] = properties
            if hasattr(new_row, 'stop_id'):
                geojson_row['properties']['stop_id'] = new_row.stop_id
            properties['position'] = position_info
            properties['current_status'] = new_row['current_status']
            geojson_row['properties']['trip_assigned'] = trip_info['trip_assigned']
            return geojson_row
        new_row['trip'] = trip_info
        new_row['position'] = position_info
        return new_row

def upcoming_stop_time_reformat_for_async(stop_time_update):
    if stop_time_update:
        sanitized_stop_time_json = stop_time_update.trip_updates.stop_time_json.replace("'", '"')
        update_json = json.loads(sanitized_stop_time_json)

        for row in update_json:
            if row['stop_sequence'] == stop_time_update.stop_sequence:
                new_stop_time_object = {}
                if row['arrival']:
                    new_stop_time_object['arrival'] = row['arrival']
                if row['departure']:
                    new_stop_time_object['departure'] = row['departure']
                new_stop_time_object['schedule_relationship'] = get_readable_schedule_relationship(row['schedule_relationship'])
                new_stop_time_object['stop_id'] = row['stop_id']
                new_stop_time_object['stop_sequence'] = row['stop_sequence']
                return new_stop_time_object
    else:
        return False
        # if stop_time_update.trip_updates:
        #     
        #     for row in update_json:
        #         new_stop_time_object = {}
        #         if row['stop_sequence'] == stop_time_update.stop_sequence:
        #             if row['arrival']:
        #                 new_stop_time_object['arrival'] = row['arrival']
        #             if row['departure']:
        #                 new_stop_time_object['departure'] = row['departure']
        #             new_stop_time_object['schedule_relationship'] = get_readable_schedule_relationship(row['schedule_relationship'])
        #             new_stop_time_object['stop_id'] = row['stop_id']
        #             new_stop_time_object['stop_sequence'] = row['stop_sequence']
        #             return new_stop_time_object
            
def upcoming_stop_time_reformat(stop_time_update_query):
    for stop_time_update in stop_time_update_query.scalars():
        if stop_time_update != None:
            if stop_time_update.trip_updates != None:
                sanitized_stop_time_json = stop_time_update.trip_updates.stop_time_json.replace("'", '"')
                update_json = json.loads(sanitized_stop_time_json)
                for row in update_json:
                    new_stop_time_object = {}
                    if row['stop_sequence'] == stop_time_update.stop_sequence:
                        if row['arrival']:
                            new_stop_time_object['arrival'] = row['arrival']
                        if row['departure']:
                            new_stop_time_object['departure'] = row['departure']
                        new_stop_time_object['schedule_relationship'] = get_readable_schedule_relationship(row['schedule_relationship'])
                        new_stop_time_object['stop_id'] = row['stop_id']
                        new_stop_time_object['stop_sequence'] = row['stop_sequence']
                        return new_stop_time_object
def get_readable_status(status):
    if status == 0:
        return 'INCOMING_AT'
    if status == 1:
        return 'STOPPED_AT'
    if status == 2:
        return 'IN_TRANSIT_TO'

def get_readable_schedule_relationship(schedule_relationship):
    if schedule_relationship == -1:
        return ''
    if schedule_relationship == 0:
        return 'SCHEDULED'
    if schedule_relationship == 1:
        return 'SKIPPED'
    if schedule_relationship == 2:
        return 'NO_DATA'
    if schedule_relationship == 3:
        return 'UNSCHEDULED'
