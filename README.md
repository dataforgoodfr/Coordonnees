#  Coordonnées

#  System Dependencies

You will need the following dependencies in order to use SpatialLite : SQLite, Spatialite, GDAL.

## Ubuntu / Debian

SQLite should be installed on the system by default.

```
sudo apt-get install gdal-bin libgdal-dev libsqlite3-mod-spatialite
```

## MacOS

There should already be a system version of SQLite but in a version that does not support extensions
which means you will need to install another version. This can be done via Brew.

```
brew update
brew install sqlite3
brew install libspatialite
brew install spatialite-tools
brew install gdal
```

After that you need to make sure that version of SQLite is used by adding it to your `PATH`. If you're using ZSH this can be done with:

```
echo "export PATH=\"$(brew --prefix)/opt/sqlite/bin:\$PATH\"" >> ~/.zshrc
```

Finally, SQLite needs to be able to find the Spatialite library installed by Brew. Peewee does not
seem to use the `SPATIALITE_LIBRARY_PATH` environment variable unfortunately. For running commands
locally using uv a workaround is to symlink it to the Python install managed by uv.

  * Find the root folder used by uv with `uv python dir`.
  * Find the version of Python used for this project
  * Synlink Spatialite with
    `ln -s $(brew --prefix)/lib/mod_spatialite.dylib $(uv python dir)/<PYTHON_VERSION>/lib/mod_spatialite.dylib`

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
