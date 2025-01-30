import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from base.models import Ingredient
import traceback


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV-файла'

    def handle(self, *args, **kwargs):
        file_name = 'ingredients.csv'  # Имя CSV файла
        try:
            # Формируем путь к файлу
            file_path = os.path.join(settings.BASE_DIR, 'data', file_name)

            # Проверяем, существует ли файл
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(
                    f'Файл "{file_name}" не найден по пути: {file_path}'))
                return

            # Открываем файл и загружаем данные
            with open(file_path, newline='', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)

                # Проверяем заголовки CSV
                headers = csv_reader.fieldnames
                self.stdout.write(self.style.SUCCESS(
                    f"Заголовки в файле: {headers}"))

                if 'name' not in headers or 'measurement_unit' not in headers:
                    self.stdout.write(
                        self.style.ERROR(
                            'Ошибка: Файл CSV не содержит требуемых столбцов'))
                    return

                ingredients_to_create = [
                    Ingredient(
                        name=row['name'].strip(),
                        measurement_unit=row['measurement_unit'].strip()
                    )
                    for row in csv_reader
                ]

            # Массовое создание новых ингредиентов
            created_ingredients = Ingredient.objects.bulk_create(
                ingredients_to_create,
                ignore_conflicts=True  # Игнорировать конфликты
            )

            # Выводим успешный результат
            self.stdout.write(self.style.SUCCESS(
                f'Данные успешно загружены!'
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
