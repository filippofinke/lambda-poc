"""Service abstractions over Docker client used by the Dispatcher.

This keeps the low-level docker interactions in a single place making the
Dispatcher class easier to test and reason about.
"""
from typing import Dict
import docker
import time
import logging

logger = logging.getLogger(__name__)


class DockerService:
    """Wrapper for simple Docker operations used by the dispatcher."""

    def __init__(self, network: str):
        self.client = docker.from_env()
        self.network = network

    def ensure_network(self):
        try:
            self.client.networks.get(self.network)
        except docker.errors.NotFound:
            self.client.networks.create(self.network)

    def get_container(self, name: str):
        return self.client.containers.get(name)

    def run_container(self, image: str, name: str, ports: Dict[str, int]):
        return self.client.containers.run(
            image, name=name, network=self.network, detach=True, ports=ports, auto_remove=True
        )

    def remove_container(self, name: str):
        try:
            cont = self.client.containers.get(name)
            try:
                cont.kill()
            except Exception:
                pass
            try:
                cont.remove()
            except Exception:
                pass
        except docker.errors.NotFound:
            pass

    def remove_network(self):
        try:
            net = self.client.networks.get(self.network)
            try:
                net.remove()
            except Exception:
                pass
        except Exception:
            pass
