import numpy as np
from django.contrib import admin


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cooking_time_range"

    def lookups(self, request, model_admin):
        # Получаем уникальные значения времени готовки
        qs = model_admin.model.objects.values_list("cooking_time", flat=True)
        times = [time for time in set(qs)]

        if len(times) < 3:
            return []

        # Создаём гистограмму с 3 бинами
        counts, bins = np.histogram(times, bins=3)

        # Определяем пороги на основе этих бинов
        fast_time, slow_time = int(bins[1]), int(bins[2])
        #  без int выдаёт не целые числа, что неудобно

        return [
            ((0, fast_time), f'быстрее {fast_time} мин ({counts[0]})'),
            ((fast_time, slow_time), f'{fast_time}–{slow_time} мин ({counts[1]})'),
            ((slow_time, 10**10), f'дольше {slow_time} мин ({counts[0]})'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            # Преобразуем строку из value() в кортеж через eval()
            range_tuple = eval(value)
            # Используем range для фильтрации по диапазону
            return queryset.filter(cooking_time__range=range_tuple)

        return queryset
