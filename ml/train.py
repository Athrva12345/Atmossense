import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def generate_synthetic_data(num_samples=1000):
    np.random.seed(42)
    # Generate realistic features
    temp = np.random.normal(loc=20, scale=10, size=num_samples) # degrees Celsius
    humidity = np.random.uniform(low=20, high=100, size=num_samples) # percentage
    pressure = np.random.normal(loc=1013, scale=10, size=num_samples) # hPa
    
    # Target: future_temp roughly dependent on current features
    # simple synthetic relationship: higher humidity reduces temp variance, lower pressure implies storm/cool down
    future_temp = temp + (humidity * 0.02) - ((pressure - 1013) * 0.1) + np.random.normal(loc=0, scale=2, size=num_samples)
    
    df = pd.DataFrame({
        'temp': temp,
        'humidity': humidity,
        'pressure': pressure,
        'future_temp': future_temp
    })
    return df

def train_and_save_model():
    print("Generating synthetic weather data...")
    df = generate_synthetic_data(2000)
    
    X = df[['temp', 'humidity', 'pressure']]
    y = df['future_temp']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForestRegressor model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Model trained successfully. Test MSE: {mse:.4f}")
    
    # Save the model
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'weather_model_v1.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_save_model()
