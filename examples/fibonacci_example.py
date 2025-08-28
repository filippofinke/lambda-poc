"""Fibonacci example: compute fibonacci of n inside the runner.

Run: python examples/fibonacci_example.py
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
    n = int(data.get('n', 0))
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return {"n": n, "fib": a}
"""

    payload = {"n": 10}
    d = Dispatcher()
    print("Dispatcher.run ->", d.run(code, payload))
    print("run_in_docker ->", run_in_docker(code, payload))


if __name__ == "__main__":
    main()
