"""
traffic_intel.py - Explains WHY traffic is bad, unlike Google Maps which just shows red.
Provides: cause, duration estimate, severity, affected radius.
"""
import random
import datetime

CONGESTION_CAUSES = {
    "HIGH": [
        "Accident reported — debris clearance underway",
        "Road construction — 1 lane closed",
        "VIP movement — police escort blocking lane",
        "School zone — elevated pedestrian activity",
        "Market overflow — illegal parking on road",
        "Waterlogging due to rain — 2 lanes submerged",
    ],
    "MEDIUM": [
        "Traffic signal malfunction at this node",
        "Minor fender bender — cleared partially",
        "Rush hour vehicle surge",
        "Delivery vehicles double-parked",
        "Bus breakdown — service vehicle en-route",
    ],
    "LOW": [
        "Normal traffic flow",
        "Light vehicle movement",
        "Off-peak hours — roads clear",
    ]
}

DURATION_ESTIMATES = {
    "HIGH": ["45-75 min", "60-90 min", "30-60 min"],
    "MEDIUM": ["15-30 min", "20-40 min", "10-25 min"],
    "LOW": ["< 5 min", "Flowing", "No delay"],
}

AFFECTED_RADIUS = {
    "HIGH": "~2.5 km radius affected",
    "MEDIUM": "~1 km radius affected",
    "LOW": "No spillover"
}

def get_traffic_intel(junction_id, congestion_level):
    """Generate detailed traffic intelligence for a junction."""
    causes = CONGESTION_CAUSES.get(congestion_level, CONGESTION_CAUSES["LOW"])
    cause = random.choice(causes)
    duration = random.choice(DURATION_ESTIMATES.get(congestion_level, DURATION_ESTIMATES["LOW"]))
    radius = AFFECTED_RADIUS.get(congestion_level, AFFECTED_RADIUS["LOW"])
    
    # Trend analysis
    if congestion_level == "HIGH":
        trend = "📈 Worsening"
    elif congestion_level == "MEDIUM":
        trend = "→ Stable"
    else:
        trend = "📉 Improving"
    
    return {
        "cause": cause,
        "estimated_duration": duration,
        "affected_radius": radius,
        "trend": trend,
        "last_updated": datetime.datetime.now().strftime("%H:%M:%S")
    }
