from typing import Optional
import random
from fastapi import FastAPI, HTTPException
import os
import sys

THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lambda_poc.dispatcher import run_in_docker

app = FastAPI()

# Pool of 5 different code implementations
CODE_POOL = [
    """
def entrypoint(data):
    name = data.get("name") or "world"
    return {"greeting": f"Hello {name}", "name": name, "container_id": "1"}
    """,
    
    """
def entrypoint(data):
    name = data.get("name") or "stranger"
    return {"greeting": f"Greetings {name}!", "name": name, "container_id": "2"}
    """,
    
    """
def entrypoint(data):
    name = data.get("name") or "friend"
    return {"greeting": f"Welcome {name}", "name": name, "container_id": "3"}
    """,
    
    """
def entrypoint(data):
    name = data.get("name") or "guest"
    return {"greeting": f"Hi there, {name}!", "name": name, "container_id": "4"}
    """,
    
    """
def entrypoint(data):
    name = data.get("name") or "visitor"
    return {"greeting": f"Nice to meet you, {name}", "name": name, "container_id": "5"}
    """
]

@app.get("/greet")
def greet(name: Optional[str] = None):
    """
    Call the dispatcher to execute a randomly selected code from CODE_POOL with payload {"name": name}
    and return the runner's JSON response.
    """
    payload = {"name": name}
    
    # Randomly select code from the pool
    selected_code = random.choice(CODE_POOL)
    
    try:
        result = run_in_docker(selected_code, payload)
        # Add information about which container was used
        result["code_index"] = CODE_POOL.index(selected_code) + 1
    except Exception as exc:
        # surface runner / dispatcher errors as HTTP 500
        raise HTTPException(status_code=500, detail=str(exc))
    
    return result

if __name__ == "__main__":
    # Run with: python -m examples.fastapi_example
    # Requires uvicorn installed: pip install uvicorn
    import uvicorn
    uvicorn.run("examples.fastapi_example:app", host="127.0.0.1", port=8000, log_level="info", reload=True)