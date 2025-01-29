from django.urls import path
from .views import short_link


urlpatterns = [
    path(
        's/<int:pk>', short_link, name='short_link'),
]
