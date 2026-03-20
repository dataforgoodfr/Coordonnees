from pathlib import Path

from dplib.models.field.types import IField


def prepare_path(path: Path):
    from_ = str(path)
    if path.suffix in (".geojson", ".zip"):
        if path.suffix == ".zip":
            from_ = "/vsizip/" + from_
        from_ = f"ST_Read('{from_}')"
    else:
        from_ = f'"{from_}"'
    return from_


def to_db_type(field: IField):
    match field.type:
        case "integer":
            return "INTEGER"
        case "string":
            return "VARCHAR"
        case "geojson":
            return "GEOMETRY"
        case "number":
            return "DOUBLE"
        case "date":
            return "DATE"
        case "list":
            return field.itemType + "[]"  # type: ignore
