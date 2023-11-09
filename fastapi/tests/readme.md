# Project Name

## Setup

Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Running Tests

This project uses `pytest` for unit testing. To run the tests, use the following command:

```bash
pytest tests/test_main.py
```

This command will run all test cases in the test_main.py file.

### Load Testing
This project uses `locust` for load testing. 

To run the load tests, use the following command:
```bash
locust -f test_load.py -u 2000 -r 100

```

This command will start a swarm of 2000 users, with a hatch rate of 100 users per second, using the Locust file in your tests directory.

### Contributing
Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests to us.

### License
This project is licensed under the MIT License - see the LICENSE.md file for details

```