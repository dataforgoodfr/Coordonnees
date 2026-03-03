from pathlib import Path

import duckdb

from ..datapackage import DataPackage, Field, Resource, Schema

DUCK_TO_DP_FIELDS = {
    "INTEGER": "integer",
    "VARCHAR": "string",
    "GEOMETRY": "geojson",
}


def load(dp: DataPackage, path: Path):
    conn = duckdb.connect()
    from_str = f'"{path}"'
    if path.suffix == ".geojson":
        conn.load_extension("spatial")
        from_str = f"ST_Read({from_str})"
    rel = conn.sql(f"SELECT * FROM {from_str}")
    schema = Schema()
    for name, type in zip(rel.columns, rel.types):
        schema.add_field(
            Field(
                type=DUCK_TO_DP_FIELDS[type],
                name=name,
            )
        )
    conn.close()
    dp.add_resource(
        Resource(
            name=path.stem,
            path=str(path),
            schema=schema,
        )
    )
    print(dp)
