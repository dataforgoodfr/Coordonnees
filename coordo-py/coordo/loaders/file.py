import shutil
from pathlib import Path

from ..datapackage import DataPackage, Field, Resource, Schema
from ..datapackage.db_helpers import prepare_path


def load(dp: DataPackage, path: str):
    query = f"SELECT * FROM {prepare_path(path)}"
    conn = dp.prepare_db()
    rel = conn.sql(query)
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
            path=path.name,
            schema=schema,
        )
    )
    shutil.copy(path, dp.basepath / path.name)
