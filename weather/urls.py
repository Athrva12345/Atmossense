from django.urls import path
from .views import ForecastAPIView, JobStatusAPIView

urlpatterns = [
    path('forecast/', ForecastAPIView.as_view(), name='forecast'),
    path('jobs/<str:job_id>/', JobStatusAPIView.as_view(), name='job-status'),
]
