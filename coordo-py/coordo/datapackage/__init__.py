# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from .package import DataPackage, Field, ForeignKeyReference, ResourceExistsStrategy
from .resource import ForeignKey, Resource, Schema

__all__ = [
    "DataPackage",
    "Resource",
    "Field",
    "Schema",
    "ForeignKey",
    "ForeignKeyReference",
    "ResourceExistsStrategy",
]
