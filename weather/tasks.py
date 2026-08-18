import os
import pandas as pd
import joblib
from celery import shared_task
from django.conf import settings
from .client import WeatherClient

# Singleton model loader
_ml_model = None

def get_ml_model():
    global _ml_model
    if _ml_model is None:
        model_path = os.path.join(settings.BASE_DIR, 'ml', 'models', 'weather_model_v1.joblib')
        _ml_model = joblib.load(model_path)
    return _ml_model

@shared_task(bind=True)
def predict_weather(self, city):
    """
    ML pipeline: fetches real data, creates a dataframe,
    and runs the trained Random Forest model.
    """
    client = WeatherClient()
    try:
        data = client.get_weather(city)
    except Exception as e:
        return {"error": str(e)}

    # Extract ML features
    df = pd.DataFrame([{
        'temp': data.get('main', {}).get('temp', 20),
        'humidity': data.get('main', {}).get('humidity', 50),
        'pressure': data.get('main', {}).get('pressure', 1000)
    }])
    
    model = get_ml_model()
    predicted_temp = model.predict(df)[0]
    
    current_temp = float(df.iloc[0]['temp'])
    predicted_temp_float = float(predicted_temp)
    diff = predicted_temp_float - current_temp
    
    forecast_5_hours = [
        round(current_temp + diff * 0.2, 2),
        round(current_temp + diff * 0.4, 2),
        round(current_temp + diff * 0.6, 2),
        round(current_temp + diff * 0.8, 2),
        round(predicted_temp_float, 2)
    ]
    
    result = {
        "city": city,
        "current_temp": current_temp,
        "predicted_temp_in_5_hours": round(predicted_temp_float, 2),
        "forecast_5_hours": forecast_5_hours,
        "ml_features_used": list(df.columns),
        "model_version": "v1.0"
    }
    
    # Cache the ML forecast for 1 hour (3600 seconds)
    from django.core.cache import cache
    cache_key = f"atmossense:ml_forecast:{city.lower()}"
    cache.set(cache_key, result, timeout=3600)
    
    return result
