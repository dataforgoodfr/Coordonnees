#  Coordonnées

#  Dependencies

You will need the following dependencies in order to use SpatialLite : 

Ubuntu / Debian
```
sudo apt-get install gdal-bin libgdal-dev libsqlite3-mod-spatialite
```

# Repo structure

This package aims at greatly simplifying the manipulation and transformation of geospatial data and the creation of interactive [map]s from data sources. It is based on 2 inter-dependent modules that are made to work together :

The **js** folder contains the Javascript part of the project, it is basically a wrapper around MapLibre, which offers a simplified API for JS developers and add some fonctionalities (popups, hovering, events).

The **python** folder contains the Python part of the project, it is capable of parsing a config format (TODO: define the JSON schema of the config) and automatically pulling data from sources and generating an augmented MapLibre Style Spec file, which can be used by the Javascript module.


#  Docker image

In case you cannot or do not want to install the system-wide dependencies, you can use the provided Dockerfile to build a Docker image containing:
* gdal-bin 
* libgdal-dev 
* libsqlite3-mod-spatialite
* uv

Build the Docker image using:

```
docker build -t coord .
```

Then launch an interactive shell in the Docker container using:

```
docker run --rm -it -v $(pwd):/app -p 8000:8000 coord
```

Inside the container, you must use 0.0.0.0 instead of 127.0.0.1:

```
cd demo
uv run manage.py runserver 0.0.0.0:8000
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
```
uv run coordo load kobotoolbox catalog/ data/20250213_Inventaire_ID_QuestionnaireK.xlsx data/20251017_Inventaire_ID_Donnees.xlsx
uv run coordo load kobotoolbox catalog/ data/20240808_EnqueteMenage_CDF_QuestionnaireK.xlsx data/20241007_EnqueteMenage_CDF_Donnees.csv
```

Serve a config file
```
uv run coordo serve data/config.json
```

In order to read SQLite files, we recommend using [DBeaver](https://dbeaver.io/download/#requirements)
