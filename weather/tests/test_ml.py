import os
import pytest
import pandas as pd
import joblib
from django.conf import settings

@pytest.fixture
def loaded_model():
    model_path = os.path.join(settings.BASE_DIR, 'ml', 'models', 'model_v1.joblib')
    # If the model does not exist yet (e.g., in CI before training), we can skip the test
    if not os.path.exists(model_path):
        pytest.skip("model_v1.joblib not found. Run ml/train.py first.")
    model = joblib.load(model_path)
    return model

def test_model_predictions_within_sane_range(loaded_model):
    """
    Assert that the RandomForestRegressor outputs values within a sane 
    meteorological range (-50C to +60C) to catch catastrophic retrains.
    """
    # Create dummy inputs covering extreme but realistic bounds
    test_cases = pd.DataFrame([
        {'temp': 20, 'humidity': 50, 'pressure': 1013, 'hour': 12, 'month': 6}, # Normal day
        {'temp': -30, 'humidity': 20, 'pressure': 1030, 'hour': 4, 'month': 1}, # Extreme cold
        {'temp': 45, 'humidity': 10, 'pressure': 1000, 'hour': 14, 'month': 8}, # Extreme heat
        {'temp': 30, 'humidity': 100, 'pressure': 980, 'hour': 16, 'month': 7}, # Tropical storm
    ])
    
    predictions = loaded_model.predict(test_cases)
    
    assert len(predictions) == 4
    for pred in predictions:
        assert isinstance(pred, float)
        assert -50 <= pred <= 60, f"Prediction {pred} is outside the sane range of -50C to 60C!"
