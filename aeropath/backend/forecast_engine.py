"""
forecast_engine.py
Short-term congestion forecasts for each junction.
Generates predictions for the next 15, 30, 60, and 120 minutes
using the trained ML model with time-shifted inputs.
"""
import datetime
import random
from math import radians, sin, cos, sqrt, atan2
from predict import predict_congestion

def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance in KM between two GPS coordinates."""
    R = 6371  # Earth radius in KM
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lng2 - lng1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

CONFIDENCE_DECAY = 0.04


def get_forecast(junction_id, base_weather_enc=0):
    """
    Produce a 4-window short-term forecast (15/30/60/120 min)
    for a single junction.
    """
    now = datetime.datetime.now()
    windows = [15, 30, 60, 120]
    forecasts = []

    for minutes in windows:
        future = now + datetime.timedelta(minutes=minutes)
        hour = future.hour
        is_rush = 1 if hour in [8, 9, 17, 18, 19] else 0
        is_weekend = 1 if future.strftime("%A") in ["Saturday", "Sunday"] else 0
        # Slightly vary weather for uncertainty
        w_enc = min(2, max(0, base_weather_enc + random.randint(-1, 1)))

        result = predict_congestion(hour, is_rush, is_weekend, w_enc)
        # Reduce confidence for further-out windows
        decay = CONFIDENCE_DECAY * (minutes / 15)
        adjusted_confidence = max(0.5, round(result["confidence"] - decay, 2))

        forecasts.append({
            "window_min": minutes,
            "label": f"+{minutes}m",
            "level": result["level"],
            "confidence": adjusted_confidence,
            "hour": hour
        })

    return forecasts


def get_network_forecast(junctions_dict, base_weather_enc=0):
    """
    Produce forecasts for all junctions.
    Returns dict keyed by junction id.
    """
    return {jid: get_forecast(jid, base_weather_enc) for jid in junctions_dict}


LEVEL_SCORE = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def score_junction_for_routing(jid, junction_states, forecast_data, window_min=30):
    """
    Composite routing score for a junction (lower = better to use in route).
    Combines current congestion + forecast.
    """
    current_level = junction_states.get(jid, {}).get("level", "LOW")
    current_score = LEVEL_SCORE.get(current_level, 1)

    forecast = forecast_data.get(jid, [])
    fw = next((f for f in forecast if f["window_min"] == window_min), None)
    forecast_score = LEVEL_SCORE.get(fw["level"], 1) if fw else 1

    return round((current_score * 0.4) + (forecast_score * 0.6), 2)


def recommend_routes(origin_id, dest_id, junctions_dict, junction_states, forecast_data):
    """
    Compare direct vs alternate routes using forecast-aware scoring.
    Returns primary route info, recommended route, and per-junction forecast.
    """
    # All junctions except origin and dest are potential waypoints
    waypoints = [j for j in junctions_dict if j not in (origin_id, dest_id)]

    # Score each waypoint
    scored = [(jid, score_junction_for_routing(jid, junction_states, forecast_data))
              for jid in waypoints]
    scored.sort(key=lambda x: x[1])

    # Direct route score
    direct_congestion = junction_states.get(dest_id, {}).get("level", "LOW")
    direct_score = LEVEL_SCORE.get(direct_congestion, 1)

    # Best alternate: lowest-scoring waypoint
    best_alt = scored[0] if scored else None
    alt_jid = best_alt[0] if best_alt else None
    alt_name = junctions_dict[alt_jid]["name"] if alt_jid else "No alternate"
    alt_score = best_alt[1] if best_alt else 3

    # Time estimates (rough simulation)
    origin_name = junctions_dict[origin_id]["name"]
    dest_name = junctions_dict[dest_id]["name"]

    # Calculate real distances
    def get_route_metrics(path_ids):
        total_km = 0
        for i in range(len(path_ids)-1):
            p1, p2 = junctions_dict[path_ids[i]], junctions_dict[path_ids[i+1]]
            total_km += haversine_distance(p1["lat"], p1["lng"], p2["lat"], p2["lng"])
        
        # Base speed 30 km/h + congestion delays
        avg_speed = 30 
        base_time = (total_km / avg_speed) * 60
        return round(total_km, 1), round(base_time, 1)

    direct_km, direct_base_time = get_route_metrics([origin_id, dest_id])
    direct_delay = (direct_score - 1) * 10 
    
    alt_km, alt_base_time = get_route_metrics([origin_id, alt_jid, dest_id]) if alt_jid else (direct_km, direct_base_time)
    alt_delay = (alt_score - 1) * 6

    return {
        "origin": {"id": origin_id, "name": origin_name},
        "destination": {"id": dest_id, "name": dest_name},
        "direct_route": {
            "path": [origin_name, dest_name],
            "path_coords": [[junctions_dict[origin_id]["lat"], junctions_dict[origin_id]["lng"]], 
                            [junctions_dict[dest_id]["lat"], junctions_dict[dest_id]["lng"]]],
            "congestion_level": direct_congestion,
            "distance_km": direct_km,
            "estimated_time_min": int(round(direct_base_time + direct_delay)),
            "score": direct_score,
            "recommended": direct_score <= 1.5
        },
        "alternate_route": {
            "path": [origin_name, alt_name, dest_name],
            "path_coords": [[junctions_dict[origin_id]["lat"], junctions_dict[origin_id]["lng"]],
                            [junctions_dict[alt_jid]["lat"], junctions_dict[alt_jid]["lng"]] if alt_jid else [],
                            [junctions_dict[dest_id]["lat"], junctions_dict[dest_id]["lng"]]],
            "via": alt_name,
            "distance_km": alt_km,
            "congestion_level": junction_states.get(alt_jid, {}).get("level", "LOW") if alt_jid else "LOW",
            "estimated_time_min": int(round(alt_base_time + alt_delay)),
            "score": alt_score,
            "recommended": alt_score < direct_score
        },
        "recommendation": "alternate" if alt_score < direct_score else "direct",
        "time_saving_min": max(0, int(round((direct_base_time + direct_delay) - (alt_base_time + alt_delay))))
    }
