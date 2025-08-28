from typing import Optional

from fastapi import FastAPI, HTTPException
import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lambda_poc.dispatcher import run_in_docker

app = FastAPI()

USER_CODE = """
def entrypoint(data):
    name = data.get("name") or "world"
    return {"greeting": f"Hello {name}", "name": name}
"""

@app.get("/greet")
def greet(name: Optional[str] = None):
    """
    Call the dispatcher to execute the USER_CODE with payload {"name": name}
    and return the runner's JSON response.
    """
    payload = {"name": name}
    try:
        result = run_in_docker(USER_CODE, payload)
    except Exception as exc:
        # surface runner / dispatcher errors as HTTP 500
        raise HTTPException(status_code=500, detail=str(exc))
    return result

if __name__ == "__main__":
    # Run with: python -m examples.fastapi_example
    # Requires uvicorn installed: pip install uvicorn
    import uvicorn
    uvicorn.run("examples.fastapi_example:app", host="127.0.0.1", port=8000, log_level="info", reload=False)