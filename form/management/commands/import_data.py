import os

import numpy as np
import pandas as pd
from django.contrib.gis.db.models.fields import Point
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from dynamic_models.models import ModelSchema
from sqlalchemy import create_engine

os.environ["SPATIALITE_LIBRARY_PATH"] = "/usr/lib/mod_spatialite.so"
engine = create_engine("sqlite:///db.sqlite3", echo=True, plugins=["geoalchemy2"])


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("form_name")
        parser.add_argument("xlsx_path")

    def handle(self, *args, **options):
        sheets_dict = pd.read_excel(options["xlsx_path"], sheet_name=None)
        form_name = options["form_name"]
        for i, (sheet_name, sheet) in enumerate(sheets_dict.items()):
            print(form_name)
            model_name = form_name if i == 0 else f"{form_name}_{sheet_name}"
            schema = ModelSchema.objects.get(name=model_name)
            model = schema.as_model()
            model.objects.all().delete()
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
            sheet.columns = [slugify(col).replace("-", "_") for col in sheet.columns]
            sheet = sheet.rename(columns={"parent": "parent_id"})
            sheet = sheet.replace({np.nan: None})
            records = [
                record | {"id": id} for id, record in sheet.to_dict("index").items()
            ]
            model.objects.bulk_create(model(**record) for record in records)
