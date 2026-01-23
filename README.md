#  Context


#  Dependencies

You will need the following dependencies in order to use SpatialLite : 

```
sudo apt-get install gdal-bin libgdal-dev libsqlite3-mod-spatialite
```

# Importing 

This package is divided in a Python and a Javascript module, since it is still in really early stage it is not published on package registries, but you can install it directly via the following commands 

Python
```
pip install git+https://github.com/dataforgoodfr/Coordonnees.git/#subdirectory=python
```

Javascript
```
npm install https://github.com/dataforgoodfr/Coordonnees.git?subdir=js
```

# Quick demo

TODO: write demo commands with the new repo structure

In order to show the results of this script, you can use the Dbeaver tool and check the tables whose name start with inventaire_id_xx :
https://dbeaver.io/download/#requirements
