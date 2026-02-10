from dataclasses import dataclass, field
from typing import (
    Any,
    Generic,
    List,
    Literal,
    Optional,
    TypedDict,
    TypeVar,
    Union,
)

from dataclasses_json import DataClassJsonMixin


class Constraints(TypedDict, total=False):
    required: bool
    unique: bool


class IntegerConstraints(Constraints):
    minLength: int
    maxLength: int


@dataclass
class MissingValue:
    value: str
    label: str


class Reference(TypedDict):
    resource: str
    fields: List[str]


@dataclass
class ForeignKey:
    fields: list[str]
    reference: Reference


T = TypeVar("T")


@dataclass
class Category(Generic[T]):
    value: T
    label: str


@dataclass
class Field:
    name: str
    type: Optional[str] = None
    type: Optional[str] = None
    format: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None
    constraints: Constraints = field(default_factory=Constraints)
    missingValues: list[str | MissingValue] = field(default_factory=list)


@dataclass
class Schema:
    fields: list[Field] = field(default_factory=list)
    missingValues: list[str | MissingValue] = field(default_factory=list)
    primaryKey: Optional[str | list[str]] = None
    uniqueKeys: Optional[list[list[str]]] = None
    foreignKeys: list[ForeignKey] = field(default_factory=list)
    rdfType: Optional[str] = None


@dataclass
class StringField(Field):
    type: str = "string"
    categories: list[str | Category[str]] = field(default_factory=list)
    categoriesOrdered: Optional[bool] = None
    format: (
        Literal["default"]
        | Literal["email"]
        | Literal["uri"]
        | Literal["binary"]
        | Literal["uuid"]
    ) = "default"


@dataclass
class IntegerField(Field):
    type: str = "integer"
    categories: list[str | Category[int]] = field(default_factory=list)
    categoriesOrdered: Optional[bool] = None


@dataclass
class NumberField(Field):
    type: str = "number"


@dataclass
class DateField(Field):
    type: str = "date"


@dataclass
class TimeField(Field):
    type: str = "time"


@dataclass
class DatetimeField(Field):
    type: str = "datetime"


@dataclass
class GeopointField(Field):
    type: str = "geopoint"


Contributor = Union[str, int | float, "_ContributorObject", list[Any], bool, None]
DELIMITER_DEFAULT = ","
DOUBLE_QUOTE_DEFAULT = True
Data = str | int | float | dict[str, Any] | list[Any] | bool | None


@dataclass
class Dialect:
    header: Optional[bool] = None
    headerRows: Optional[List[str]] = None
    headerJoin: Optional[str] = None
    commentRows: Optional[List[str]] = None
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
    itemKeys: Optional[List[str]] = None
    sheetNumber: Optional[int] = None
    sheetName: Optional[str] = None
    table: Optional[str] = None


@dataclass
class Resource:
    name: str
    path: str
    data: Optional["Data"] = None
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    sources: Optional[List["Source"]] = None
    licenses: Optional[List["License0"]] = None
    format: Optional[str] = None
    mediatype: Optional[str] = None
    encoding: Optional[str] = None
    bytes: Optional[int] = None
    hash: Optional[str] = None
    dialect: Dialect = field(default_factory=Dialect)
    schema: Schema = field(default_factory=Schema)


@dataclass
class Source:
    title: str | None
    path: str | None
    email: str | None
    version: str | None


@dataclass
class Package(DataClassJsonMixin):
    name: Optional[str] = None
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    version: Optional[str] = None
    created: Optional[str] = None
    contributors: Optional[List[Contributor]] = None
    keywords: Optional[List[str]] = None
    image: Optional[str] = None
    licenses: Optional[List["License"]] = None
    resources: List[Resource] = field(default_factory=list)
    sources: Optional[List[Source]] = None

    def to_dict(self, encode_json=False):
        def remove_falsy(obj):
            if isinstance(obj, dict):
                return {
                    k: remove_falsy(v)
                    for k, v in obj.items()
                    if v or isinstance(v, bool)
                }
            if isinstance(obj, list):
                return [remove_falsy(v) for v in obj]
            return obj

        return remove_falsy(super().to_dict(encode_json))


class License(TypedDict, total=False):
    name: str
    path: str
    title: str


class License0(TypedDict, total=False):
    name: str
    path: str
    title: str


class Source0(TypedDict, total=False):
    title: str
    path: str
    email: str
    version: str


class _ContributorObject(TypedDict, total=False):
    title: str

    path: str

    email: str

    givenName: str
    familyName: str
    organization: str
    roles: list[str]
