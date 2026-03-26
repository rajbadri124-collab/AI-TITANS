"""
chatbot.py - AI Transport Advisor chatbot logic.
Handles natural language queries about traffic, weather, routes and transport.
No external LLM needed — rule-based + context-aware responses.
"""
import datetime
import re

RESPONSES = {
    "traffic": [
        "Based on real-time data, {junction} currently has {level} congestion. Cause: {cause}. Estimated delay: {duration}.",
        "Traffic at {junction} is {level} right now. {cause}. I'd recommend {alt} as a detour.",
    ],
    "weather": [
        "It's currently {icon} {condition} near {junction}. Temperature: {temp}°C. {advice}",
        "Weather near {junction}: {condition} with {humidity}% humidity. {advice}",
    ],
    "transport": [
        "Given {condition} weather and {level} traffic, I suggest: {suggestions}",
        "Best transport options right now: {suggestions}. Travel time estimate: {duration}.",
    ],
    "ambulance": [
        "Ambulance AMB-01 is currently at {lat}, {lng}. Green wave {status}.",
        "Emergency unit AMB-01 last seen at coordinates {lat}, {lng}. {status}.",
    ],
    "route": [
        "For travel from {origin} to {dest}, the current best route avoids {junction} ({level} congestion). Try via {alt}.",
    ],
    "default": [
        "I can help with traffic, weather, transport suggestions, and ambulance status. What do you want to know?",
        "Try asking: 'traffic at MG Road', 'weather Koramangala', 'best transport now', or 'ambulance status'.",
    ]
}

JUNCTION_ALIASES = {
    "mg road": "J1", "mg": "J1",
    "koramangala": "J2", "korama": "J2",
    "indiranagar": "J3", "indir": "J3",
    "rajajinagar": "J4", "raja": "J4",
    "hsr layout": "J5", "hsr": "J5",
}

def match_junction(text):
    text = text.lower()
    for alias, jid in JUNCTION_ALIASES.items():
        if alias in text:
            return jid
    return None

def get_chatbot_response(user_input, junction_states, weather_data, last_ambulance, traffic_intel_data, JUNCTIONS):
    """Generate a smart chatbot response based on user input and live context."""
    msg = user_input.lower().strip()
    hour = datetime.datetime.now().hour
    
    jid = match_junction(msg)
    j_name = JUNCTIONS[jid]["name"] if jid else "MG Road"
    jid = jid or "J1"
    
    j_state = junction_states.get(jid, {"level": "LOW", "confidence": 0.5})
    j_weather = weather_data.get(jid, {})
    j_intel = traffic_intel_data.get(jid, {})
    
    condition = j_weather.get("condition", "Sunny")
    icon = j_weather.get("icon", "☀️")
    temp = j_weather.get("temperature_c", 28)
    humidity = j_weather.get("humidity_pct", 60)
    advice = j_weather.get("advice", "Normal conditions")
    suggestions = ", ".join(j_weather.get("transport_suggestions", ["Car", "Bike"]))
    level = j_state.get("level", "LOW")
    cause = j_intel.get("cause", "Normal flow")
    duration = j_intel.get("estimated_duration", "No delay")
    
    # Determine intent
    if any(w in msg for w in ["weather", "rain", "sun", "fog", "hot", "cloudy", "thunder"]):
        return {
            "reply": f"{icon} {j_name}: {condition}, {temp}°C, {humidity}% humidity.\n💡 {advice}",
            "type": "weather"
        }
    
    elif any(w in msg for w in ["transport", "vehicle", "how to travel", "go by", "commute", "travel", "reach"]):
        return {
            "reply": f"Best transport near {j_name} ({condition} weather, {level} traffic):\n→ {suggestions}",
            "type": "transport"
        }
    
    elif any(w in msg for w in ["ambulance", "ambu", "emergency", "evp", "gps"]):
        if last_ambulance:
            lat = round(last_ambulance.get("lat", 12.97), 6)
            lng = round(last_ambulance.get("lng", 77.59), 6)
            status = "ACTIVE — Green Wave engaged" if last_ambulance.get("active") else "Standby"
            return {"reply": f"🚑 AMB-01 location: {lat}°N, {lng}°E\nStatus: {status}", "type": "ambulance"}
        return {"reply": "🚑 No active ambulance dispatch tracked currently.", "type": "ambulance"}
    
    elif any(w in msg for w in ["traffic", "congestion", "jam", "busy", "road"]):
        return {
            "reply": f"📍 {j_name} — Status: {level}\n📌 Cause: {cause}\n⏱ Est. delay: {duration}\n📊 Trend: {j_intel.get('trend', '→ Stable')}",
            "type": "traffic"
        }
    
    elif any(w in msg for w in ["route", "alternative", "detour", "reroute", "shortcut"]):
        others = [j for j in JUNCTIONS if j != jid and junction_states.get(j, {"level":"LOW"})["level"] != "HIGH"]
        alt = JUNCTIONS[others[0]]["name"] if others else "alternative route"
        return {
            "reply": f"🛣 {j_name} has {level} congestion.\n✅ Suggested detour: {alt}\nApprox time saving: 10-15 min",
            "type": "route"
        }
    
    elif any(w in msg for w in ["hello", "hi", "hey", "help"]):
        return {
            "reply": "👋 Hi! I'm AeroPath AI. I can tell you about:\n• 🚦 Traffic & congestion causes\n• ☀️ Weather conditions\n• 🚌 Best transport options\n• 🚑 Ambulance GPS status\n\nTry: 'traffic at Koramangala' or 'weather Indiranagar'",
            "type": "greeting"
        }
    
    return {
        "reply": "I didn't quite get that. Try asking:\n• 'traffic MG Road'\n• 'weather Koramangala'\n• 'best transport now'\n• 'ambulance status'",
        "type": "default"
    }
