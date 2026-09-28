# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import re
from pathlib import Path

from duckdb.sqltypes import DuckDBPyType
from pandas.api.types import (
    is_datetime64_dtype,
    is_float_dtype,
    is_integer_dtype,
    is_string_dtype,
)
import geopandas as gpd


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


def clean_str(s: str) -> str:
    return re.sub(r"[^a-z0-9._-]", "", s.strip().lower())


def find_geo_cols(resource, df): 
    """
    find geometry data in dataframe columns
    returns an empty array if no geo_cols have been found
    """
    geo_cols = [
        f.name
        for f in resource.schema.fields
        if f.type == "geojson"
        and f.name in df.columns
        and df[f.name].notna().any()
    ]

    return geo_cols


def convert_df_to_geodf(df, geo_cols):
    """
    Convert a Dataframe into GeoDataframe
    GeoPandas only supports one active geometry column in a GeoDataFrame.
    Convert any additional geo columns into WKB strings so parquet export can succeed.
    """
    for col in geo_cols[1:]:
        df[col] = df[col].apply(
            lambda geom: geom.wkb if geom is not None else None
        )

    return gpd.GeoDataFrame(df, geometry=geo_cols[0], crs="EPSG:4326")