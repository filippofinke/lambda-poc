"""Simple client example showing how to call run_in_docker from dispatcher.

This example assumes you have built the Docker image with `./build.sh`
and that the Docker daemon is available to `dispatcher.py`.

The script is runnable either from the repository root:

    python examples/client_example.py

or from inside the `examples/` directory. When run from `examples/` the
repo root is added to `sys.path` so the top-level `dispatcher` module can be
imported.
"""

import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lambda_poc.dispatcher import Dispatcher, run_in_docker


def main():
    code = """
def entrypoint(data):
    return {"echo": data}
"""
    payload = {"message": "hello from example"}
    # Library-style: instantiate and use a Dispatcher
    d = Dispatcher()
    res = d.run(code, payload)
    print("Dispatcher.run ->", res)

    # Or use the module-level convenience function (uses a global default dispatcher)
    res2 = run_in_docker(code, payload)
    print("run_in_docker ->", res2)


if __name__ == "__main__":
    main()
