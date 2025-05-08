import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из ../data/ingredients.json'

    def handle(self, *args, **kwargs):
        file_path = Path(settings.BASE_DIR) / 'data' / 'ingredients.json'

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        created = 0
        for item in data:
            obj, is_created = Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
            if is_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Загружено {created} новых ингредиентов'
        ))
