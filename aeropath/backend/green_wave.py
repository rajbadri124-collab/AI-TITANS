from math import radians, sin, cos, sqrt, atan2
import datetime

# --- Define city junctions (Bengaluru mock coordinates) ---
JUNCTIONS = {
    "J1": {"lat": 12.9716, "lng": 77.5946, "name": "MG Road"},
    "J2": {"lat": 12.9352, "lng": 77.6245, "name": "Koramangala"},
    "J3": {"lat": 12.9500, "lng": 77.6100, "name": "Indiranagar"},
    "J4": {"lat": 12.9800, "lng": 77.5700, "name": "Rajajinagar"},
    "J5": {"lat": 12.9600, "lng": 77.6400, "name": "HSR Layout"}
}

# --- Tracks which junctions have active green waves ---
active_green_waves = {}

def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lng2 - lng1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def check_and_trigger_green_wave(vehicle_id, ambulance_lat,
                                  ambulance_lng, threshold_m=500):
    """
    Check if ambulance is within threshold of any junction.
    Trigger green wave if yes. Deactivate if moved away.
    Returns list of triggered junctions and alert messages.
    """
    results = []
    triggered_junctions = []
    
    # Sort junctions by distance to find the closest and the 'next' one
    sorted_junctions = []
    for jid, jdata in JUNCTIONS.items():
        dist = haversine_distance(
            ambulance_lat, ambulance_lng,
            jdata["lat"], jdata["lng"]
        )
        sorted_junctions.append((jid, jdata, dist))
    
    sorted_junctions.sort(key=lambda x: x[2])
    
    # Pre-calculate 'Next Junction' (the one after the current closest if current is < target)
    next_junction_info = None
    if len(sorted_junctions) > 1:
        if sorted_junctions[0][2] <= threshold_m:
            next_junction_info = sorted_junctions[1][1]["name"]

    for jid, jdata, dist in sorted_junctions:
        if dist <= threshold_m:
            # Trigger green wave
            active_green_waves[jid] = {
                "vehicle_id": vehicle_id,
                "triggered_at": datetime.datetime.now().strftime("%H:%M:%S"),
                "distance_m": round(dist)
            }
            triggered_junctions.append(jid)
            results.append({
                "junction_id": jid,
                "junction_name": jdata["name"],
                "distance_m": round(dist),
                "status": "GREEN_WAVE_ACTIVE",
                "traffic_mode": "ZERO_TRAFFIC",
                "next_vessel_preempt": next_junction_info,
                "message": f"EMERGENCY: Ambulance {vehicle_id} is "
                           f"{round(dist)}m from {jdata['name']}. "
                           f"Switching to ZERO_TRAFFIC mode. "
                           f"Next patrol at {next_junction_info or 'N/A'} alerted."
            })
        else:
            # Deactivate if ambulance moved away
            if jid in active_green_waves:
                if active_green_waves[jid].get("vehicle_id") == vehicle_id:
                    del active_green_waves[jid]

    return {
        "triggered": results,
        "active_green_waves": list(active_green_waves.keys()),
        "total_triggered": len(triggered_junctions),
        "next_predicted_junction": next_junction_info
    }

def get_all_junction_statuses():
    """Return all junctions with their current green wave status."""
    statuses = []
    for jid, jdata in JUNCTIONS.items():
        status = "GREEN_WAVE_ACTIVE" if jid in active_green_waves else "NORMAL"
        traffic_mode = "ZERO_TRAFFIC" if jid in active_green_waves else "BALANCED"
        statuses.append({
            "id": jid,
            "name": jdata["name"],
            "lat": jdata["lat"],
            "lng": jdata["lng"],
            "status": status,
            "traffic_mode": traffic_mode
        })
    return statuses
