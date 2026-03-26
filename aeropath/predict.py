import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# --- Load dataset ---
df = pd.read_csv("data/traffic_data.csv")

# --- Features & target ---
FEATURES = ["hour", "is_rush_hour", "is_weekend", "weather_encoded"]
TARGET = "congestion_level"

X = df[FEATURES]
y = df[TARGET]

# --- Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# --- Train model ---
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- Evaluate ---
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2%}")
print(classification_report(y_test, y_pred,
      target_names=["LOW", "MEDIUM", "HIGH"]))

# --- Save model ---
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/congestion_model.pkl")
print("Model saved to models/congestion_model.pkl")

# --- Prediction function (used by Flask) ---
def load_model():
    return joblib.load("models/congestion_model.pkl")

def predict_congestion(hour, is_rush, is_weekend, weather_encoded):
    model = load_model()
    features = [[hour, is_rush, is_weekend, weather_encoded]]
    prediction = model.predict(features)[0]
    confidence = max(model.predict_proba(features)[0])
    level_map = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
    return {
        "level": level_map[prediction],
        "confidence": round(float(confidence), 2),
        "forecast_window": "15-60 minutes"
    }

# --- Quick test ---
if __name__ == "__main__":
    result = predict_congestion(
        hour=8, is_rush=1, is_weekend=0, weather_encoded=1
    )
    print("Test prediction:", result)
