# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum

from ..datapackage import DataPackage
from ..datapackage.resource import Resource


class ResourceAction(str, Enum):
    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"

class Separator(str, Enum):
    COMMA = ","
    SEMICOLON = ";"
    TAB = "\t"
    PIPE = "|"
    DOT = "."
    
class Loader(ABC):
    def __init__(self, package: Path, action: ResourceAction):
        self.dp = DataPackage.from_path(package)
        self.action = action
        self.resources: list[Resource] = []

    def add(self):
        """
        Extract the corresponding resources to add, transform, and load them into the package.
        """
        self.extract_and_get_resources()
        for resource in self.resources:
            self.dp.attach_resource(resource)
        self.transform()
        self.load()
        self.save()

    def remove(self):
        """
        Extract the correct resources to remove, then remove them from the package.
        """
        self.extract_and_get_resources()
        for resource in self.resources:
            self.dp.remove_resource(resource.name)
        self.save()

    @abstractmethod
    def extract_and_get_resources(self):
        """
        Extract data and resources from the source and populate the `resources` list.
        """
        raise NotImplementedError()

    def transform(self):
        """
        Optional step to transform the resources.
        """
        pass

    @abstractmethod
    def load(self):
        """
        Load physically resources into the package.
        """
        raise NotImplementedError()


    def save(self):
        """
        Invoke the package's save method, which updates the datapackage.json file on disk.
        """
        self.dp.save()
