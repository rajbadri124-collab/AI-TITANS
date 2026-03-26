import json
import datetime
import os

ALERT_FILE = "alerts.log"

def fire_alert(junction_id, junction_name, vehicle_id, distance_m):
    """Write a new alert to the log file."""
    alert = {
        "id": datetime.datetime.now().strftime("%H%M%S%f"),
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "junction_id": junction_id,
        "junction_name": junction_name,
        "vehicle_id": vehicle_id,
        "distance_m": distance_m,
        "message": f"Ambulance {vehicle_id} approaching "
                   f"{junction_name} ({distance_m}m). "
                   f"Green Wave ACTIVATED. Patrol units notified."
    }
    with open(ALERT_FILE, "a") as f:
        f.write(json.dumps(alert) + "\n")
    return alert

def get_recent_alerts(limit=10):
    """Return last N alerts from log file."""
    if not os.path.exists(ALERT_FILE):
        return []
    with open(ALERT_FILE, "r") as f:
        lines = f.readlines()
    alerts = []
    for line in lines[-limit:]:
        try:
            alerts.append(json.loads(line.strip()))
        except:
            pass
    return list(reversed(alerts))

def clear_alerts():
    """Clear alert log (use before demo)."""
    if os.path.exists(ALERT_FILE):
        os.remove(ALERT_FILE)
