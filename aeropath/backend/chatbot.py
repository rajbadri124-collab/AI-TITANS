"""
chatbot.py - AI Transport Advisor chatbot logic.
Handles natural language queries about traffic, weather, routes and transport.
No external LLM needed — rule-based + context-aware responses.
"""
import datetime
import re
import os
import requests
from dotenv import load_dotenv

load_dotenv()

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

def get_chatbot_response(user_input, junction_states, weather_data, last_ambulance, traffic_intel_data, JUNCTIONS, forecast_cache):
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
    j_forecast = forecast_cache.get(jid, [])
    
    # Reach-time analysis (forecast)
    reach_text = ""
    if j_forecast:
        lvl_30 = j_forecast[1]["level"] if len(j_forecast) > 1 else "Unknown"
        if lvl_30 == "HIGH":
            reach_text = f"WARNING: Traffic at {j_name} is predicted to spike to HIGH in 30 minutes. "

    condition = j_weather.get("condition", "Sunny")
    icon = j_weather.get("icon", "☀️")
    temp = j_weather.get("temperature_c", 28)
    advice = j_weather.get("advice", "Normal conditions")
    suggestions = ", ".join(j_weather.get("transport_suggestions", ["Car", "Bike"]))
    level = j_state.get("level", "LOW")
    
    # Mode specific advice
    best_mode = "Car"
    is_rush = hour in [8, 9, 17, 18, 19]
    if is_rush or level in ["MEDIUM", "HIGH"]:
        best_mode = "Metro (Purple/Green Line)" if "Bengaluru" in j_name or jid in ["J1","J2","J3"] else "Bike/Rapid"
    if condition == "Rainy":
        best_mode = "Metro or Cab"

    # --- Live xAI / Grok Integration ---
    xai_key = os.environ.get("XAI_API_KEY")
    if xai_key:
        system_prompt = f"""You are AeroPath AI, a proactive and creative Urban Mobility Expert.
Context:
- User Destination: {ctx_dest or 'Unknown'} (Mode: {ctx_mode})
- Current Junction ({j_name}): Status={level}, Weather={condition} ({temp}C).
- Forecast: {reach_text or 'Stable for next 60m'}.
- Recommended Mode: {best_mode}.
- Ambulance AMB-01: {'ACTIVE' if last_ambulance.get("active") else 'Standby'}

Task: 
1. If the user is in a 'Car' during peak/rain, suggest 'Metro' or 'Rapid' to save time.
2. Warn the user if traffic will be bad when they arrive (Reach-Time Analysis).
3. Be proactive and helpful. Keep it to 2-3 sentences max. Use <b>tags for emphasis."""
        
        try:
            resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}", "Content-Type": "application/json"},
                json={
                    "model": "grok-beta", 
                    "messages": [
                        {"role": "system", "content": system_prompt}, 
                        {"role": "user", "content": msg}
                    ]
                },
                timeout=8
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                reply = reply.replace("**", "<b>").replace("\n", "<br>")
                return {"reply": f"🤖 <b>AeroPath AI:</b><br>{reply}", "type": "llm"}
        except Exception as e:
            print("xAI Request Failed:", e)

    # Fallback/Rule-based Intelligence
    if any(w in msg for w in ["route", "short", "best", "traffic", "peak", "time", "suggest"]):
        peak_text = "It is currently <b>PEAK RUSH HOUR</b>." if is_rush else "Traffic is currently flowing normally."
        rec_text = f"I suggest switching to <b>{best_mode}</b> to bypass the current {level} congestion." if best_mode.lower() != ctx_mode.lower() else f"Your {ctx_mode} is optimized for these conditions."
        
        return {"reply": f"{reach_text}{peak_text} {icon} {condition} detected.<br><br>{rec_text}", "type": "route_intel"}

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
