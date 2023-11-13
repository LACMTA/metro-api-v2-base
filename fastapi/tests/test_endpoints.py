import os
import requests
import pytest

# Get the environment variable
env = os.getenv('ENV')

# Set the URL based on the environment variable
if env == 'local':
    url = 'http://localhost:80'
elif env == 'dev':
    url = 'https://dev-metro-api-v2.ofhq3vd1r7une.us-west-2.cs.amazonlightsail.com'
else:
    raise ValueError("Invalid environment. Set ENV environment variable to 'local' or 'dev'")

agency_ids = ["LACMTA", "LACMTA_Rail"]

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_all_trip_updates(agency_id):
    response = requests.get(f"{url}/{agency_id}/trip_updates")
    assert response.status_code == 200

@pytest.mark.parametrize("agency_id", agency_ids)
def test_get_all_vehicle_positions(agency_id):
    response = requests.get(f"{url}/{agency_id}/vehicle_positions")
    assert response.status_code == 200