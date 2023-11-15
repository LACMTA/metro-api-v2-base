import os
import requests
import pytest

# Get the url
url = 'https://dev-metro-api-v2.ofhq3vd1r7une.us-west-2.cs.amazonlightsail.com'

agency_ids = ["LACMTA", "LACMTA_Rail"]
import os
import requests
import pytest

# Set the URL
url = 'http://localhost:80'

agency_ids = ["LACMTA", "LACMTA_Rail"]

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_all_trip_updates(agency_id):
    response = requests.get(f"{url}/{agency_id}/trip_updates")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_all_vehicle_positions(agency_id):
    response = requests.get(f"{url}/{agency_id}/vehicle_positions")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_all_vehicle_positions(agency_id):
    response = requests.get(f"{url}/{agency_id}/trip_updates/trip_id")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_vehicle_positions_route_code_json(agency_id):
    response = requests.get(f"{url}/{agency_id}/vehicle_positions/route_code/720?format=json")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_vehicle_positions_route_code_geojson(agency_id):
    response = requests.get(f"{url}/{agency_id}/vehicle_positions/route_code/720?format=geojson")
    assert response.status_code == 200
