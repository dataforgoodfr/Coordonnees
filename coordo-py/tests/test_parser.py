# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey

from coordo.sql.mapper import FieldMapper
from coordo.syntax_parsers import sql_parser
from coordo.sql.evaluator import to_sql
from coordo.sql.builder import compile_query


def test_sql_mapper_and_parser():
    metadata = MetaData()
    parent_table = Table(
        "parents",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("some_column", String),
        Column("other_column", String),
    )
    children_table = Table(
        "children",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parents.id")),
        Column("another_column", String),
    )
    mapper = FieldMapper("parents", metadata)

    assert mapper["some_column"] is parent_table.c.some_column
    assert mapper["children"]["another_column"] == children_table.c.another_column

    ast = sql_parser.parse("centroid(some_column if other_column > 5)")
    expr, joins = to_sql(ast, mapper)
    assert (
        compile_query(expr)
        == "st_centroid(CASE WHEN (parents.other_column > 5.0) THEN parents.some_column END)"
    )
