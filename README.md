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
./build.sh
```

Run the dispatcher (this will communicate with the local Docker daemon):

```bash
python dispatcher.py
```

The `dispatcher.py` includes a small interactive example (in the `__main__` block) that demonstrates posting multiple sample pieces of code and retrieving results.

## Usage example (programmatic)

See `examples/client_example.py` for a small client showing how to call `run_in_docker(code, payload)` from `dispatcher.py`.

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
