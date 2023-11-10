import requests
import pytest
from app.models import TripUpdate, VehiclePosition

agency_ids = ["lacmta", "lacmta_rail"]
trip_update_fields = [f for f in TripUpdate.__fields__.keys()]
vehicle_position_fields = [f for f in VehiclePosition.__fields__.keys()]

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_all_trip_updates(agency_id):
    response = requests.get(f"http://localhost:80/{agency_id}/trip_updates")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id,field", [(a, f) for a in agency_ids for f in trip_update_fields])
def test_get_list_of_trip_update_field_values(agency_id, field):
    response = requests.get(f"http://localhost:80/{agency_id}/trip_updates/{field}")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_all_vehicle_positions(agency_id):
    response = requests.get(f"http://localhost:80/{agency_id}/vehicle_positions")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id,field", [(a, f) for a in agency_ids for f in vehicle_position_fields])
def test_get_list_of_vehicle_position_field_values(agency_id, field):
    response = requests.get(f"http://localhost:80/{agency_id}/vehicle_positions/{field}")
    assert response.status_code == 200