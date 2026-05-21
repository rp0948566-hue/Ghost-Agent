import functools
from typing import Callable, Dict, Any

_TASK_REGISTRY: Dict[str, Dict[str, Any]] = {}

def task(name: str, description: str = ""):
    """Decorator to register a browser task handler."""
    def decorator(fn: Callable) -> Callable:
        _TASK_REGISTRY[name] = {"fn": fn, "description": description}
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            return await fn(*args, **kwargs)
        return wrapper
    return decorator

class TaskRegistry:
    @staticmethod
    def get(name: str) -> Callable | None:
        entry = _TASK_REGISTRY.get(name)
        return entry["fn"] if entry else None

    @staticmethod
    def list_tasks() -> Dict[str, str]:
        return {k: v["description"] for k, v in _TASK_REGISTRY.items()}
