"""Library package for lambda-poc dispatcher functionality.

Expose a Dispatcher class and a module-level convenience function
`run_in_docker` for backward compatibility.
"""
from .dispatcher import Dispatcher, get_default_dispatcher, run_in_docker

__all__ = ["Dispatcher", "get_default_dispatcher", "run_in_docker"]
