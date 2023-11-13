# Metro FastAPI Unit Tests

## Setup

Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Running all tests

This project uses `pytest` for unit testing. To run all the tests, use the following command:

```bash
pytest tests/test_main.py
```

This command will run all test cases in the test_main.py file.

### Logs

The tests will generate a log with naming in the following format:

`test_log_YEARMONTHDAY_TIME.txt`

That has details on the number of tests failed.

## Running endpoint tests

We use a Python script with `pytest` to run the endpoint tests with different environments. To run the endpoint tests, use the following commands:

### To test localhost

`python test_endpoints.py --local`

### To test deployed `dev`` instance

`python test_endpoints.py --dev`

## Load Testing

We use `locust` for load testing.

> Note: Ideally, you should run on a different machine that has access to the server running our fastapi application.

To run the load tests, use the following command:
```bash
locust -f load_testing.py -u 2000 -r 100

```

This command will start a swarm of 1000 users, with a hatch rate of 100 users per second, using the Locust file in your tests directory.

