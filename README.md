# lambda-poc

Lightweight proof-of-concept for running user-provided Python "runners" inside ephemeral Docker containers.

This repository contains:

- `runner.py` — a tiny FastAPI-based runner that accepts Python code via `/load` and executes it via `/run`.
- `dispatcher.py` — a simple controller that builds/starts Docker containers for submitted code, calls the runner, and performs container lifecycle cleanup.
- `Dockerfile` and `build.sh` — build the runner image used by the dispatcher.

This project is intended as a minimal PoC and should NOT be used as-is in production without adding proper sandboxing, resource limits, and security controls.

**Contents**

- Overview
- Quick start
- Usage examples
- Development notes
- Security and limitations

## Quick start

Prerequisites:

- Docker installed and running
- Python 3.11 (recommended) for running the `dispatcher.py` locally

Build the runner image:

```bash
cd runner && ./build.sh
```

Run the dispatcher (this will communicate with the local Docker daemon). The dispatcher module is available under the `lambda_poc` package; to run the small interactive demo use the `examples/client_example.py` script or run a short script that imports `lambda_poc.dispatcher`.

Example (run the included client):

```bash
python examples/client_example.py
```

If you want to run the runner directly for development, the runner script is under `runner/runner.py` and can be started with:

```bash
python runner/runner.py
```

Note that the project doesn't include a top-level `dispatcher.py` executable — the dispatcher is provided as the `lambda_poc` package (`lambda_poc/dispatcher.py`).

## Usage example (programmatic)

See `examples/client_example.py` for a small client showing how to call `run_in_docker(code, payload)` from `dispatcher.py`.

## Examples

This repository includes a set of small example scripts under the `examples/` directory that demonstrate common usage patterns of the `Dispatcher` and `run_in_docker` helper. Each example is runnable from the repository root, for example:

```bash
python examples/echo_example.py
python examples/fibonacci_example.py
python examples/parallel_runs.py
python examples/with_context_example.py
python examples/error_example.py
python examples/payload_example.py
```

- `echo_example.py`: simple echo of the input payload
- `fibonacci_example.py`: compute Fibonacci(n) inside the runner
- `parallel_runs.py`: run different code snippets to show container caching
- `with_context_example.py`: use `Dispatcher` as a context manager
- `error_example.py`: demonstrates how runner exceptions propagate
- `payload_example.py`: show different payload types and returned summary

Notes:

- You need Docker running locally and a built runner image. Build the image with `./build.sh` before running examples.
- Examples will contact the Docker daemon via the `Dispatcher` and start ephemeral containers; ensure your environment allows it.

## Development

- Linting: follow standard Python best practices. Use `ruff`/`black` if desired.
- Tests: none included in this PoC.

## Security and limitations

This PoC intentionally keeps things small; it executes arbitrary Python code inside containers. Without additional sandboxing and resource controls this is unsafe. If you plan to extend this project, consider:

- Running containers with user namespaces / non-root users
- Limiting CPU / memory and execution time
- Disallowing network access from user code or restricting it
- Validating and restricting uploaded code

## License

MIT — see `LICENSE`.
