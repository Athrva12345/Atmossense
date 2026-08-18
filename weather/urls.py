from django.urls import path
from .views import ForecastAPIView, JobStatusAPIView
from .health import health_check, readiness_check

urlpatterns = [
    path('forecast/', ForecastAPIView.as_view(), name='forecast'),
    path('jobs/<str:job_id>/', JobStatusAPIView.as_view(), name='job-status'),
    path('health/', health_check, name='health'),
    path('ready/', readiness_check, name='ready'),
]
