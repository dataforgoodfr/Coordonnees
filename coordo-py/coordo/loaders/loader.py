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


class Loader(ABC):
    def __init__(self, package: Path, action: ResourceAction):
        self.dp = DataPackage.from_path(package)
        self.action = action
        self.resources: list[Resource] = []

    def etl(self):
        self.extract()
        self.handle_resources()
        if self.action in [ResourceAction.ADD, ResourceAction.UPDATE]:
            self.transform()
            self.load()
        self.dp.save()

    def handle_resources(self):
        for resource in self.resources:
            if self.action == ResourceAction.ADD:
                self.dp.add_resource(resource)
            elif self.action == ResourceAction.UPDATE:
                self.dp.update_resource(resource)
            elif self.action == ResourceAction.REMOVE:
                self.dp.remove_resource(resource.name)

    @abstractmethod
    def extract(self):
        raise NotImplementedError()

    @abstractmethod
    def transform(self):
        raise NotImplementedError()

    @abstractmethod
    def load(self):
        raise NotImplementedError()
