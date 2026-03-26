from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import threading, time, random
import os

from predict import predict_congestion
from green_wave import (check_and_trigger_green_wave,
                         get_all_junction_statuses, JUNCTIONS)
from alerts import fire_alert, get_recent_alerts, clear_alerts

# Set working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder="templates")
CORS(app)

# --- In-memory junction congestion state ---
junction_states = {}

def simulate_congestion():
    """Background thread: update junction predictions every 30 seconds."""
    while True:
        hour = int(time.strftime("%H"))
        is_rush = 1 if hour in [8, 9, 17, 18, 19] else 0
        is_weekend = 1 if time.strftime("%A") in ["Saturday","Sunday"] else 0
        weather_enc = random.randint(0, 2)
        for jid in JUNCTIONS:
            try:
                result = predict_congestion(hour, is_rush,
                                            is_weekend, weather_enc)
                junction_states[jid] = result
            except:
                pass
        time.sleep(30)

thread = threading.Thread(target=simulate_congestion, daemon=True)
thread.start()

def get_best_alternative_route(exclude_jids):
    """Finds the nearest junction with LOW traffic to use as a detour."""
    best_alt = "Outer Ring Road (Default)"
    for jid, jdata in JUNCTIONS.items():
        if jid not in exclude_jids:
            st = junction_states.get(jid, {}).get("level", "LOW")
            if st == "LOW":
                return jdata["name"]
    # Fallback to any non-excluded road
    for jid, jdata in JUNCTIONS.items():
        if jid not in exclude_jids:
            return jdata["name"]
    return best_alt

# ---- ENDPOINTS ----

@app.route("/")
def index():
    """ Serve the integrated frontend """
    return render_template("index.html")

@app.route("/api/predict", methods=["GET"])
def predict():
    """Manual congestion prediction."""
    hour = int(request.args.get("hour", 8))
    is_rush = int(request.args.get("is_rush", 0))
    is_weekend = int(request.args.get("is_weekend", 0))
    weather = int(request.args.get("weather", 0))
    result = predict_congestion(hour, is_rush, is_weekend, weather)
    return jsonify(result)

@app.route("/api/ambulance/update", methods=["POST"])
def ambulance_update():
    """Receive ambulance GPS and trigger green wave if needed."""
    data = request.get_json()
    vehicle_id = data.get("vehicle_id", "AMB-01")
    lat = float(data.get("lat"))
    lng = float(data.get("lng"))

    # Determine detour before triggering
    best_alt = get_best_alternative_route([])
    evp_result = check_and_trigger_green_wave(vehicle_id, lat, lng, 500, best_alt)

    for item in evp_result["triggered"]:
        fire_alert(
            item["junction_id"],
            item["junction_name"],
            vehicle_id,
            item["distance_m"]
        )
        # Force the message in the DB to include the detour generated
        item["message"] = f"EMERGENCY: Ambulance on {item['junction_name']}! Green Wave activated. Traffic divert to {best_alt}!"

    return jsonify(evp_result)

@app.route("/api/junctions", methods=["GET"])
def get_junctions():
    """Return all junctions with congestion level + green wave status."""
    junctions = get_all_junction_statuses()
    for j in junctions:
        if j["id"] in junction_states:
            j["congestion"] = junction_states[j["id"]]["level"]
            j["confidence"] = junction_states[j["id"]]["confidence"]
        else:
            j["congestion"] = "LOW"
            j["confidence"] = 0.5
    return jsonify(junctions)

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Return last 10 alerts."""
    return jsonify(get_recent_alerts(10))

@app.route("/api/dashboard/data", methods=["GET"])
def dashboard_data():
    """Single endpoint for everything the frontend needs."""
    junctions = get_all_junction_statuses()
    for j in junctions:
        if j["id"] in junction_states:
            j["congestion"] = junction_states[j["id"]]["level"]
            j["confidence"] = junction_states[j["id"]]["confidence"]
        else:
            j["congestion"] = "LOW"
            j["confidence"] = 0.5
    return jsonify({
        "junctions": junctions,
        "alerts": get_recent_alerts(5),
        "stats": {
            "active_alerts": len(get_recent_alerts(100)),
            "junctions_monitored": len(JUNCTIONS),
            "commute_saving_pct": 17
        }
    })

@app.route("/api/demo/scenario_a", methods=["GET"])
def scenario_a():
    """Rush hour congestion demo."""
    result = predict_congestion(
        hour=8, is_rush=1, is_weekend=0, weather_encoded=1
    )
    return jsonify({
        "scenario": "Rush Hour — Monday 8AM, Rainy",
        "prediction": result,
        "message": "High congestion predicted at J2. Rerouting suggested."
    })

@app.route("/api/demo/scenario_b", methods=["GET"])
def scenario_b():
    """Ambulance approaching J1 demo."""
    clear_alerts()
    best_alt = get_best_alternative_route(["J1", "J2"])
    result = check_and_trigger_green_wave(
        "AMB-01", 12.9650, 77.5920, 800, best_alt
    )
    for item in result["triggered"]:
        msg = f"EMERGENCY: Ambulance on {item['junction_name']}! Green Wave activated. Traffic divert to {best_alt}!"
        fire_alert(item["junction_id"], item["junction_name"], "AMB-01", item["distance_m"])
        # Update the stored message explicitly so it's correct
        conn = __import__("sqlite3").connect("database.db")
        conn.cursor().execute("UPDATE alerts SET message=? WHERE junction_id=?", (msg, item["junction_id"]))
        conn.commit()
        conn.close()

    return jsonify({
        "scenario": "Ambulance Dispatch — Unit AMB-01",
        "evp_result": result,
        "alerts_fired": len(result["triggered"])
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
