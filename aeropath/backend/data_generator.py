import pandas as pd
import numpy as np
import random
import os

np.random.seed(42)
random.seed(42)

junctions = ["J1", "J2", "J3", "J4", "J5"]
weather_options = ["sunny", "rainy", "foggy"]
records = []

for day in range(60):                        # 60 days of data
    for hour in range(24):
        for junction in junctions:
            is_rush = 1 if hour in [8,9,17,18,19] else 0
            is_weekend = 1 if day % 7 >= 5 else 0
            weather = random.choice(weather_options)
            weather_enc = {"sunny": 0, "rainy": 1, "foggy": 2}[weather]

            base = 20
            if is_rush: base += random.randint(30, 60)
            if weather == "rainy": base += random.randint(10, 20)
            if is_weekend: base -= random.randint(5, 15)
            vehicle_count = max(0, base + random.randint(-5, 5))

            if vehicle_count < 30:
                level = 0       # LOW
            elif vehicle_count < 60:
                level = 1       # MEDIUM
            else:
                level = 2       # HIGH

            records.append({
                "day": day,
                "hour": hour,
                "junction_id": junction,
                "is_rush_hour": is_rush,
                "is_weekend": is_weekend,
                "weather_encoded": weather_enc,
                "vehicle_count": vehicle_count,
                "congestion_level": level
            })

df = pd.DataFrame(records)
os.makedirs("../data", exist_ok=True)
df.to_csv("../data/traffic_data.csv", index=False)
print(f"Dataset created: {len(df)} rows")
print(df["congestion_level"].value_counts())
