import statistics
from django.contrib import admin


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cooking_time_range"

    def lookups(self, request, model_admin):
        qs = model_admin.model.objects.values_list("cooking_time", flat=True)
        times = list(qs)
        if len(times) < 3:
            return []

        Q1 = statistics.median_low(times[:len(times) // 2])
        median = statistics.median(times)

        return [
            (f"fast_{Q1}", f"быстрее {int(Q1)} мин"),
            (f"medium_{Q1}_{median}", f"{int(Q1)}–{int(median)} мин"),
            (f"long_{median}", f"дольше {int(median)} мин"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            parts = value.split("_")
            if parts[0] == "fast":
                return queryset.filter(cooking_time__lt=int(parts[1]))
            elif parts[0] == "medium":
                return queryset.filter(cooking_time__range=(
                    int(parts[1]), int(parts[2])))
            elif parts[0] == "long":
                return queryset.filter(cooking_time__gt=int(parts[1]))
        return queryset
