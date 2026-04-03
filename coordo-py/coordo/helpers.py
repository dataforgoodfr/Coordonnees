# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from typing import Any, TypeVar

T = TypeVar("T")


def safe(obj: Any, attr: str) -> T:
    value = getattr(obj, attr)
    if value is None:
        raise ValueError(f"{attr} is required but was None")
    return value
