 Metro API v2

Metro API v2 is an API for Metro's GTFS-RT and GTFS Static data.

* [Documentation site](https://lacmta.github.io/metro-api-v2/)

## Getting Started

### Clone the Repository

Install the repository locally. The application can be run directly or through a Docker container.

``` shell
# clone the repository
git clone https://github.com/LACMTA/metro_api_v2.git

# change to the directory
cd metro-api-v2
```

### Set Environment Variables

Get the `.env` file with the necessary credentials and add it to the repository's root directory.

## Deploying

### Prerequistes

- [Docker installed](https://docs.docker.com/get-docker/)
    - Even if you are running Linux through WSL, you will need to install the Docker Desktop for Windows, not Linux! Have WSL v2 installed, or else you will need to turn on Hyper-V and Containers within the Windows Features.

This requires Docker to run the multiple containers as part of a single image.

### Set Docker Compose File

Get the `docker-compose.yml` and add it to the repository's root directory.

### Build All Containers

Build all containers as part of the same image so they can talk to each other:

``` shell
docker compose build
```

This will take a while each time you run after starting docker because all the files need to be downloaded.  While docker is open, these files will stay cached.

### Run the Containers

Run the containers using this command in order to test your application changes locally before deployment.

```shell
docker compose up
```

### Deployment

__To Development:__

Deployments are handled through GitHub by opening a Pull Request from a dedicated branch into the `dev` branch.

Upon merging into the `dev` branch, a GitHub Actions workflow will trigger to deploy the image to the dev environment on AWS Lightsail.

__To Production:__

Open a Pull Request from the `dev` branch to the `main` branch.

Upon merging into the `main` branch, a GitHub Actions workflow will trigger to deploy the image to the production environment on AWS Lightsail.

## Developing

### Prerequisites

Install python

On Ubuntu:

```shell
sudo apt update && upgrade
sudo apt install python3 python3-pip
```

### Set Environment Variables

Get the `secrets.py` files with the necessary credentials and add them to the `\fastapi\app\` and `\data-loading-service\app\` folders.

Make sure they are targeted by the `.gitignore` and grayed out, indicating that they will not be tracked or committed to the repository.

### Developing the FastAPI Application

``` shell
# change to the API application directory
cd fastapi

# install the required libraries
pip3 install -r requirements.txt

# run uvicorn to serve the API
uvicorn app.main:app --reload --port 1212
```

You may run into an error when trying to install `psycopg2`.

Use this command to run uvicorn from Windows.

``` shell
python -m uvicorn app.main:app --reload 
```

### Developing the Data Loading Service Application

``` shell
# change to the API application directory
cd data-loading-service
```

``` shell
# install the required libraries
pip3 install -r requirements.txt
```

Run the application

``` shell
# install the required libraries
cd app

python main.py

# or
python3 main.py
```

### Debugging in VS Code

Go to `Run -> Open Configurations` and add this to the `launch.json` file:

``` js
{
    "name": "Python: Module",
    "type": "python",
    "request": "launch",
    "module": "uvicorn",
    "args": ["app.main:app", "--reload"],
    "justMyCode": true
}
```

This will tell the debugger to launch uvicorn as a python module, which is the equivalent of running `python -m uvicorn` in the terminal.  The `justMyCode` setting tells the debugger to only debug your code and not the included libraries.

To use this configuration, press `F1` or `ctrl-shift-P` and choose `Debug: Select and Start Debugging`.  From the list, select the `Python: Module` configuration.

### Database

Install [DBeaver](https://dbeaver.io/download/).

Install [PostgreSQL v15.2](https://www.postgresql.org/download/).

#### Changing the Database

Is the data updated via:

* a manual trigger
* or an automated schedule

Use the `data-loading-service` application for automated scheduled data loading because it will re-create the database tables and columns.

If the database update is updated via a manual trigger, we can use the Jupyter Notebooks/Python scripts for one-time changes to the database. Any manual changes will need to be applied to both the dev and production environments.

Which tables are automated?

The `config.py` file inside the application folders sets the `TARGET_DB_SCHEMA` value to determine whether the production or dev database is used.

## Endpoint Naming Conventions

- All GTFS endpoints require an `agency_id`.
- If no specific value for a parameter is specified at the end, the endpoint will return all values for that parameter.

## Versioning

Metro API v2 uses a modified version of [Semantic Versioning](https://semver.org/), with major (`X`), minor(`x`), and hotfix(`*`) releases for the numbers respectively: `X.x.*`.

More versioning information can be found in [versioning.md](versioning.md)

## Extra Notes

### Build Individual Docker Containers For Each Application

You can use these instructions to build individual containers that run independently and don't talk to each other, and to push updates to 

``` shell
# cd into any application folder: fastapi, data-loading-service
cd fastapi

# create image in current folder with tag nginx
# [application]:[version]
docker build . -t metro-api-v2:metro-api-v2 .

# runs metro-api-v2 image
docker run --rm -it  -p 80:80/tcp metro-api-v2:metro-api-v2
```