import json
from abc import abstractmethod
from pathlib import Path
from typing import ClassVar, Iterable, Optional

from pydantic import BaseModel
from pydantic import Field as PydanticField
from pygeofilter.ast import AstType as Filter


class Source(BaseModel):
    title: Optional[str]
    path: Optional[str]
    email: Optional[str]
    version: Optional[str]


class Dialect(BaseModel):
    header: Optional[bool] = None
    headerRows: Optional[list[str]] = None
    headerJoin: Optional[str] = None
    commentRows: Optional[list[str]] = None
    commentChar: Optional[str] = None
    delimiter: Optional[str] = None
    lineTerminator: Optional[str] = None
    quoteChar: Optional[str] = None
    doubleQuote: Optional[bool] = None
    escapeChar: Optional[str] = None
    nullSequence: Optional[str] = None
    skipInitialSpace: Optional[bool] = None
    property: Optional[str] = None
    itemType: Optional[str] = None
    itemKeys: Optional[list[str]] = None
    sheetNumber: Optional[int] = None
    sheetName: Optional[str] = None
    table: Optional[str] = None


class MissingValue(BaseModel):
    value: str
    label: str


class Reference(BaseModel):
    resource: str
    fields: list[str]


class ForeignKey(BaseModel):
    fields: list[str]
    reference: Reference


class Constraints(BaseModel):
    required: Optional[bool] = None
    unique: Optional[bool] = None


class Category(BaseModel):
    value: str
    label: str


class Field(BaseModel):
    name: str
    type: Optional[str] = None
    format: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None
    constraints: Optional[Constraints] = None
    categories: Optional[list[str | Category]] = None
    missingValues: Optional[list[str | MissingValue]] = None


class Schema(BaseModel):
    fields: list[Field] = PydanticField(default_factory=list)
    missingValues: list[str | MissingValue] = PydanticField(default_factory=list)
    primaryKey: Optional[str | list[str]] = None
    uniqueKeys: Optional[list[list[str]]] = None
    foreignKeys: list[ForeignKey] = PydanticField(default_factory=list)
    rdfType: Optional[str] = None


class Resource(BaseModel):
    name: str
    path: str
    # data: Optional["Data"] = None
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    sources: Optional[list[Source]] = None
    # licenses: Optional[list["License0"]] = None
    format: Optional[str] = None
    mediatype: Optional[str] = None
    encoding: Optional[str] = None
    bytes: Optional[int] = None
    hash: Optional[str] = None
    dialect: Dialect = PydanticField(default_factory=Dialect)
    schema: Schema = PydanticField(default_factory=Schema)  # type: ignore


class DataPackage(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    version: Optional[str] = None
    created: Optional[str] = None
    # contributors: Optional[list[Contributor]] = None
    keywords: Optional[list[str]] = None
    image: Optional[str] = None
    # licenses: Optional[list["License"]] = None
    resources: list[Resource] = PydanticField(default_factory=list)
    sources: Optional[list[Source]] = None

    _registry: ClassVar[dict[str, type["DataPackage"]]] = {}

    @classmethod
    def register(cls, fmt: str):
        def decorator(subclass):
            cls._registry[fmt] = subclass
            return subclass

        return decorator

    @classmethod
    def from_path(cls, path: Path | str) -> "DataPackage":
        path = Path(path)
        if path.is_dir():
            _path = path
            path = path / "datapackage.json"
        else:
            _path = path.parent
        dict = json.loads(path.read_text())
        # We only check the format of the first resource now but
        # we should improve this and do error handling
        fmt = dict["resources"][0]["format"]
        subclass = cls._registry.get(fmt)
        if not subclass:
            raise ValueError(f"No registered subclass for format {fmt}")
        self = subclass.from_dict(dict)
        self._path = _path
        return self

    @classmethod
    def from_dict(cls, dic: dict):
        return cls.model_validate(dic)

    def get_resource(self, name: str):
        return next(resource for resource in self.resources if resource.name == name)

    def write_schema(self, path: Path):
        if not path.exists():
            path.mkdir()
        elif not path.is_dir():
            raise Exception("Please provide a folder.")
        self._path = path
        schema_path = path / "datapackage.json"
        schema_path.write_text(self.model_dump_json(exclude_none=True, indent=2))

    @abstractmethod
    def write_data(self, resource_name: str, it: Iterable[dict]):
        if not self._path:
            raise Exception("You can't write to an unsaved datapackage.")

    @abstractmethod
    def read_data(
        self,
        resource_name: str,
        filter: Filter | None = None,
        groupby: list[str] | None = None,
        aggregate: dict[str, str] | None = None,
    ) -> Iterable[dict]:
        if not self._path:
            raise Exception("You can't read an unsaved datapackage.")
