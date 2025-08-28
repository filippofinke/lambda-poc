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
        # Lock to protect access to containers dict
        self.lock = threading.RLock()

        self._stop_event = threading.Event()
        self.docker.ensure_network()
        threading.Thread(target=self._cleanup_idle, daemon=True).start()

    def _hash_code(self, user_code: str) -> str:
        return hashlib.sha256(user_code.encode()).hexdigest()[:16]

    def _ensure_container(self, code_hash: str, user_code: str) -> str:
        name = f"runner_{code_hash}"
        
        with self.lock:
            # Check if we already have a container for this code hash
            if code_hash in self.containers:
                try:
                    cont = self.docker.get_container(name)
                    if cont.status != "running":
                        cont.start()
                        self._wait_for_container_ready(cont)
                    
                    # Update last used time
                    self.containers[code_hash]["last_used"] = time.time()
                    cont.reload()
                    host_ip = cont.ports["8080/tcp"][0]["HostIp"]
                    host_port = cont.ports["8080/tcp"][0]["HostPort"]
                    return f"{host_ip}:{host_port}"
                except Exception as e:
                    logger.warning(f"Error checking existing container: {e}")
                    # Container might be in a bad state, remove it from our cache
                    self.containers.pop(code_hash, None)
            
            # Create a new container
            logger.info(f"Creating new container for code_hash: {code_hash}")
            try:
                # Remove any existing container with this name
                self.docker.remove_container(name)
                
                # Create a new container
                cont = self.docker.run_container(self.image, name, {"8080/tcp": None})
                
                # Wait for container to be ready
                self._wait_for_container_ready(cont)
                
                # Load the user code with retry logic
                self._load_code_with_retry(cont, user_code)
                
                # Store in our cache
                self.containers[code_hash] = {"name": name, "last_used": time.time()}
                
                # Get the host information
                cont.reload()
                host_ip = cont.ports["8080/tcp"][0]["HostIp"]
                host_port = cont.ports["8080/tcp"][0]["HostPort"]
                return f"{host_ip}:{host_port}"
            except Exception as e:
                logger.error(f"Failed to create container: {e}")
                # Clean up in case of failure
                try:
                    self.docker.remove_container(name)
                except Exception:
                    pass
                raise

    def _wait_for_container_ready(self, container, timeout=30):
        """Wait until container is fully started and network is available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            if container.status == "running":
                # Check if network ports are assigned
                if "8080/tcp" in container.ports and container.ports["8080/tcp"]:
                    # Give it a moment for the service to start listening
                    time.sleep(1)
                    try:
                        host_ip = container.ports["8080/tcp"][0]["HostIp"]
                        host_port = container.ports["8080/tcp"][0]["HostPort"]
                        # Check if service is responding
                        health_url = f"http://{host_ip}:{host_port}/"
                        requests.get(health_url, timeout=1)
                        return True
                    except requests.RequestException:
                        # Service not ready yet, keep waiting
                        time.sleep(0.5)
            else:
                time.sleep(0.5)
        
        raise TimeoutError(f"Container {container.name} not ready after {timeout} seconds")

    def _load_code_with_retry(self, container, user_code, max_retries=5, retry_delay=1):
        """Load user code into container with retry logic."""
        container.reload()
        host_ip = container.ports["8080/tcp"][0]["HostIp"]
        host_port = container.ports["8080/tcp"][0]["HostPort"]
        url = f"http://{host_ip}:{host_port}/load"
        
        last_exception = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json={"code": user_code}, timeout=10)
                resp.raise_for_status()
                return
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt+1}/{max_retries} to load code failed: {e}")
                time.sleep(retry_delay)
        
        # If we got here, all attempts failed
        raise RuntimeError(f"Failed to load code after {max_retries} attempts: {last_exception}")

    def run(self, user_code: str, input_data: dict) -> dict:
        code_hash = self._hash_code(user_code)
        
        # Ensure container and get host address
        host_addr = self._ensure_container(code_hash, user_code)
        
        # Now call the run endpoint with retry
        url = f"http://{host_addr}/run"
        max_retries = 3
        retry_delay = 1
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=input_data, timeout=30)
                resp.raise_for_status()
                
                with self.lock:
                    if code_hash in self.containers:
                        self.containers[code_hash]["last_used"] = time.time()
                
                return resp.json()
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt+1}/{max_retries} to run code failed: {e}")
                if attempt < max_retries - 1:  # Don't sleep after the last attempt
                    time.sleep(retry_delay)
        
        # If we got here, all attempts failed
        raise RuntimeError(f"Failed to run code after {max_retries} attempts: {last_exception}")

    def _cleanup_idle(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            containers_to_remove = []
            
            with self.lock:
                for code_hash, meta in list(self.containers.items()):
                    if now - meta["last_used"] > self.ttl_seconds:
                        containers_to_remove.append((code_hash, meta["name"]))
            
            # Remove containers outside the lock to minimize lock contention
            for code_hash, name in containers_to_remove:
                try:
                    self.docker.remove_container(name)
                except Exception:
                    pass
                
                with self.lock:
                    self.containers.pop(code_hash, None)
                    
            for _ in range(10):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def shutdown(self):
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        
        # Get a copy of containers to clean up
        containers_to_remove = []
        with self.lock:
            for code_hash, meta in list(self.containers.items()):
                containers_to_remove.append((code_hash, meta["name"]))
            
        # Clean up containers
        for code_hash, name in containers_to_remove:
            try:
                self.docker.remove_container(name)
            except Exception:
                pass
            
            with self.lock:
                self.containers.pop(code_hash, None)
        
        try:
            self.docker.remove_network()
        except Exception:
            pass


_default_dispatcher: Optional[Dispatcher] = None
_dispatcher_lock = threading.Lock()

def get_default_dispatcher() -> Dispatcher:
    global _default_dispatcher
    with _dispatcher_lock:
        if _default_dispatcher is None:
            _default_dispatcher = Dispatcher()
        return _default_dispatcher


def run_in_docker(user_code: str, input_data: dict) -> dict:
    return get_default_dispatcher().run(user_code, input_data)


# Ensure the default dispatcher is shut down at process exit
def _shutdown_default_dispatcher() -> None:
    global _default_dispatcher
    with _dispatcher_lock:
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
