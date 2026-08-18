import time
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from celery import shared_task
from .client import WeatherClient

@shared_task(bind=True)
def predict_weather(self, city):
    """
    Dummy ML pipeline: fetches real data, creates a dataframe,
    and runs a simple Random Forest simulation using scikit-learn.
    """
    client = WeatherClient()
    try:
        data = client.get_weather(city)
    except Exception as e:
        return {"error": str(e)}

    # Simulate ML feature extraction with pandas
    df = pd.DataFrame([{
        'temp': data.get('main', {}).get('temp', 20),
        'humidity': data.get('main', {}).get('humidity', 50),
        'pressure': data.get('main', {}).get('pressure', 1000)
    }])
    
    # Simulate an ML inference load (CPU bound)
    time.sleep(2)
    
    # Dummy Scikit-learn model logic
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    # Fit on dummy historical data just for structural compliance
    dummy_x = pd.DataFrame({'temp': [15, 20, 25], 'humidity': [40, 50, 60], 'pressure': [1010, 1000, 990]})
    dummy_y = [16, 21, 24]  # Predicted future temperatures
    model.fit(dummy_x, dummy_y)
    
    predicted_temp = model.predict(df)[0]
    
    result = {
        "city": city,
        "current_temp": df.iloc[0]['temp'],
        "predicted_temp_in_5_hours": round(predicted_temp, 2),
        "ml_features_used": list(df.columns)
    }
    
    # Cache the ML forecast for 1 hour (3600 seconds)
    from django.core.cache import cache
    cache_key = f"atmossense:ml_forecast:{city.lower()}"
    cache.set(cache_key, result, timeout=3600)
    
    return result
