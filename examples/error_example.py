"""Error example: demonstrates a user function raising an exception.

Run: python examples/error_example.py
"""
import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lambda_poc.dispatcher import Dispatcher


def main():
    # This code will raise when run inside the runner
    code = """
def entrypoint(data):
    raise ValueError('intentional error from user code')
"""

    d = Dispatcher()
    try:
        print(d.run(code, {}))
    except Exception as e:
        print("Caught exception from runner:", type(e).__name__, e)


if __name__ == "__main__":
    main()
