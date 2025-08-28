"""Payload example: demonstrate different input types and outputs.

Run: python examples/payload_example.py
"""
import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lambda_poc.dispatcher import run_in_docker


def main():
    code = """
def entrypoint(data):
    # Return a summary of the incoming payload types
    return {
        "types": {k: type(v).__name__ for k, v in data.items()},
        "count": len(data)
    }
"""

    payload = {"s": "string", "i": 42, "lst": [1, 2, 3], "m": {"k": "v"}}
    print(run_in_docker(code, payload))


if __name__ == "__main__":
    main()
