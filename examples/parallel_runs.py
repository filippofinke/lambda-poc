"""Parallel-ish example: run different code snippets sequentially to show caching.

This runs multiple different pieces of user code to demonstrate the dispatcher
caches containers by code hash (so identical code will reuse the same runner).

Run: python examples/parallel_runs.py
"""
import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lambda_poc.dispatcher import Dispatcher


def main():
    d = Dispatcher()

    code1 = """
def entrypoint(data):
    return {"id": 1, "msg": data}
"""

    code2 = """
def entrypoint(data):
    return {"id": 2, "len": len(str(data))}
"""

    print("Run code1 first time:")
    print(d.run(code1, {"payload": "first"}))

    print("Run code1 second time (should reuse container):")
    print(d.run(code1, {"payload": "second"}))

    print("Run code2 (different code, new container):")
    print(d.run(code2, {"payload": "x" * 20}))


if __name__ == "__main__":
    main()
