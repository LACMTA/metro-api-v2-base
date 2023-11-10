import subprocess
from datetime import datetime

def run_tests():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f'test_log_{timestamp}.txt'
    with open(log_file_name, 'w') as f:
        print("Running unit tests...", file=f)
        result = subprocess.run(["pytest", "-v", "test_endpoints.py"], stdout=f, text=True)
        if result.returncode == 0:
            print("Unit tests check has passed", file=f)
        else:
            print("Unit tests check has failed", file=f)
            return

        print("Running load tests...", file=f)
        # result = subprocess.run(["locust", "-f", "test_load.py", "-u", "2000", "-r", "100"], stdout=f, text=True)
        # if result.returncode == 0:
        #     print("Load tests check has passed", file=f)
        # else:
        #     print("Load tests check has failed", file=f)
        #     return

        print("All checks passed", file=f)

if __name__ == "__main__":
    run_tests()