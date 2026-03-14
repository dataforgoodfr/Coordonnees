from collections import UserDict
from typing import Any, TypeVar

T = TypeVar("T")


def safe(obj: Any, attr: str) -> T:
    value = getattr(obj, attr)
    if value is None:
        raise ValueError(f"{attr} is required but was None")
    return value


class StrictDict(UserDict):
    def __setitem__(self, key, item):
        if key in self.data:
            raise KeyError(f"Registry collision: '{key}' is already set.")
        super().__setitem__(key, item)
