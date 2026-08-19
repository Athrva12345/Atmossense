# AtmosSense: Temperature Prediction Model (v1.0)

## Overview
This document serves as the Model Card for the AtmosSense machine learning pipeline. The current model uses a Scikit-Learn `RandomForestRegressor` to predict the expected ambient temperature 1 hour into the future (which serves as the anchor point for the 5-hour extrapolated interpolation).

## Features
The model requires the following features, extracted natively in the Celery task (`weather/tasks.py`) from the OpenWeatherMap API and the current UTC time:
- **`temp`**: Current temperature (Celsius)
- **`humidity`**: Relative humidity (%)
- **`pressure`**: Atmospheric pressure (hPa)
- **`hour`**: Current hour of the day (0-23)
- **`month`**: Current month of the year (1-12)

## Model Architecture and Hyperparameters
- **Algorithm**: `RandomForestRegressor` (Scikit-Learn)
- **Hyperparameters**:
  - `n_estimators`: 100
  - `max_depth`: 10
  - `random_state`: 42

## Current Performance Metrics
*(Evaluated on a synthetic test split in v1.0)*
- **RMSE (Root Mean Squared Error)**: ~3.36°C
- **MAE (Mean Absolute Error)**: ~2.64°C
- **R² (Coefficient of Determination)**: ~0.81

## Artifact Generation and Retraining
To train a new version of the model, you can run the offline training script directly. This script synthesizes weather time-series data, extracts features, trains the regressor, and dumps both the `.joblib` model artifact and a `metadata.json` describing the performance.

**To Retrain the Model:**
1. Activate the python environment (e.g., inside the Docker container or local venv).
2. Run the script:
   ```bash
   python ml/train.py
   ```
3. The script will automatically overwrite `ml/models/model_v1.joblib` and `ml/models/metadata.json`.
4. Run the test suite to ensure the new model predictions stay within sane bounds:
   ```bash
   pytest weather/tests/test_ml.py
   ```

## Production Integration
The Celery worker uses a **Singleton pattern** to ensure the `.joblib` model is only loaded from disk *once* per worker process, keeping inference latency sub-millisecond and preventing disk I/O bottlenecks.
