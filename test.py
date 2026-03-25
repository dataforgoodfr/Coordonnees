from coordo.sql.mapper import FieldMapper
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table

metadata = MetaData()

Table(
    "parents",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("some_column", String),
    Column("other_column", String),
)

Table(
    "children",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("parent_id", Integer, ForeignKey("parents.id")),
    Column("another_column", String),
)
mapper = FieldMapper("parents", metadata)

print(mapper["some_column"])
# parents.some_column
print(mapper["children"]["another_column"])
# children.other_column

from coordo.sql.parser import parse, to_sql

ast = parse("centroid(some_column if other_column > 5)")
sql = to_sql(ast, mapper)
print(compile(sql))

from coordo.sql.builder import build_query, compile

query = build_query(metadata, "parents")
print(compile(query))
# SELECT parents.id, parents.some_column, parents.other_column
# FROM parents

query = build_query(
    metadata,
    "parents",
    {"location": parse("centroid(children.another_column)")},
)
print(compile(query))
# SELECT st_centroid(CASE WHEN (parents.other_column > 5.0) THEN parents.some_column END) AS st_centroid_1
# FROM parents

query = build_query(
    metadata,
    "parents",
    {"mean": "avg(children.another_column)"},
)
print(compile(query))

query = build_query(
    metadata,
    "parents",
    {"mean": "avg(children.another_column)"},
    groupby=["some_column"],
)
print(compile(query))
