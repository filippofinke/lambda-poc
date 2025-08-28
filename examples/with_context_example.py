"""Context manager example: use Dispatcher in a `with` block.

Run: python examples/with_context_example.py
"""
import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lambda_poc.dispatcher import Dispatcher


def main():
    code = """
def entrypoint(data):
    return {"upper": str(data.get('text', '')).upper()}
"""

    payload = {"text": "use context manager"}
    with Dispatcher() as d:
        print(d.run(code, payload))


if __name__ == "__main__":
    main()
