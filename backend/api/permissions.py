from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Проверяет, является ли пользователь автором рецепта."""
    def has_object_permission(self, request, view, obj):
        # Разрешаем только чтение для всех
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Разрешаем изменение или удаление только автору рецепта
        return obj.author == request.user
