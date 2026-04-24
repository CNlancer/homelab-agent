from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from homelab_agent.models.task import TaskSpec


ActionHandler = Callable[[TaskSpec], dict]


@dataclass(frozen=True)
class RegisteredAction:
    executor_name: str
    action_name: str
    handler: ActionHandler


class ActionRouter:
    def __init__(self) -> None:
        self._handlers: Dict[Tuple[str, str], ActionHandler] = {}

    def register(self, executor_name: str, action_name: str, handler: ActionHandler) -> None:
        self._handlers[(executor_name, action_name)] = handler

    def resolve(self, task: TaskSpec) -> RegisteredAction:
        key = (task.target_type, task.action)
        handler = self._handlers.get(key)
        if handler is None:
            joined = ".".join(key)
            raise KeyError("unregistered action: {0}".format(joined))
        return RegisteredAction(
            executor_name=task.target_type,
            action_name=task.action,
            handler=handler,
        )
