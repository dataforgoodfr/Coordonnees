 # coordo-py

This is the Python side of coordo. It is divided in 3 main modules :

## sql

Let's start with some SQLAlchemy tables
```py
from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey

metadata = MetaData()

Table("parents", metadata,
    Column("id", Integer, primary_key=True),
    Column("some_column", String),
    Column("other_column", String),
)

Table("children", metadata,
    Column("id", Integer, primary_key=True),
    Column("parent_id", Integer, ForeignKey('parents.id')),
    Column("another_column", String),
)
```

You can then use the field mapper to naturally access columns and reverse relationships
```py
from coordo.sql.mapper import FieldMapper

mapper = FieldMapper("parents", metadata)

>>> mapper["some_column"]
Column('some_column', String(), table=<parents>)

>>> mapper["children"]["another_column"]
Column('another_column', String(), table=<children>)
```

PS: if you are using the SQLAlchemy ORM you can use `Base.metadata`

Using this field mapper you can then parse an expression using our simplified language
```py
from coordo.sql.parser import parse
from coordo.sql.evaluator import to_sql
from coordo.sql.builder import compile_query


ast = parse("centroid(some_column if other_column > 5)")
expr, joins = to_sql(ast, mapper)
>>> print(compile_query(expr))
st_centroid(CASE WHEN (parents.other_column > 5.0) THEN parents.some_column END)
```

You can also use expressions with the query builder

```py
from coordo.sql.builder import build_query

query = build_query(metadata, "parents")
>>> print(compile_query(query))
SELECT parents.id, parents.some_column, parents.other_column
FROM parents
```

Reverse relationships are automatically left-joined

```py
query = build_query(
    metadata,
    "parents",
    {"location": parse("centroid(children.another_column)")},
)

>>> print(compile_query(query))
SELECT st_centroid(children.another_column) AS location
FROM parents LEFT OUTER JOIN children ON parents.id = children.parent_id
```

Aggregations are automatically wrapped in CTEs

```py
query = build_query(
    metadata,
    "parents",
    {"mean": parse("avg(children.another_column)")},
)

>>> compile(query)
WITH anon_1 AS
 (SELECT avg(children.another_column) AS avg_1
FROM parents LEFT OUTER JOIN children ON parents.id = children.parent_id)
 SELECT anon_1.avg_1
FROM anon_1
```
