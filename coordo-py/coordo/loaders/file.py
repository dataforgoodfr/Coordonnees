from pathlib import Path

import duckdb

from ..datapackage import Schema

DUCK_TO_DP_FIELDS = {"integer"}


def load(path: Path):
    conn = duckdb.connect()
    from_str = f'"{path}"'
    if path.suffix == ".geojson":
        conn.load_extension("spatial")
        from_str = f"ST_Read({from_str})"
    description = conn.sql(f"SELECT * FROM {from_str}").description
    schema = Schema()
    print(description)
    for desc in description:
        col_name = desc[0]
        col_type = desc[1]
        print(col_name, col_type)
    conn.close()
