import shutil
from pathlib import Path

from ..datapackage import DataPackage, Field, Resource, Schema
from ..datapackage.db_helpers import prepare_path, to_dp_type


def load(dp: DataPackage, path: Path, overwrite = False):
    query = f"SELECT * FROM {prepare_path(path)}"
    conn, _ = dp.prepare_db()
    rel = conn.sql(query)
    schema = Schema()
    for name, type in zip(rel.columns, rel.types):
        schema.add_field(
            Field(
                type=to_dp_type(type),
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
    shutil.copy(path, dp._basepath / path.name)
