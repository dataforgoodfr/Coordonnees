from dynamic_models.models import ModelSchema, models

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

DJANGO_TYPES = {
    "integer": "django.db.models.IntegerField",
    "decimal": "django.db.models.DecimalField",
    "range": "django.db.models.RangeField",
    "text": "django.db.models.TextField",
    "select one": "django.db.models.CharField",
    "select multiple": "django.db.models.CharField",
    "select one from file": "django.db.models.CharField",
    "select multiple from file": "django.db.models.CharField",  # space separated values, we should try
    "select all that apply": "django.db.models.CharField",  # to find a better way to store them
    "rank": "django.db.models.CharField",
    "geopoint": "django.contrib.gis.db.models.PointField",
    "start-geopoint": "django.contrib.gis.db.models.PointField",
    "geotrace": "django.contrib.gis.db.models.LineStringField",
    "geoshape": "django.contrib.gis.db.models.PolygonField",
    "date": "django.db.models.DateField",
    "time": "django.db.models.TimeFied",
    "dateTime": "django.db.models.DateTimeField",
    "photo": "django.db.models.ImageField",
    "audio": "django.db.models.FileField",
    "background-audio": "django.db.models.FileField",
    "video": "django.db.models.FileField",
    "file": "django.db.models.FileField",
    "barcode": None,
    "hidden": None,
    "xml-external": None,
}

FIELD_KWARGS = {
    "django.contrib.gis.db.models.PointField": {"dim": 3},
    "django.db.models.DecimalField": {
        "max_digits": 10,  # this is arbitrary, to review
        "decimal_places": 2,
    },
}


def import_form(form, name=None, parent=None):
    if not name:
        name = form["id_string"]
    schema = ModelSchema.objects.create(name=name)
    import_questions(form["children"], schema)
    if parent:
        schema.fields.create(
            name="parent",  # maybe should be _parent, to review
            class_name="django.db.models.ForeignKey",
            kwargs={"on_delete": models.CASCADE, "to": parent.name},
        )


def import_questions(questions, schema):
    for question in questions:
        qtype = question["type"]
        if qtype in METADATA_TYPES + IGNORE_TYPES:
            print("Skipping :", qtype)
            continue
        if qtype == "group":
            import_questions(question["children"], schema)
            continue
        if qtype == "repeat":
            import_form(
                question, name=f"{schema.name}_{question["name"]}", parent=schema
            )
            continue
        kwargs = {}
        kwargs["null"] = True
        if "bind" in question:
            bind = question["bind"]
            if "required" in bind:
                kwargs["null"] = bind["required"] != "yes"
        if "choices" in question:
            kwargs["choices"] = [
                (choice["name"], choice["label"]) for choice in question["choices"]
            ]
        field_class = DJANGO_TYPES[qtype]
        schema.fields.create(
            name=question["name"],
            class_name=field_class,
            kwargs=kwargs | FIELD_KWARGS.get(field_class, {}),
        )
