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
    
    # Extract Context from appended string "(User is traveling to {dest} via {mode})"
    ctx_dest = None
    ctx_mode = "car"
    dest_match = re.search(r"traveling to (.*?) via (.*?)\)", msg)
    if dest_match:
        ctx_dest = dest_match.group(1).title()
        ctx_mode = dest_match.group(2)
        msg = re.sub(r"\(user is.*?\)", "", msg).strip() # Clean for intent matching

    jid = match_junction(msg)
    j_name = JUNCTIONS[jid]["name"] if jid else (ctx_dest or "MG Road")
    jid = jid or "J1"
    
    j_state = junction_states.get(jid, {"level": "LOW", "confidence": 0.5})
    j_weather = weather_data.get(jid, {})
    j_intel = traffic_intel_data.get(jid, {})
    
    # ... (existing data setup) ...
    condition = j_weather.get("condition", "Sunny")
    icon = j_weather.get("icon", "☀️")
    temp = j_weather.get("temperature_c", 28)
    advice = j_weather.get("advice", "Normal conditions")
    suggestions = ", ".join(j_weather.get("transport_suggestions", ["Car", "Bike"]))
    level = j_state.get("level", "LOW")
    
    # Mode specific advice
    mode_notes = {
        "bike": "Helmet is mandatory. Watch out for potholes.",
        "car": "Seatbelts on. Ideal for current weather.",
        "bus": "Check BMTC/Local schedules. Expect stops."
    }

    if "cafe" in msg or "coffee" in msg:
        loc = ctx_dest or j_name
        return {"reply": f"☕ There are several popular cafes near {loc}. I'd recommend 'Blue Tokai' or 'Third Wave' for a quick {ctx_mode} stop.", "type":"suggestion"}

    if "safe" in msg:
        return {"reply": f"🛡️ Safety Check: Travel via {ctx_mode} to {ctx_dest or j_name} looks good. {mode_notes.get(ctx_mode, '')}", "type":"safety"}

    # Determine intent (existing fallbacks)
    if any(w in msg for w in ["weather", "rain", "sun", "fog"]):
        return {"reply": f"{icon} {j_name}: {condition}, {temp}°C.\n💡 {advice}", "type": "weather"}
    
    elif any(w in msg for w in ["transport", "vehicle", "how to"]):
        return {"reply": f"Best transport for {j_name} ({ctx_mode} selected):\n✅ {suggestions}", "type": "transport"}
    
    elif any(w in msg for w in ["ambulance", "gps"]):
        st = "ACTIVE" if last_ambulance.get("active") else "Standby"
        return {"reply": f"🚑 AMB-01 Status: {st}. Coords: {last_ambulance.get('lat')}, {last_ambulance.get('lng')}", "type": "ambulance"}
    
    elif any(w in msg for w in ["hello", "hi", "hey", "help"]):
        return {"reply": f"👋 Hi! I'm AeroPath AI. I see you're heading to {ctx_dest or 'somewhere exciting'} via {ctx_mode}. How can I help with traffic or weather?", "type": "greeting"}
    
    return {
        "reply": f"I'm monitoring your route to {ctx_dest or 'the destination'}. Ask me about 'cafes', 'traffic', or 'safety'!",
        "type": "default"
    }
