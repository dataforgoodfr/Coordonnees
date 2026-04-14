# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from abc import ABC, abstractmethod
from pathlib import Path

from ..datapackage import DataPackage, ResourceExistsStrategy
from ..datapackage.resource import Resource


class Loader(ABC):
    def __init__(self, package: Path, strategy: ResourceExistsStrategy):
        self.dp = DataPackage.from_path(package)
        self.strategy = strategy
        self.resources: list[Resource] = []

    def add_resources_to_datapackage(self):
        for resource in self.resources:
            self.dp.add_resource(resource, self.strategy)

    def etl(self):
        self.extract()
        self.add_resources_to_datapackage()
        self.transform()
        self.load()
        self.dp.save()

    @abstractmethod
    def extract(self):
        raise NotImplementedError()

    @abstractmethod
    def transform(self):
        raise NotImplementedError()

    @abstractmethod
    def load(self):
        raise NotImplementedError()
