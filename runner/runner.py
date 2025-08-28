from fastapi import FastAPI, Request, HTTPException
import types
import uvicorn
import threading
import time
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

app = FastAPI()
# runtime module created by /load
user_module: Optional[types.ModuleType] = None

# Idle timeout in seconds. If no requests (/load or /run) are received for
# this many seconds the runner will exit. Controlled via env var
# RUNNER_IDLE_TTL (defaults to 60 seconds). Set to 0 or negative to disable.
RUNNER_IDLE_TTL = int(os.environ.get("RUNNER_IDLE_TTL", "60"))

# Track last activity timestamp (monotonic)
_last_activity = time.monotonic()


def _touch_activity() -> None:
    global _last_activity
    _last_activity = time.monotonic()


def _idle_monitor() -> None:
    if RUNNER_IDLE_TTL <= 0:
        logger.debug("RUNNER_IDLE_TTL disabled (<=0)")
        return
    logger.info("idle monitor started, TTL=%s seconds", RUNNER_IDLE_TTL)
    while True:
        now = time.monotonic()
        idle = now - _last_activity
        if idle > RUNNER_IDLE_TTL:
            logger.info("No activity for %s seconds, exiting", idle)
            # Forcefully exit the process; uvicorn will stop with this.
            try:
                os._exit(0)
            except Exception:
                # As a fallback, raise SystemExit
                raise SystemExit(0)
        time.sleep(1)



@app.post("/load")
async def load_code(request: Request) -> Dict[str, Any]:
    """Load user-provided Python code into a fresh module namespace.

    Expects JSON body: {"code": "<python source>"}
    The provided code must define a function `entrypoint(data)` which will be
    called later by the `/run` endpoint.
    """
    global user_module
    payload = await request.json()
    code_str = payload.get("code")

    if not isinstance(code_str, str):
        raise HTTPException(status_code=400, detail="Missing or invalid 'code' field")

    # Create isolated module namespace for the user code
    user_module = types.ModuleType("user_module")
    try:
        exec(code_str, user_module.__dict__)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error executing code: {exc}")

    if not hasattr(user_module, "entrypoint"):
        raise HTTPException(status_code=400, detail="Code must define an 'entrypoint(data)' function")

    _touch_activity()
    return {"status": "loaded"}


@app.post("/run")
async def run_code(request: Request) -> Any:
    """Run the previously loaded `entrypoint` with the provided JSON payload.

    Expects arbitrary JSON which is forwarded to `entrypoint(data)`.
    The return value from `entrypoint` is returned as JSON.
    """
    if user_module is None:
        raise HTTPException(status_code=400, detail="No code loaded. Call /load first.")

    payload = await request.json()
    try:
        result = user_module.entrypoint(payload)
    except Exception as exc:
        # Surface user-code exceptions as server errors with the exception string
        raise HTTPException(status_code=500, detail=f"User code raised an exception: {exc}")

    _touch_activity()
    return result


if __name__ == "__main__":
    # Use uvicorn programmatically for a simple development server
    # start idle monitor thread
    threading.Thread(target=_idle_monitor, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8080)


# When running under an external ASGI server we still want the idle monitor
# to be active; start it at import time in a daemon thread.
try:
    threading.Thread(target=_idle_monitor, daemon=True).start()
except Exception:
    pass
