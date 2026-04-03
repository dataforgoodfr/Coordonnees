# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import re
from pathlib import Path

import duckdb

AGGREGATES_SQL = (Path(__file__).parent / "aggregates.sql").read_text()


def load_conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect()
    conn.install_extension("SPATIAL")
    conn.load_extension("SPATIAL")
    conn.execute(AGGREGATES_SQL)
    return conn


AGGREGATES_MACROS = set(
    map(
        lambda s: s.lower(),
        re.findall(r"CREATE(?: OR REPLACE)? MACRO (\w+)\s?\(", AGGREGATES_SQL),
    )
)
AGGREGATES_FUNCTIONS = set(
    load_conn()
    .sql(
        "SELECT DISTINCT lower(function_name) AS name FROM duckdb_functions() WHERE function_type = 'aggregate'"
    )
    .to_df()["name"]
)
AGGREGATES = AGGREGATES_MACROS.union(AGGREGATES_FUNCTIONS)

SPATIAL_FUNCTIONS = set(
    load_conn()
    .sql(
        "SELECT DISTINCT lower(function_name)[4:] AS name FROM duckdb_functions() WHERE function_name LIKE 'ST_%'"
    )
    .to_df()["name"]
)
