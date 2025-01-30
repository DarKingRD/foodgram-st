import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from base.models import Ingredient
import traceback


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON-фикстуры'

    def handle(self, *args, **kwargs):
        file_name = 'ingredients.json'  # Имя JSON файла
        try:
            # Формируем путь к файлу
            file_path = os.path.join(settings.BASE_DIR, 'data', file_name)

            # Открываем файл и загружаем данные
            with open(file_path, 'r', encoding='utf-8') as file:

                # Массовое создание новых ингредиентов
                created_ingredients = Ingredient.objects.bulk_create(
                    [
                        Ingredient(**ingredient)
                        for ingredient in json.load(file)
                    ],
                    ignore_conflicts=True  # Игнорировать конфликты
                )

            # Выводим успешный результат
            self.stdout.write(self.style.SUCCESS(
                f'Данные успешно загружены! '
                f'Добавлено записей: {len(created_ingredients)}'
            ))

        except Exception as e:
            # Выводим полную трассировку ошибки
            self.stdout.write(self.style.ERROR(
                f'Произошла ошибка при обработке файла "{file_name}": {str(e)}'
            ))
            # Дополнительная информация для диагностики
            self.stdout.write(self.style.ERROR(
                f'Полная трассировка ошибки:\n{traceback.format_exc()}'))
