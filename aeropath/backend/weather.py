import requests
import random
import datetime

# wttr.in mapping for our dashboard
WEATHER_MAP = {
    "sunny": "Sunny", "clear": "Sunny",
    "cloud": "Partly Cloudy", "overcast": "Partly Cloudy",
    "fog": "Foggy", "mist": "Foggy",
    "rain": "Rainy", "drizzle": "Drizzle", "shower": "Rainy",
    "thunder": "Thunderstorm", "storm": "Thunderstorm",
    "snow": "Snowy"
}

WEATHER_ICONS = {
    "Sunny": "☀️", "Hot": "🌡️", "Partly Cloudy": "⛅",
    "Foggy": "🌫️", "Rainy": "🌧️", "Drizzle": "🌦️",
    "Thunderstorm": "⛈️", "Clear": "🌙", "Snowy": "❄️"
}

WEATHER_IMPACT = {
    "Sunny": {"delay_multiplier": 1.0, "advice": "Normal conditions."},
    "Partly Cloudy": {"delay_multiplier": 1.0, "advice": "Mild conditions."},
    "Foggy": {"delay_multiplier": 1.4, "advice": "⚠️ Low visibility. Reduce speed."},
    "Rainy": {"delay_multiplier": 1.6, "advice": "⚠️ Wet roads. Increase distance."},
    "Drizzle": {"delay_multiplier": 1.2, "advice": "Slippery roads."},
    "Thunderstorm": {"delay_multiplier": 2.0, "advice": "🔴 Severe weather. Use public transport."},
    "Clear": {"delay_multiplier": 0.9, "advice": "Clear skies."},
    "Hot": {"delay_multiplier": 1.1, "advice": "Heat advisory."},
}

TRANSPORT_SUGGESTIONS = {
    "Sunny": ["🚗 Car / Cab", "🛵 Bike", "🚲 Cycling recommended"],
    "Partly Cloudy": ["🚗 Car", "🛵 Bike", "🚲 Cycling ok"],
    "Foggy": ["🚌 Bus (safer)", "🚗 Drive carefully", "❌ Avoid bikes"],
    "Rainy": ["🚇 Metro (best)", "🚌 BMTC Bus", "🚗 Cab", "❌ No bikes"],
    "Drizzle": ["🚗 Car", "🚇 Metro", "🛵 Ride cautiously"],
    "Thunderstorm": ["🚇 Metro ONLY", "🏠 Work from home"],
    "Clear": ["🚗 Car", "🛵 Bike", "🚲 Cycling great"],
}

_cache = {}

def simulate_weather(junction_id):
    """
    FETCHER: Uses wttr.in to get real-time weather for Bangalore.
    Uses junction_id to manage per-node variation (simulated from real base).
    """
    try:
        # Fetch real-time weather for Bangalore
        res = requests.get("https://wttr.in/Bangalore?format=j1", timeout=5)
        data = res.json()["current_condition"][0]
        
        real_temp = int(data["temp_C"])
        real_hum = int(data["humidity"])
        desc = data["weatherDesc"][0]["value"].lower()
        
        # Map wttr description to our internal types
        condition = "Sunny"
        for key, val in WEATHER_MAP.items():
            if key in desc:
                condition = val
                break
        
        # Add slight variation per junction for visual realism
        j_var = hash(junction_id) % 3 - 1 # -1, 0, or 1
        temp = real_temp + j_var
        
        impact = WEATHER_IMPACT.get(condition, WEATHER_IMPACT["Sunny"])
        
        return {
            "condition": condition,
            "icon": WEATHER_ICONS.get(condition, "🌤️"),
            "temperature_c": temp,
            "humidity_pct": real_hum,
            "delay_multiplier": impact["delay_multiplier"],
            "advice": impact["advice"],
            "transport_suggestions": TRANSPORT_SUGGESTIONS.get(condition, ["Car", "Bus"]),
            "source": "REAL-TIME (wttr.in)"
        }
    except Exception as e:
        # Fallback to simulation if offline
        print(f"Weather Fetch Error: {e}")
        return {
            "condition": "Sunny", "icon": "☀️", "temperature_c": 28, "humidity_pct": 60,
            "delay_multiplier": 1.0, "advice": "Normal conditions (Fallback).",
            "transport_suggestions": ["Car", "Bus"], "source": "SIMULATED (Fallback)"
        }
