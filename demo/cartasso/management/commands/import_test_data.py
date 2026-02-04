from coordo.sources.kobotoolbox import KoboToolboxSource
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        source = KoboToolboxSource(
            "data/20250213_Inventaire_ID_QuestionnaireK.xlsx", "sqlite:///coordo.sqlite"
        )
        source.create_tables()
        source.import_data("data/20251017_Inventaire_ID_Donnees.xlsx")
