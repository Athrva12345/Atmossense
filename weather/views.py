from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .client import WeatherClient
from .throttles import TokenBucketThrottle

class ForecastAPIView(APIView):
    throttle_classes = [TokenBucketThrottle]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='city', description='City name for weather forecast', required=True, type=str),
        ],
        responses={200: dict}
    )
    def get(self, request):
        city = request.query_params.get('city')
        if not city:
            return Response({"error": "city parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        client = WeatherClient()
        try:
            weather_data = client.get_weather(city)
            # In Phase 3, we will enqueue an ML celery task here instead of returning the raw external API data.
            # For now, just forward the fetched data to verify the Gateway layer works.
            return Response({"message": "Weather fetched successfully", "data": weather_data})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
