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


# Junction lat/lng — must match JUNCTIONS in green_wave.py
JUNCTION_COORDS = {
    "J1": (12.9716, 77.5946),   # MG Road
    "J2": (12.9352, 77.6245),   # Koramangala
    "J3": (12.9784, 77.6408),   # Indiranagar
    "J4": (12.9921, 77.5559),   # Rajajinagar
    "J5": (12.9116, 77.6395),   # HSR Layout
}

# WMO weather code → (condition, emoji)
WMO_MAP = {
    0:  ("Clear Sky",     "☀️"),
    1:  ("Partly Cloudy", "🌤"),
    2:  ("Partly Cloudy", "⛅"),
    3:  ("Overcast",      "☁️"),
    45: ("Foggy",         "🌫"),
    48: ("Foggy",         "🌫"),
    51: ("Drizzle",       "🌦"),
    53: ("Drizzle",       "🌦"),
    55: ("Drizzle",       "🌦"),
    61: ("Rainy",         "🌧"),
    63: ("Rainy",         "🌧"),
    65: ("Heavy Rain",    "🌧"),
    71: ("Snowy",         "❄️"),
    80: ("Showers",       "🌦"),
    81: ("Showers",       "🌦"),
    95: ("Thunderstorm",  "⛈"),
}

def simulate_weather(junction_id):
    """
    Fetches real-time weather from Open-Meteo using each junction's actual coordinates.
    """
    lat, lng = JUNCTION_COORDS.get(junction_id, (12.9716, 77.5946))
    hour = datetime.datetime.now().hour

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lng}"
            f"&current_weather=true"
            f"&hourly=relative_humidity_2m"
            f"&wind_speed_unit=kmh"
            f"&timezone=Asia%2FKolkata"
        )
        res = requests.get(url, timeout=6)
        data = res.json()
        cw = data["current_weather"]
        code = int(cw.get("weathercode", 0))
        temp = round(cw.get("temperature", 28))
        wind = round(cw.get("windspeed", 10))
        hum  = data.get("hourly", {}).get("relative_humidity_2m", [65])[hour]

        condition, icon = WMO_MAP.get(code, WMO_MAP.get((code // 10) * 10, ("Partly Cloudy", "⛅")))

        # Night icon override — after 6 PM or before 6 AM, use moon for clear skies
        if (hour >= 18 or hour < 6) and condition in ("Clear Sky", "Partly Cloudy"):
            icon = "🌙"

        impact = WEATHER_IMPACT.get(condition, WEATHER_IMPACT.get("Partly Cloudy", {"delay_multiplier": 1.0, "advice": "Normal conditions."}))

        return {
            "condition": condition,
            "icon": icon,
            "temperature_c": temp,
            "wind_kmh": wind,
            "humidity_pct": hum,
            "delay_multiplier": impact["delay_multiplier"],
            "advice": impact["advice"],
            "transport_suggestions": TRANSPORT_SUGGESTIONS.get(condition, ["Car", "Bus"]),
            "source": f"REAL-TIME (Open-Meteo @ {lat},{lng})"
        }
    except Exception as e:
        print(f"Weather Fetch Error [{junction_id}]: {e}")
        return {
            "condition": "Unknown", "icon": "🌐", "temperature_c": "--", "humidity_pct": 60,
            "delay_multiplier": 1.0, "advice": "Weather data unavailable.",
            "transport_suggestions": ["Car", "Bus"], "source": "FETCH FAILED"
        }
