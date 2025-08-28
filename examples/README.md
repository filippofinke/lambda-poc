# Examples

See `client_example.py` for a small demonstration of calling `run_in_docker` from `dispatcher.py`.

Other example scripts:

- `echo_example.py` : simple echo of the input payload
- `fibonacci_example.py` : compute Fibonacci(n) inside the runner
- `parallel_runs.py` : run different code snippets to show container caching
- `with_context_example.py` : use `Dispatcher` as a context manager
- `error_example.py` : demonstrates how runner exceptions propagate
- `payload_example.py` : show different payload types and returned summary

## FastAPI example

A small FastAPI app is provided in `examples/fastapi_example.py`. It exposes:

- GET /greet?name=YourName

which forwards the request to the dispatcher (`run_in_docker`) so the greeting is computed inside the runner container. The endpoint returns the runner result as JSON.

Quick run instructions:

1. Make sure Docker is running on the host and the runner image (configured via `lambda_poc.constants.RUNNER_IMAGE`) is available.
2. Install Python dependencies:
   - pip install fastapi uvicorn requests
     (You likely already have requests in the project.)
3. Start the FastAPI app:
   - python -m examples.fastapi_example
     or
   - uvicorn examples.fastapi_example:app --reload --port 8000
4. Call the endpoint:
   - http://127.0.0.1:8000/greet?name=Alice

Notes:

- The dispatcher will start a runner container for the provided code hash on first use; the first request may take a few seconds.
- If you need to build or pull the runner image, consult the project's top-level README or the value of `lambda_poc.constants.RUNNER_IMAGE`.
