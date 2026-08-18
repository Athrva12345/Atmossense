import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.urls import reverse
from .client import WeatherClient

@pytest.fixture
def api_client():
    return APIClient()

class TestWeatherClient:
    @patch('weather.client.requests.get')
    def test_get_weather_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"temp": 25.0, "weather": "Sunny"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = WeatherClient()
        result = client.get_weather('London')
        
        assert result == {"temp": 25.0, "weather": "Sunny"}
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs['params']['q'] == 'London'
        assert kwargs['params']['units'] == 'metric'

class TestForecastAPIView:
    @patch('weather.views.WeatherClient.get_weather')
    @patch('weather.throttles.redis_client.register_script')
    def test_forecast_api_success(self, mock_redis_script, mock_get_weather, api_client):
        # Mock Redis Lua script to always allow request
        mock_script_exec = MagicMock(return_value=1)
        mock_redis_script.return_value = mock_script_exec
        
        mock_get_weather.return_value = {"temp": 22.0}
        
        url = reverse('forecast')
        response = api_client.get(url, {'city': 'NYC'})
        
        assert response.status_code == 200
        assert response.json()['data']['temp'] == 22.0

    @patch('weather.throttles.redis_client.register_script')
    def test_forecast_api_missing_city(self, mock_redis_script, api_client):
        # Mock Redis Lua script to always allow request
        mock_script_exec = MagicMock(return_value=1)
        mock_redis_script.return_value = mock_script_exec
        
        url = reverse('forecast')
        response = api_client.get(url)
        
        assert response.status_code == 400
        assert 'city parameter is required' in response.json()['error']

    @patch('weather.throttles.redis_client.register_script')
    def test_forecast_api_rate_limited(self, mock_redis_script, api_client):
        # Mock Redis Lua script to deny request (simulate rate limit exceeded)
        mock_script_exec = MagicMock(return_value=0)
        mock_redis_script.return_value = mock_script_exec
        
        url = reverse('forecast')
        response = api_client.get(url, {'city': 'NYC'})
        
        assert response.status_code == 429
