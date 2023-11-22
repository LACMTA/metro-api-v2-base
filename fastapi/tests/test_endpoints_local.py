import os
import requests
import pytest
import websockets
import asyncio
import json

# Set the URL
url = 'http://localhost:80'
websocket_url = 'ws://localhost:80'

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

def test_get_vehicle_positions_bus_route_code_json():
    response = requests.get(f"{url}/LACMTA/vehicle_positions/route_code/720?format=json")
    assert response.status_code == 200

def test_get_vehicle_positions_rail_route_code_json():
    response = requests.get(f"{url}/LACMTA_Rail/vehicle_positions/route_code/801?format=json")
    assert response.status_code == 200

def test_get_vehicle_positions_route_code_geojson():
    response = requests.get(f"{url}/LACMTA/vehicle_positions/route_code/720?format=geojson")
    assert response.status_code == 200

def test_get_vehicle_positions_route_code_geojson():
    response = requests.get(f"{url}/LACMTA_Rail/vehicle_positions/route_code/801?format=geojson")
    assert response.status_code == 200
@pytest.mark.asyncio
async def test_websocket_endpoint():
    # Include the agency_id in the URL
    websocket_url_with_agency_id = f"{websocket_url}/ws/LACMTA_Rail/vehicle_positions"
    async with websockets.connect(websocket_url_with_agency_id) as websocket:
        # Wait for a response
        response = await websocket.recv()

        # Parse the response
        response_data = json.loads(response)

        # Assert that the response is what you expected
        assert response_data["type"] == "ping"