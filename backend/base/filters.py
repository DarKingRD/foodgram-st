import numpy as np
from django.contrib import admin


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cooking_time_range"

    def lookups(self, request, model_admin):
        # Получаем уникальные значения времени готовки
        qs = model_admin.model.objects.values_list("cooking_time", flat=True)
        times = [time for time in set(qs) if isinstance(time, (int, float))]  # фильтруем на числовые значения

        if len(times) < 3:
            return []

        # Создаём гистограмму с 3 бинами
        bins = np.histogram(times, bins=3)[1]

        # Определяем пороги на основе этих бинов
        fast_time = bins[1]
        slow_time = bins[2]

        return [
            ((0, fast_time), f'быстрее {int(fast_time)} мин'),
            ((fast_time, slow_time), f'{int(fast_time)}–{int(slow_time)} мин'),
            ((slow_time, 10**10), f'дольше {int(slow_time)} мин'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            # Преобразуем строку из value() в кортеж через eval()
            range_tuple = eval(value)
            # Используем range для фильтрации по диапазону
            if len(range_tuple) == 2:
                return queryset.filter(cooking_time__range=range_tuple)

            elif len(range_tuple) == 1:
                if "fast" in value:
                    return queryset.filter(cooking_time__lt=range_tuple[0])
                elif "long" in value:
                    return queryset.filter(cooking_time__gt=range_tuple[0])

        return queryset
