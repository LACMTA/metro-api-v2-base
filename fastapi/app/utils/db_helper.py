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
    if row.trip_id:
        trip['tripid'] = row.trip_id
    if row.start_time:
        trip['startTime'] = row.start_time
    if row.start_date:
        trip['startDate'] = row.start_date
    if row.schedule_relationship:
        trip['scheduleRelationship'] = get_readable_schedule_relationship(row.schedule_relationship)
    if row.route_id:
        trip['routeId'] = row.route_id
    if row.direction_id:
        trip['directionId'] = row.direction_id
    trip_update['trip'] = trip

    stop_time_updates = []
    
    if row.stop_time_json:
        clean_stop_time_json = row.stop_time_json.replace("'", '"')
        for stop_time in json.loads(clean_stop_time_json):
            this_stop_time = {}
            if stop_time['stop_sequence']:
                this_stop_time['stopSequence'] = stop_time['stop_sequence']
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
                this_stop_time['scheduleRelationship'] = get_readable_schedule_relationship(stop_time['schedule_relationship'])
            if stop_time['stop_id']:
                this_stop_time['stopId'] = stop_time['stop_id']
            stop_time_updates.append(this_stop_time)
    trip_update['stopTimeUpdates'] = stop_time_updates
    result_row['tripUpdate'] = trip_update
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
        if row.position_speed:
            position_info['speed'] = row.position_speed
            del row.position_speed
        if row.geometry:
            row.geometry = JsonReturn(geo.mapping(shape.to_shape((row.geometry))))

        if geojson == True:
            geojson_row['type'] = 'Feature'
            if row.geometry:
                geojson_row['geometry'] = row.geometry
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

def get_readable_status(status):
    if status == 0:
        return 'INCOMING_AT'
    if status == 1:
        return 'STOPPED_AT'
    if status == 2:
        return 'IN_TRANSIT_TO'

def get_readable_schedule_relationship(schedule_relationship):
    if schedule_relationship == 0:
        return 'SCHEDULED'
    if schedule_relationship == 1:
        return 'SKIPPED'
    if schedule_relationship == 2:
        return 'NO_DATA'
    if schedule_relationship == 3:
        return 'UNSCHEDULED'
