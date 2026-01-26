from collections import defaultdict

import numpy as np
import pandas as pd
import peewee
from playhouse.db_url import connect
from playhouse.shortcuts import SqliteDatabase
from pyxform.xls2json import parse_file_to_json

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


class KoboToolboxImporter:
    def __init__(self, xlsform_path):
        form = parse_file_to_json(xlsform_path)
        self._parse_form(form)

    def create_tables(self, db_url):
        db = connect(db_url)
        db.load_extension("mod_spatialite")

        class BaseModel(peewee.Model):
            class Meta:
                database = db

        self.tables = []
        for model, fields in self.models.items():
            if "parent" in fields:
                parent_table_name = fields["parent"][1]["model"]
                fields["parent"][1]["model"] = next(
                    table
                    for table in self.tables
                    if table._meta.table_name == parent_table_name
                )
            self.tables.append(
                type(
                    model,
                    (BaseModel,),
                    {name: field[0](**field[1]) for name, field in fields.items()},
                )
            )
        db.drop_tables(self.tables)
        db.create_tables(self.tables)

    def import_data(self, db_url, xlsx_path):
        db = connect(db_url)
        db.load_extension("mod_spatialite")
        sheets_dict = pd.read_excel(xlsx_path, sheet_name=None)
        main_table_name = self.tables[0]._meta.table_name
        for i, (sheet_name, sheet) in enumerate(sheets_dict.items()):
            table_name = (
                main_table_name if i == 0 else f"{main_table_name}_{sheet_name}"
            )
            model = next(
                table
                for table in self.tables
                if table._meta.table_name == table_name.lower()
            )
            sheet = sheet.rename(columns={"_index": "id", "_parent_index": "parent"})
            fields = []
            for name, field in model._meta.fields.items():
                if name in sheet.columns:
                    if isinstance(field, PointField):
                        sheet[name] = (
                            sheet[name]
                            .fillna("")
                            .apply(
                                lambda coords: (
                                    [float(c) for c in coords.split(" ")[:3]]
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
            # sheet = sheet.rename(columns={"parent": "parent_id"})
            sheet = sheet.replace({np.nan: None})
            records = [
                record | {"id": id} for id, record in sheet.to_dict("index").items()
            ]
            model.insert_many(records).execute()

    def _parse_form(self, form, model=None, parent=None):
        if not model:
            model = form["id_string"].lower()
            self.models = defaultdict(dict)
            self.choices = []
        self._parse_questions(form["children"], model)
        if parent:
            self.models[model]["parent"] = (
                peewee.ForeignKeyField,
                dict(model=parent, on_delete="CASCADE", backref=form["name"]),
            )

    def _parse_questions(self, questions, model):
        for question in questions:
            qtype = question["type"]
            if qtype in METADATA_TYPES + IGNORE_TYPES:
                print("Skipping :", qtype)
                continue
            if qtype == "group":
                self._parse_questions(question["children"], model)
                continue
            if qtype == "repeat":
                self._parse_form(
                    question,
                    model=f"{model}_{question['name']}",
                    parent=model,
                )
                continue
            kwargs = {}
            kwargs["null"] = True
            if "bind" in question:
                bind = question["bind"]
                if "required" in bind:
                    kwargs["null"] = bind["required"] != "yes"
            if "choices" in question:
                self.choices.extend(
                    [
                        (question["name"], choice["name"], choice["label"])
                        for choice in question["choices"]
                    ]
                )
            if qtype in PEEWEE_TYPES:
                self.models[model][question["name"]] = (PEEWEE_TYPES[qtype], kwargs)


if __name__ == "__main__":
    path = "../data/20250213_Inventaire_ID_QuestionnaireK.xlsx"
    importer = KoboToolboxImporter(path)
    importer.create_tables("sqlite:///coordo.sqlite")
    importer.import_data(
        "sqlite:///coordo.sqlite", "../data/20251017_Inventaire_ID_Donnees.xlsx"
    )
