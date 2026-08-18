import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.urls import reverse
from .client import WeatherClient
from .tasks import predict_weather
from celery.result import AsyncResult

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture(autouse=True)
def override_cache(settings):
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

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
    @patch('weather.throttles.redis_client.register_script')
    @patch('weather.tasks.predict_weather.delay')
    def test_forecast_api_enqueue(self, mock_delay, mock_redis_script, api_client):
        # Mock Redis Lua script to always allow request
        mock_script_exec = MagicMock(return_value=1)
        mock_redis_script.return_value = mock_script_exec
        
        mock_task = MagicMock()
        mock_task.id = "fake-job-id"
        mock_delay.return_value = mock_task
        
        url = reverse('forecast')
        response = api_client.get(url, {'city': 'NYC'})
        
        assert response.status_code == 202
        assert response.json()['job_id'] == "fake-job-id"
        mock_delay.assert_called_once_with('NYC')

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

class TestJobStatusAPIView:
    @patch('weather.views.AsyncResult')
    def test_job_status(self, mock_async_result, api_client):
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.result = {'predicted_temp_in_5_hours': 25.0}
        mock_async_result.return_value = mock_result
        
        url = reverse('job-status', args=['fake-job-id'])
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response.json()['status'] == 'SUCCESS'
        assert response.json()['result']['predicted_temp_in_5_hours'] == 25.0

class TestCeleryTasks:
    @patch('weather.tasks.WeatherClient.get_weather')
    def test_predict_weather_task(self, mock_get_weather):
        mock_get_weather.return_value = {
            "main": {"temp": 22.0, "humidity": 45, "pressure": 1012}
        }
        
        result = predict_weather('NYC')
        
        assert result['city'] == 'NYC'
        assert result['current_temp'] == 22.0
        assert 'predicted_temp_in_5_hours' in result
        assert isinstance(result['predicted_temp_in_5_hours'], float)
        assert result['model_version'] == 'v1.0'

from django.core.cache import cache

class TestCaching:
    def setup_method(self):
        cache.clear()

    @patch('weather.client.requests.get')
    def test_client_caching(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"temp": 25.0}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = WeatherClient()
        
        # Cache Miss
        result1 = client.get_weather('London')
        assert result1 == {"temp": 25.0}
        assert mock_get.call_count == 1
        
        # Cache Hit
        result2 = client.get_weather('London')
        assert result2 == {"temp": 25.0}
        assert mock_get.call_count == 1  # Should not have been called again

    @patch('weather.throttles.redis_client.register_script')
    def test_forecast_api_edge_cache_hit(self, mock_redis_script, api_client):
        # Mock Redis Lua script to always allow request
        mock_script_exec = MagicMock(return_value=1)
        mock_redis_script.return_value = mock_script_exec
        
        cache_key = "atmossense:ml_forecast:nyc"
        cache.set(cache_key, {"predicted_temp": 22.0}, timeout=3600)
        
        url = reverse('forecast')
        response = api_client.get(url, {'city': 'NYC'})
        
        assert response.status_code == 200
        assert response.json()['message'] == "Forecast retrieved from cache"
        assert response['Cache-Control'] == 'public, max-age=3600'
        
    @patch('weather.views.AsyncResult')
    def test_job_status_edge_cache_headers(self, mock_async_result, api_client):
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.result = {'predicted_temp_in_5_hours': 25.0}
        mock_async_result.return_value = mock_result
        
        url = reverse('job-status', args=['fake-job-id'])
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response['Cache-Control'] == 'public, max-age=3600'

class TestHealthEndpoints:
    def test_liveness_probe(self, api_client):
        url = reverse('health')
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'

    @patch('weather.health.connections')
    @patch('weather.health.cache.set')
    def test_readiness_probe_success(self, mock_cache_set, mock_connections, api_client):
        mock_cursor = MagicMock()
        mock_connections.__getitem__.return_value.cursor.return_value = mock_cursor
        mock_cache_set.return_value = True
        
        url = reverse('ready')
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response.json()['status'] == 'ready'

    @patch('weather.health.connections')
    def test_readiness_probe_db_failure(self, mock_connections, api_client):
        mock_connections.__getitem__.return_value.cursor.side_effect = Exception("DB Down")
        
        url = reverse('ready')
        response = api_client.get(url)
        
        assert response.status_code == 503
        assert response.json()['status'] == 'error'
        assert response.json()['services']['db'] == 'error'
