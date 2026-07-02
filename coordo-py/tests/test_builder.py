from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    text,
    column,
)

from coordo.sql import builder


def _mk_metadata():
    md = MetaData()
    Table(
        "mytable",
        md,
        Column("id", Integer, primary_key=True),
        Column("value", Integer),
    )
    Table(
        "othertable",
        md,
        Column("id", Integer, primary_key=True),
        Column("ref", Integer),
        Column("val", Integer),
    )
    return md


def test_build_query_ungrouped_label_text():
    md = _mk_metadata()

    def fake_to_sql(ast, field_map, base_query):
        return (text("'N/A'"), [])

    orig = builder.to_sql
    builder.to_sql = fake_to_sql
    try:
        q = builder.build_query(md, "mytable", columns={"status": None})
        s = builder.compile_query(q)
    finally:
        builder.to_sql = orig

    assert "'N/A'" in s and "status" in s


def test_build_query_grouped_uses_any_value():
    md = _mk_metadata()

    def fake_to_sql(ast, field_map, base_query):
        return (column("value"), [])

    orig = builder.to_sql
    builder.to_sql = fake_to_sql
    try:
        q = builder.build_query(md, "mytable", columns={"avgv": None}, groupby=["id"])
        s = builder.compile_query(q)
    finally:
        builder.to_sql = orig

    assert "any_value" in s.lower() and "avgv" in s


def test_build_query_adds_joins():
    md = _mk_metadata()
    othertable = md.tables["othertable"]
    mytable = md.tables["mytable"]

    def fake_to_sql(ast, field_map, base_query):
        return (othertable.c.val, [(othertable, mytable.c.id == othertable.c.ref)])

    orig = builder.to_sql
    builder.to_sql = fake_to_sql
    try:
        q = builder.build_query(md, "mytable", columns={"v": None})
        s = builder.compile_query(q)
    finally:
        builder.to_sql = orig

    assert "left outer join" in s.lower() or "left join" in s.lower()


if __name__ == "__main__":
    test_build_query_ungrouped_label_text()
    test_build_query_grouped_uses_any_value()
    test_build_query_adds_joins()
    print("ALL OK")
