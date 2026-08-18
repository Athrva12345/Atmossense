import requests
from django.conf import settings
from django.core.cache import cache

class WeatherClient:
    def __init__(self):
        self.base_url = settings.WEATHER_API_URL
        self.api_key = settings.WEATHER_API_KEY

    def get_weather(self, city):
        """Fetch current weather data from external API, with caching."""
        cache_key = f"atmossense:external_weather:{city.lower()}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        url = f"{self.base_url.rstrip('/')}/weather"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Cache for 15 minutes (900 seconds)
        cache.set(cache_key, data, timeout=900)
        
        return data
