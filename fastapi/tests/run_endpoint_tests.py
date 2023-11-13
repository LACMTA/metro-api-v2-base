import os
import sys

def run_tests(env):
    if env == '--local':
        os.system('ENV=local pytest test_endpoints.py')
    elif env == '--dev':
        os.system('ENV=dev pytest test_endpoints.py')
    else:
        raise ValueError("Invalid environment. Choose --local or --dev")

if len(sys.argv) != 2:
    print("Usage: python run_tests.py [--local|--dev]")
else:
    env = sys.argv[1]
    run_tests(env)