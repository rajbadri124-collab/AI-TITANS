from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import threading, time, random, os, datetime

from predict import predict_congestion
from green_wave import (check_and_trigger_green_wave,
                         get_all_junction_statuses, JUNCTIONS)
from alerts import fire_alert, get_recent_alerts, clear_alerts
from weather import simulate_weather
from traffic_intel import get_traffic_intel
from chatbot import get_chatbot_response
from forecast_engine import get_network_forecast, recommend_routes

app = Flask(__name__)
CORS(app)

# --- Shared state ---
junction_states = {}
weather_cache = {}
traffic_intel_cache = {}
forecast_cache = {}
last_ambulance_position = {"lat": None, "lng": None, "active": False}
data_ingestion_log = [] 

def simulate_congestion():
    """Background thread: updates telemetric state every 30s."""
    while True:
        try:
            hour = datetime.datetime.now().hour
            is_rush = 1 if hour in [8, 9, 17, 18, 19] else 0
            is_weekend = 1 if datetime.datetime.now().strftime("%A") in ["Saturday", "Sunday"] else 0
            for jid in JUNCTIONS:
                w_data = simulate_weather(jid)
                weather_cache[jid] = w_data
                weather_enc = 1 if w_data["condition"] == "Rainy" else (2 if w_data["condition"] == "Sunny" else 0)
                result = predict_congestion(hour, is_rush, is_weekend, weather_enc)
                junction_states[jid] = result
                traffic_intel_cache[jid] = get_traffic_intel(jid, result["level"])
                packet = {
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    "junction": JUNCTIONS[jid]["name"],
                    "source": "IOT_NODE_" + jid,
                    "type": "TELEMETRY",
                    "payload": f"LVL={result['level']} | CONF={result['confidence']} | TMP={w_data['temperature_c']}C"
                }
                data_ingestion_log.insert(0, packet)
                if len(data_ingestion_log) > 50: data_ingestion_log.pop()
            forecast_cache.update(get_network_forecast(JUNCTIONS, 1))
        except Exception as e:
            print(f"Simulation error: {e}")
        time.sleep(30)

thread = threading.Thread(target=simulate_congestion, daemon=True)
thread.start()

# ---- Serve Frontend ----

@app.route("/")
def root():
    # Frontend logic handles the initial check, but we serve login.html by default
    return send_from_directory("../frontend", "login.html")

@app.route("/dashboard")
def dashboard():
    return send_from_directory("../frontend", "dashboard.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("../frontend", filename)


# ---- API ENDPOINTS ----

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if email == "admin@aeropath.ai" and password == "password123":
        return jsonify({"status": "success", "token": "mock-jwt-token-7788"})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route("/api/geocode", methods=["GET"])
def reverse_geocode():
    """Simulates finding the nearest junction from a lat/lng."""
    lat = float(request.args.get("lat", 0))
    lng = float(request.args.get("lng", 0))
    
    # Distance based mock-up
    nearest = None
    min_dist = 999
    for jid, data in JUNCTIONS.items():
        dist = ((data["lat"] - lat)**2 + (data["lng"] - lng)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest = {"id": jid, "name": data["name"]}
    
    if min_dist > 0.1: # Too far from our cluster
        return jsonify({"status": "offline", "message": "Outside monitored zone, defaulting to MG Road.", "id": "J1", "name": "MG Road"})
    
    return jsonify({"status": "live", "id": nearest["id"], "name": nearest["name"]})

@app.route("/api/route", methods=["GET"])
def route_plan():
    origin, dest = request.args.get("origin"), request.args.get("dest")
    if not origin or not dest or origin not in JUNCTIONS or dest not in JUNCTIONS:
        return jsonify({"error": "Invalid origin/dest"}), 400
    if origin == dest:
        return jsonify({"error": "Origin and destination are the same."}), 400
    
    result = recommend_routes(origin, dest, JUNCTIONS, junction_states, forecast_cache)
    
    # Add 'Proper Reason' based on intelligence
    dest_intel = traffic_intel_cache.get(dest, {})
    origin_intel = traffic_intel_cache.get(origin, {})
    
    reason = "Optimized based on real-time flow."
    if result["recommendation"] == "alternate":
        reason = f"Avoids {dest_intel.get('cause', 'congestion')} at destination. Forecast predicts high delay."
    elif result["direct_route"]["congestion_level"] != "LOW":
        reason = f"Direct route is congested, but alternate route via {result['alternate_route']['via']} is longer/slower."
    else:
        reason = "Green-tier flow detected. Direct path is optimal."

    result["reason"] = reason
    return jsonify(result)

@app.route("/api/dashboard/data", methods=["GET"])
def dashboard_data():
    junctions = get_all_junction_statuses()
    for j in junctions:
        jid = j["id"]
        state = junction_states.get(jid, {"level": "LOW", "confidence": 0.5})
        j.update({"congestion": state["level"], "confidence": state["confidence"], 
                  "weather": weather_cache.get(jid, {}), "intel": traffic_intel_cache.get(jid, {}),
                  "forecast": forecast_cache.get(jid, [])})
    
    return jsonify({
        "junctions": junctions, 
        "ingestion_log": data_ingestion_log[:10],
        " ambulance": last_ambulance_position,
        "stats": { "data_source": "REAL-TIME", "active_nodes": len(JUNCTIONS) }
    })

@app.route("/api/ambulance/gps", methods=["POST"])
def ambulance_gps_live():
    data = request.get_json()
    v_id, lat, lng = data.get("vehicle_id", "AMB-01"), float(data.get("lat")), float(data.get("lng"))
    last_ambulance_position.update({"lat": lat, "lng": lng, "active": True})
    evp_result = check_and_trigger_green_wave(v_id, lat, lng, threshold_m=600)
    for item in evp_result["triggered"]:
        fire_alert(item["junction_id"], item["junction_name"], v_id, item["distance_m"])
    return jsonify({"status": "success", "evp": evp_result})

@app.route("/api/chat", methods=["POST"])
def chat():
    msg = request.get_json().get("message", "")
    return jsonify(get_chatbot_response(msg, junction_states, weather_cache, last_ambulance_position, traffic_intel_cache, JUNCTIONS, forecast_cache))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
