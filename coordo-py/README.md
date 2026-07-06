 # coordo-py

This is the Python side of coordo. It can be used to:
- parse data (Excel, CSV / TSV, Kobotoolbox) and populate a DataPackage
- read with a Datapackage
- translate `coordo`-like syntax in SQL

## Datapackage

A Datapackage is composed of resources, which are the equivalent of tables in standard relational databases.
Each resource is stored as a `.parquet` file in the Datapackage. Resources can be linked with one another using foreign keys.

Resources can be created on the fly after parsing input data and determining their schema.
Likewise, by parsing input data and determining the underlying resources, one can:
- remove the associated resources if they exist
- append the newly parsed input data to the existing resources
- replace the the existing resources by the newly parsed input data

It is also possible to:
- remove individual resources
- delete all data for a specific resource (but the resource, its schema and foreign keys are kept)

>[!WARNING]
>If resources are linked to other resources by foreign keys, removing them will raise an error. 
>In such case, you'll have to remove the foreign keys beforehand. 
>Once the foreign keys wre removed individually, you can safely remove the resources.

As of now, the following types of input data can be used to populate a `coordo` Datapackage:
- Kobotoolbox data
- Excel files
- CSV / TSV files (or any file containing data separated by a character)


## Usage

### Resources

Add a new resource and populate it with parsed data:
```
coordo add <type of input> <arguments> --package <path/to/datapackage>
```

Remove a resource corresponding to the input data:
```
coordo remove <type of input> <arguments> --package <path/to/datapackage>
```

>[!TIP]
>One can also do:
>```
>coordo remove resource <name of resource> --package <path/to/datapackage>
>```

Append data to existing resources:
```
coordo append <type of input> <arguments> --package <path/to/datapackage>
```

Replace data of existing resources by new data (the resource schemas stay unchanged):
```
coordo replace <type of input> <arguments> --package <path/to/datapackage>
```

Delete all data in a resource (but keep its schema and foreign keys):
```
coordo delete resource <name of resource> --package <path/to/datapackage>
```


### Foreign keys

Add new foreign keys from one resource to another one:
```
coordo add foreignkey <source resource>.<field name> <target resource>.<field name> --package <path/to/datapackage>
```

The command to remove it is almost the same:
```
coordo remove foreignkey <source resource>.<field name> <target resource>.<field name> --package <path/to/datapackage>
```

### Examples

#### Kobotoolbox

To add / remove / append / replace a new Datapackage resource with Kobotoolbox data, you can use the command line:
```
coordo add kobotoolbox <path/to/form (`.xlsx` format)> <path/to/data (`.xlsx` format)> --package <path/to/datapackage>
```

This is the API equivalent:
```py
from pathlib import Path
from coordo.loaders import KoboToolboxLoader

package = "path/to/datapackage"
xlsform = "path/to/form (`.xlsx` format)"
xlsdata = "path/to/data (`.xlsx` format)"

kb = KoboToolboxLoader(package, xlsform, xlsdata)
kb.add()
kb.remove()
kb.append()
kb.replace()
```

#### File (Excel / character-separated)

To add / remove / append / replace a new Datapackage resource with data from a single file, you can use the command line:
```
coordo add file <path/to/file> --package <path/to/datapackage>
```

and its API equivalent:
```py
from pathlib import Path
from coordo.loaders import get_file_loader

package = "path/to/datapackage"
file = "path/to/file"

file_loader = get_file_loader(package, file)
file_loader.add()
file_loader.remove()
file_loader.append()
file_loader.replace()
```

#### Remove resource / detelete resource data using the API

```py
from pathlib import Path
from coordo.loaders import Loader

package = "path/to/datapackage"
resource_name = "bye_bye_resource"

# delete all data from this resource
Loader.delete_data_from_resource(package, resource_name)

# or if you want to delete this resource altogether
Loader.remove_one_resource(package, resource_name)
```

#### Foreign keys

```
coordo add file file1.csv --package catalog/mydatapackage
coordo add file file2.csv --package catalog/mydatapackage
coordo add foreignkey file1.colA file2.colB --package catalog/mydatapackage
coordo remove foreignkey file1.colA file2.colB --package catalog/mydatapackage
```

or using the API:


### Specific use cases

#### Kobotoolbox





To remove resources corresponding to Kobotoolbox data:
```
coordo remove kobotoolbox <path/to/form (`.xlsx` format)> <path/to/data (`.xlsx` format)> --package <path/to/datapackage>
```

or using the API:
```py
from pathlib import Path
from coordo.loaders import KoboToolboxLoader

package = Path("path/to/datapackage")
xlsform = Path("path/to/form (`.xlsx` format)")
xlsdata = Path("path/to/data (`.xlsx` format)")

KoboToolboxLoader(package, xlsform, xlsdata).add()
```





## Parse data and populate a Datapackage






### Syntax parsers

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
from coordo.syntax_parsers import sql_parser
from coordo.sql.evaluator import to_sql
from coordo.sql.builder import compile_query

ast = sql_parser.parse("centroid(some_column if other_column > 5)")
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


## Development

### Testing

To run the pytest tests, simply run in `coordo-py` directory:

```bash
pytest
```

### Data types

#### KoboToolbox

For surveys, Kobotoolbox uses the standard XLSForm format.
Briefly, each `xlsx` file contains 3 sheets:
- `survey`
- `choices`
- `settings`

All information can be found at https://support.kobotoolbox.org/edit_forms_excel.html
