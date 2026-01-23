from collections import defaultdict

import numpy as np
import pandas as pd
import peewee
from geojson import Point
from playhouse.sqlite_ext import SqliteExtDatabase
from pyxform.xls2json import parse_file_to_json

db = SqliteExtDatabase("peewee.sqlite")
db.connect()
db.load_extension("mod_spatialite")

METADATA_TYPES = [
    "start",
    "end",
    "today",
    "deviceid",
    "subscriberid",
    "simserial",
    "phonenumber",
    "username",
    "email",
    "audit",
    "calculate",
    "note",
]

IGNORE_TYPES = [
    "note",
    "calculate",
]

# DJANGO_TYPES = {
#     "integer": "django.db.models.IntegerField",
#     "decimal": "django.db.models.DecimalField",
#     "range": "django.db.models.RangeField",
#     "text": "django.db.models.TextField",
#     "select one": "django.db.models.CharField",
#     "select multiple": "django.db.models.CharField",
#     "select one from file": "django.db.models.CharField",
#     "select multiple from file": "django.db.models.CharField",  # space separated values, we should try
#     "select all that apply": "django.db.models.CharField",  # to find a better way to store them
#     "rank": "django.db.models.CharField",
#     "geopoint": "django.contrib.gis.db.models.PointField",
#     "start-geopoint": "django.contrib.gis.db.models.PointField",
#     "geotrace": "django.contrib.gis.db.models.LineStringField",
#     "geoshape": "django.contrib.gis.db.models.PolygonField",
#     "date": "django.db.models.DateField",
#     "time": "django.db.models.TimeFied",
#     "dateTime": "django.db.models.DateTimeField",
#     "photo": "django.db.models.ImageField",
#     "audio": "django.db.models.FileField",
#     "background-audio": "django.db.models.FileField",
#     "video": "django.db.models.FileField",
#     "file": "django.db.models.FileField",
#     "barcode": None,
#     "hidden": None,
#     "xml-external": None,
# }


class PointField(peewee.Field):
    field_type = "POINT"

    def db_value(self, value):
        if value is not None:
            return f"POINT({value[0]} {value[1]})"
        return None

    def python_value(self, value):
        if value is not None:
            point_str = value.split("(")[1].split(")")[0]
            x, y = map(float, point_str.split())
            return (x, y)
        return None


PEEWEE_TYPES = {
    "integer": peewee.IntegerField,
    "decimal": peewee.DecimalField,
    "range": peewee.IntegerField,
    "text": peewee.TextField,
    "select one": peewee.CharField,
    "select multiple": peewee.CharField,
    "select one from file": peewee.CharField,
    "select multiple from file": peewee.CharField,
    "select all that apply": peewee.CharField,
    "rank": peewee.CharField,
    "geopoint": PointField,
    "start-geopoint": PointField,
    # "geotrace": peewee.LineStringField,
    # "geoshape": peewee.PolygonField,
    "date": peewee.DateField,
    "time": peewee.TimeField,
    "dateTime": peewee.DateTimeField,
    # "photo": peewee.ImageField,
    # "audio": peewee.FileField,
    # "background-audio": peewee.FileField,
    # "video": peewee.FileField,
    # "file": peewee.FileField,
    "barcode": None,
    "hidden": None,
    "xml-external": None,
}


class BaseModel(peewee.Model):
    class Meta:
        database = db


class KoboTooloboxImporter:
    def import_xlsform(self, xlsform_path):
        form = parse_file_to_json(xlsform_path)
        self.models = defaultdict(dict)
        self._import_form(form)
        db.create_tables(
            [type(model, (BaseModel,), fields) for model, fields in self.models.items()]
        )

    def import_form_data(xlsform_path, xlsx_path):
        sheets_dict = pd.read_excel(xlsx_path, sheet_name=None)
        for i, (sheet_name, sheet) in enumerate(sheets_dict.items()):
            model_name = schema_name if i == 0 else f"{schema_name}_{sheet_name}"
            # schema = ModelSchema.objects.get(name=model_name)
            # model = schema.as_model()
            # model.objects.all().delete()
            sheet = sheet.rename(columns={"_parent_index": "parent"})
            sheet = sheet.set_index("_index")
            fields = []
            for field in schema.fields.all():
                if field.name in sheet.columns:
                    if field.class_name.split(".")[-1] == "PointField":
                        sheet[field.name] = (
                            sheet[field.name]
                            .fillna("")
                            .apply(
                                lambda coords: (
                                    Point([float(c) for c in coords.split(" ")[:3]])
                                    if coords
                                    else None
                                )
                            )
                        )

                    fields.append(field.name)
                else:
                    print(f"Field {field.name} not found in data")
            sheet = sheet[fields]
            # sheet.columns = [slugify(col).replace("-", "_") for col in sheet.columns]
            sheet = sheet.rename(columns={"parent": "parent_id"})
            sheet = sheet.replace({np.nan: None})
            records = [
                record | {"id": id} for id, record in sheet.to_dict("index").items()
            ]
            # model.objects.bulk_create(model(**record) for record in records)

    def _import_form(self, form, model=None, parent=None):
        if not model:
            model = form["id_string"]
        self._import_questions(form["children"], model)
        if parent:
            self.models[model]["parent"] = peewee.DeferredForeignKey(
                model,
                on_delete="CASCADE",
            )

    def _import_questions(self, questions, model):
        for question in questions:
            qtype = question["type"]
            if qtype in METADATA_TYPES + IGNORE_TYPES:
                print("Skipping :", qtype)
                continue
            if qtype == "group":
                self._import_questions(question["children"], model)
                continue
            if qtype == "repeat":
                self._import_form(
                    question,
                    model=f"{model}_{question["name"]}",
                    parent=model,
                )
                continue
            kwargs = {}
            kwargs["null"] = True
            if "bind" in question:
                bind = question["bind"]
                if "required" in bind:
                    kwargs["null"] = bind["required"] != "yes"
            # if "choices" in question:
            #     kwargs["choices"] = [
            #         (choice["name"], choice["label"]) for choice in question["choices"]
            #     ]
            if qtype in PEEWEE_TYPES:
                self.models[model][question["name"]] = PEEWEE_TYPES[qtype](**kwargs)
