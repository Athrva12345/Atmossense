import requests
from django.conf import settings

class WeatherClient:
    def __init__(self):
        self.base_url = settings.WEATHER_API_URL
        self.api_key = settings.WEATHER_API_KEY

    def get_weather(self, city):
        """Fetch current weather data from external API."""
        url = f"{self.base_url.rstrip('/')}/weather"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
