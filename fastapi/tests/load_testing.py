from locust import HttpUser, task, between
import click

@click.command()
@click.option('--host', default='http://localhost:80', help='Host URL')

def run_locust(host):
    WebsiteUser.host = host


class WebsiteUser(HttpUser):
    wait_time = between(1, 2.5)

    @task
    def load_route_overview_lacmta(self):
        self.client.get("/LACMTA/route_overview/720")

    @task
    def load_route_overview_lacmta_rail(self):
        self.client.get("/LACMTA_Rail/route_overview/801")


    @task
    def load_route_overview_all(self):
        self.client.get("/all/route_overview/")

    @task
    def load_vehicle_positions_bus(self):
        self.client.get("/LACMTA/vehicle_positions?format=geojson")


    @task
    def load_vehicle_positions_rail(self):
        self.client.get("/LACMTA_Rail/vehicle_positions?format=geojson")

    @task
    def load_trip_updates_for_801(self):
        self.client.get("/LACMTA_Rail/trip_updates/route_id/801")

    @task
    def load_trip_updates_all_bus(self):
        self.client.get("/LACMTA/trip_updates")

    @task
    def load_trip_updates_all_rail(self):
        self.client.get("/LACMTA_Rail/trip_updates")
        
# @task
# def load_agency(self):
#     self.client.get("/agency_id/agency/")

    # @task
    # def load_agency(self):
    #     self.client.get("/agency_id/agency/")\

if __name__ == '__main__':
    run_locust()