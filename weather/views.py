from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .client import WeatherClient
from .throttles import TokenBucketThrottle
from .tasks import predict_weather

class ForecastAPIView(APIView):
    throttle_classes = [TokenBucketThrottle]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='city', description='City name for weather forecast', required=True, type=str),
        ],
        responses={202: dict}
    )
    def get(self, request):
        city = request.query_params.get('city')
        if not city:
            return Response({"error": "city parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Enqueue the ML task
        task = predict_weather.delay(city)
        return Response(
            {"message": "Forecast job submitted", "job_id": task.id},
            status=status.HTTP_202_ACCEPTED
        )

class JobStatusAPIView(APIView):
    @extend_schema(
        responses={200: dict}
    )
    def get(self, request, job_id):
        result = AsyncResult(job_id)
        response_data = {
            'job_id': job_id,
            'status': result.status,
            'result': result.result if result.ready() else None
        }
        return Response(response_data, status=status.HTTP_200_OK)
