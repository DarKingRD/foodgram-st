from django.urls import path
from base.views import redirect_short_link

urlpatterns = [
    path('<str:short_code>/', redirect_short_link, name='redirect_short_link'),
]