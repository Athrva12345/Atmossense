import os
import json
import datetime
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def generate_synthetic_data(num_samples=5000):
    np.random.seed(42)
    
    # Generate dates over a couple of years
    start_date = pd.to_datetime('2024-01-01')
    dates = [start_date + pd.Timedelta(hours=i) for i in range(num_samples)]
    
    df = pd.DataFrame({'timestamp': dates})
    df['hour'] = df['timestamp'].dt.hour
    df['month'] = df['timestamp'].dt.month
    
    # Seasonality effect
    season_effect = np.sin((df['month'] - 1) * (2 * np.pi / 12)) * 15
    diurnal_effect = np.sin((df['hour'] - 6) * (2 * np.pi / 24)) * 5
    
    # Base temp based on season and diurnal
    df['temp'] = 15 + season_effect + diurnal_effect + np.random.normal(0, 3, num_samples)
    
    df['humidity'] = np.clip(np.random.normal(60, 15, num_samples), 10, 100)
    df['pressure'] = np.random.normal(1013, 10, num_samples)
    
    # Target: temp + 1 hour (which correlates to the next row)
    df['future_temp'] = df['temp'].shift(-1)
    df = df.dropna()
    
    return df

def train_and_save_model():
    print("Generating synthetic time-series weather data...")
    df = generate_synthetic_data(5000)
    
    features = ['temp', 'humidity', 'pressure', 'hour', 'month']
    X = df[features]
    y = df['future_temp']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForestRegressor model...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model trained. RMSE: {rmse:.2f}, MAE: {mae:.2f}, R2: {r2:.2f}")
    
    # Save the model
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'model_v1.joblib')
    joblib.dump(model, model_path)
    
    # Save metadata
    metadata = {
        "training_date": datetime.datetime.now().isoformat(),
        "model_version": "v1.0",
        "algorithm": "RandomForestRegressor",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42
        },
        "features": features,
        "metrics": {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4)
        }
    }
    
    metadata_path = os.path.join(model_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Model saved to {model_path}")
    print(f"Metadata saved to {metadata_path}")

if __name__ == "__main__":
    train_and_save_model()
