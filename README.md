<h1 align="center">Welcome to lambda-poc</h1>

> Lightweight proof-of-concept for running user-provided Python "runners" inside ephemeral Docker containers

## Features

- [x] Execute user-provided Python code inside isolated Docker containers
- [x] FastAPI-based runner that accepts code via /load and executes via /run
- [x] Container caching by code hash to speed repeated runs
- [x] Automatic idle cleanup of unused containers
- [x] Small, easy-to-read codebase for experimentation

## Install / Requirements

- Docker (daemon available to the user running the dispatcher)
- Python 3.11 recommended (for running examples locally)
- Project Python deps (for running dispatcher/examples):
  - pip install -r requirements.txt
- Build runner Docker image (see Quick start)

## Quick start

1. Build the runner image:

```bash
cd runner
./build.sh
```

2. Run an example (from repository root):

```bash
python examples/client_example.py
```

Notes:

- The dispatcher will start a runner container for a code hash on first use; first run may take a few seconds.
- Ensure Docker is running and the built image name matches lambda_poc.constants.RUNNER_IMAGE (default: runner-service).

## Usage

- runner/runner.py — tiny FastAPI app that accepts Python source via POST /load and runs entrypoint(data) via POST /run.
- lambda_poc/dispatcher.py — starts containers, loads code, invokes the runner, and performs TTL-based cleanup.
- Examples under examples/ demonstrate common workflows (echo, fibonacci, error handling, payloads, FastAPI integration).

Example: programmatic run using the convenience helper

```python
from lambda_poc.dispatcher import run_in_docker

code = """
def entrypoint(data):
    return {"echo": data}
"""
print(run_in_docker(code, {"msg": "hello"}))
```

## Examples

Run any example from the repo root:

```bash
python examples/echo_example.py
python examples/fibonacci_example.py
python examples/parallel_runs.py
python examples/with_context_example.py
python examples/error_example.py
python examples/payload_example.py
# For the FastAPI demo:
uvicorn examples.fastapi_example:app --reload --port 8000
```

## Development

- Install dependencies:

```bash
pip install -r requirements.txt
```

- Build runner image for testing:

```bash
cd runner && ./build.sh
```

- Run and iterate on examples or import lambda_poc.Dispatcher in your code.

## Security & Limitations

This is a proof-of-concept. Do NOT run untrusted code with this setup in production — it executes arbitrary Python in containers without strict sandboxing. Suggested hardening before production use:

- Add resource limits (CPU/memory) and timeouts
- Run containers with restricted users and seccomp/apparmor policies
- Restrict network access and filesystem mounts
- Validate or sandbox uploaded code

## License

MIT — see LICENSE

## Author

👤 Filippo Finke

- Website: https://filippofinke.ch
- Twitter: https://twitter.com/filippofinke
- Github: https://github.com/filippofinke
- LinkedIn: https://linkedin.com/in/filippofinke
