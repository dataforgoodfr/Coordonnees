#  Context


#  Dependencies

You will need the following dependencies in order to use SpatialLite : 

```
sudo apt-get install gdal-bin libgdal-dev libsqlite3-mod-spatialite
```

# Importing 

This package is divided in a Python and a Javascript module, since it is still in really early stage, you can install it directly via the following commands 

Python
```
pip install "coordo @ git+https://github.com/dataforgoodfr/Coordonnees.git/#subdirectory=python"
```

Javascript
```
npm install https://github.com/dataforgoodfr/Coordonnees.git?subdir=js
```


# Quick demo

For a quick demo, just do the following actions 

```
uv run manage.py import_xlsform 20250213_Inventaire_ID_QuestionnaireK.xlsx
uv run manage.py import_data inventaire_ID 20251017_Inventaire_ID_Donnees.xlsx
```

In order to show the results of this script, you can use the Dbeaver tool and check the tables whose name start with dynamic_models_inventaire_id_xx :
https://dbeaver.io/download/#requirements

To run the map viewer
```
uv run manage.py runserver
```
