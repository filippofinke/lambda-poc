"""Class-based Dispatcher that manages runner containers and calls.

This module defines `Dispatcher` which can be instantiated and used as a
library. It encapsulates caching of containers per code hash, lifecycle
cleanup, and provides a `run` method.
"""
from __future__ import annotations

import hashlib
import logging
import requests
import time
import threading
import atexit
from typing import Dict, Optional

from .services import DockerService
from .constants import DEFAULT_NETWORK, DEFAULT_TTL_SECONDS, RUNNER_IMAGE

logger = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self, *, ttl_seconds: int = DEFAULT_TTL_SECONDS, network: str = DEFAULT_NETWORK, image: str = RUNNER_IMAGE, docker_service: Optional[DockerService] = None):
        self.ttl_seconds = ttl_seconds
        self.network = network
        self.image = image
        self.docker = docker_service or DockerService(network)

        # code_hash -> {name, last_used}
        self.containers: Dict[str, Dict] = {}

        self._stop_event = threading.Event()
        self.docker.ensure_network()
        threading.Thread(target=self._cleanup_idle, daemon=True).start()

    def _hash_code(self, user_code: str) -> str:
        return hashlib.sha256(user_code.encode()).hexdigest()[:16]

    def _ensure_container(self, code_hash: str, user_code: str) -> str:
        name = f"runner_{code_hash}"
        try:
            cont = self.docker.get_container(name)
            if cont.status != "running":
                cont.start()
        except Exception:
            # create a new container
            cont = self.docker.run_container(self.image, name, {"8080/tcp": None})
            time.sleep(1)
            cont.reload()
            host_ip = cont.ports["8080/tcp"][0]["HostIp"]
            host_port = cont.ports["8080/tcp"][0]["HostPort"]
            url = f"http://{host_ip}:{host_port}/load"
            resp = requests.post(url, json={"code": user_code})
            resp.raise_for_status()

        self.containers[code_hash] = {"name": name, "last_used": time.time()}
        cont.reload()
        host_ip = cont.ports["8080/tcp"][0]["HostIp"]
        host_port = cont.ports["8080/tcp"][0]["HostPort"]
        return f"{host_ip}:{host_port}"

    def run(self, user_code: str, input_data: dict) -> dict:
        code_hash = self._hash_code(user_code)
        host_addr = self._ensure_container(code_hash, user_code)
        url = f"http://{host_addr}/run"
        resp = requests.post(url, json=input_data)
        resp.raise_for_status()
        self.containers[code_hash]["last_used"] = time.time()
        return resp.json()

    def _cleanup_idle(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            for code_hash, meta in list(self.containers.items()):
                if now - meta["last_used"] > self.ttl_seconds:
                    try:
                        self.docker.remove_container(meta["name"])
                    except Exception:
                        pass
                    self.containers.pop(code_hash, None)
            for _ in range(10):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def shutdown(self):
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        for code_hash, meta in list(self.containers.items()):
            try:
                self.docker.remove_container(meta["name"])
            except Exception:
                pass
            self.containers.pop(code_hash, None)
        try:
            self.docker.remove_network()
        except Exception:
            pass


_default_dispatcher: Optional[Dispatcher] = None


def get_default_dispatcher() -> Dispatcher:
    global _default_dispatcher
    if _default_dispatcher is None:
        _default_dispatcher = Dispatcher()
    return _default_dispatcher


def run_in_docker(user_code: str, input_data: dict) -> dict:
    return get_default_dispatcher().run(user_code, input_data)


# Ensure the default dispatcher is shut down at process exit
def _shutdown_default_dispatcher() -> None:
    global _default_dispatcher
    if _default_dispatcher is not None:
        try:
            _default_dispatcher.shutdown()
        except Exception:
            pass

atexit.register(_shutdown_default_dispatcher)


Dispatcher.__enter__ = lambda self: self


def _dispatcher_exit(self, exc_type, exc, tb):
    try:
        self.shutdown()
    except Exception:
        pass
    return False


Dispatcher.__exit__ = _dispatcher_exit
