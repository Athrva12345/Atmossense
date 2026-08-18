from django.urls import path
from .views import ForecastAPIView

urlpatterns = [
    path('forecast/', ForecastAPIView.as_view(), name='forecast'),
]
