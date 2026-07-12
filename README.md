# Coordonnées

# Repo structure

This package aims at greatly simplifying the manipulation and transformation of geospatial data and the creation of interactive [map]s from data sources. It is based on 2 inter-dependent modules that are made to work together :

The **js** folder contains the Javascript part of the project, it is basically a wrapper around MapLibre, which offers a simplified API for JS developers and add some fonctionalities (popups, hovering, events).

The **python** folder contains the Python part of the project, it is capable of parsing a config format (TODO: define the JSON schema of the config) and automatically pulling data from sources and generating an augmented MapLibre Style Spec file, which can be used by the Javascript module.

# Python API

## Datapackages

A Datapackage is composed of resources, which are the equivalent of tables in standard relational databases.
Each resource is stored as a `.parquet` file in the Datapackage. Resources can be linked with one another using foreign keys.

Resources can be created on the fly after parsing input data and determining their schema.
Likewise, by parsing input data and determining the underlying resources, one can:
- remove the associated resources if they exist
- append the newly parsed input data to the existing resources
- replace the existing resources by the newly parsed input data

It is also possible to:
- remove individual resources
- delete all data for a specific resource (but the resource, its schema and foreign keys are kept)

> [!WARNING]
> If resources are linked to other resources by foreign keys, removing them will raise an error. 
> In such case, you'll have to remove the foreign keys beforehand. 
> Once the foreign keys were removed individually, you can safely remove the resources.

As of now, the following types of input data can be used to populate a `coordo` Datapackage:
- Kobotoolbox data
- Excel files
- CSV / TSV files (or any file containing data separated by a character)


## Usage

### Resources

Add a new resource and populate it with parsed data:
```bash
coordo add <type of input> <arguments> --package <path/to/datapackage>
```

Remove a resource corresponding to the input data:
```bash
coordo remove <type of input> <arguments> --package <path/to/datapackage>
```

>[!TIP]
>One can also do:
>```bash
>coordo remove resource <name of resource> --package <path/to/datapackage>
>```

Append data to existing resources:
```bash
coordo append <type of input> <arguments> --package <path/to/datapackage>
```

Replace data of existing resources by new data (the resource schemas stay unchanged):
```bash
coordo replace <type of input> <arguments> --package <path/to/datapackage>
```

Delete all data in a resource (but keep its schema and foreign keys):
```bash
coordo delete resource <name of resource> --package <path/to/datapackage>
```


### Foreign keys

Add new foreign keys from one resource to another one:
```bash
coordo add foreignkey <source resource>.<field name> <target resource>.<field name> --package <path/to/datapackage>
```

The command to remove it is almost the same:
```bash
coordo remove foreignkey <source resource>.<field name> <target resource>.<field name> --package <path/to/datapackage>
```

### Examples

#### Kobotoolbox

> [!NOTE]
> For Kobotoolbox, a supplementary argument `--form <path/to/form (Excel file)>` **must be provided when adding / removing resources** and can be optionally supplied when updating data.

To add / remove / append / replace a new Datapackage resource with Kobotoolbox data, you can use the command line:
```bash
coordo < add / remove / append / replace > kobotoolbox <path/to/data (Excel file)> [--form <path/to/form (Excel file)>] --package <path/to/datapackage>
```

This is the API equivalent:
```py
from pathlib import Path
from coordo.loaders import KoboToolboxLoader

package = "path/to/datapackage"
xlsform = "path/to/form (Excel file)"
xlsdata = "path/to/data (Excel file)"

kb = KoboToolboxLoader(package, xlsform, xlsdata)
kb.add()
kb.remove()
kb.append()
kb.replace()
```

#### File (Excel / character-separated)

To add / remove / append / replace a new Datapackage resource with data from a single file, you can use the command line:
```bash
coordo < add / remove / append / replace > file <path/to/file> --package <path/to/datapackage>
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

#### Remove resource / delete resource data using the API

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

```bash
coordo add file file1.csv --package catalog/mydatapackage
coordo add file file2.csv --package catalog/mydatapackage
coordo add foreignkey file1.colA file2.colB --package catalog/mydatapackage
coordo remove foreignkey file1.colA file2.colB --package catalog/mydatapackage
```

or using the API:
```py
from pathlib import Path
from coordo.loaders import Loader

package = "path/to/datapackage"
source_field = "resourceA.colA"
target_field = "resourceB.colB"

# add
Loader.add_foreign_key(package, source_field, target_field)
# remove
Loader.remove_foreign_key(package, source_field, target_field)
```


## Map server

You can integrate coordo into any Python web framework.

First create the map object :

```py
from coordo.map import Map

map = Map.from_file(config_file)
```

Then simply use the .handle_request(path, method, data) to integrate it in your server. Here are some examples :

### Flask

```py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/maps/<path:subpath>")
def maps(subpath: str):
    return jsonify(
        map.handle_request(
            request.method,
            subpath,
            request.get_json(),
        )
    )
```

### Django

```py
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def my_map_view(request, subpath):
    return JsonResponse(
        map.handle_request(
            request.method,
            subpath,
            request.body
        )
    )

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('map/<path:subpath>/', views.map_view, name='map'),
]
```

# Install from other projects

This repo is still in very early stage so it is not yet published on registries, but you can still install the Python and Javascript packages with the following commands for testing

Python

```
pip install git+https://github.com/dataforgoodfr/Coordonnees.git#subdirectory=python
```

Javascript

```
npm install git+https://github.com/dataforgoodfr/Coordonnees.git
```

# CLI

For development or to quickly test the library

Install

```
uv venv
uv pip install -e coordo-py
make build
```

Import data into catalog

```bash
AWS_ACCESS_KEY_ID=<access_key_id> AWS_SECRET_ACCESS_KEY=<secret_access_key> aws s3 sync s3://coordonnees-upload ./data --delete --endpoint-url https://s3.fr-par.scw.cloud --region fr-par
make catalog
```

Serve a config file

```
uv run coordo serve configs/all4trees_config.json
```
