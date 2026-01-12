from django.core.management.base import BaseCommand
from dynamic_models.models import FieldSchema, ModelSchema
from pyxform.xls2json import parse_file_to_json

from form.utils import import_form


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("xlsform_path")

    def handle(self, *args, **options):
        for field in FieldSchema.objects.all():
            field.delete()
        for schema in ModelSchema.objects.all():
            schema.delete()
        form = parse_file_to_json(options["xlsform_path"])
        import_form(form)
