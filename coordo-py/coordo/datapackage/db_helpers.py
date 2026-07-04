# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from pandas.api.types import (
    is_integer_dtype,
    is_float_dtype,
    is_string_dtype,
    is_datetime64_dtype,
)
from duckdb.sqltypes import DuckDBPyType


def prepare_path(path: Path):
    from_ = str(path)
    if path.suffix in (".geojson", ".zip"):
        if path.suffix == ".zip":
            from_ = "/vsizip/" + from_
        from_ = f"ST_Read('{from_}')"
    else:
        from_ = f'"{from_}"'
    return from_


def duckdb_type_to_dp_type(type: DuckDBPyType) -> dict:
    match type.id:
        case "bigint" | "integer":
            return {"type": "integer"}
        case "geometry":
            return {"type": "geojson"}
        case "double":
            return {"type": "number"}
        case "date":
            return {"type": "date"}
        case "list":
            return {"type": "list", "itemType": type.children[0]}
        case _:
            return {"type": "string"}


def pandas_type_to_dp_type(type: str) -> dict:
    """
    Convert a pandas type to a Data Package type.
    Note that pandas parses list columns as object,
    and that pandas (unlike Geopandas) does not have a built-in dtype of geometry data.
    """
    if is_integer_dtype(type):
        return {"type": "integer"}
    elif is_float_dtype(type):
        return {"type": "number"}
    elif is_string_dtype(type):
        return {"type": "string"}
    elif is_datetime64_dtype(type):
        return {"type": "date"}
    else:
        return {"type": "string"}
