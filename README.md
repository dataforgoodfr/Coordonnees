#  Coordonnées

#  Dependencies

You will need the following dependencies in order to use SpatialLite : 

Ubuntu / Debian
```
sudo apt-get install gdal-bin libgdal-dev libsqlite3-mod-spatialite
```

# Repo structure

This package aims at greatly simplifying the manipulation and transformation of geospatial data and the creation of interactive maps from data sources. It is based on 2 inter-dependent modules that are made to work together :

The **js** folder contains the Javascript part of the project, it is basically a wrapper around MapLibre, which offers a simplified API for JS developers and add some fonctionalities (popups, hovering, events).

The **python** folder contains the Python part of the project, it is capable of parsing a config format (TODO: define the JSON schema of the config) and automatically pulling data from sources and generating an augmented MapLibre Style Spec file, which can be used by the Javascript module.

The **demo** folder show an example of how you could use those packages to build a geospatial platform. You can run the following commands to get started :

```
uv run manage.py import_test_data
uv run manage.py runserver
```

This is also useful for debugging, the python coordo lib is in editable mode so any modification the the python folder wille be taken into account in demo folder. For the js side you need to run `make build-js` to sync the modification to the demo folder.

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
pip install git+https://github.com/dataforgoodfr/Coordonnees.git/#subdirectory=python
```

Javascript
```
npm install git+https://github.com/dataforgoodfr/Coordonnees.git#master
```

# Quick demo

For development or to see an example of an app using both the Python and Javascript packages, you can run

```
cd demo
uv run manage.py runserver
```

In order to read SQLite files, we recommend using [DBeaver](https://dbeaver.io/download/#requirements)
