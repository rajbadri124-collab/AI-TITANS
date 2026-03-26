import json
import datetime
import os
import sqlite3

DB_FILE = "database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id TEXT PRIMARY KEY,
                  time TEXT,
                  junction_id TEXT,
                  junction_name TEXT,
                  vehicle_id TEXT,
                  distance_m REAL,
                  message TEXT)''')
    conn.commit()
    conn.close()

def fire_alert(junction_id, junction_name, vehicle_id, distance_m):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    alert_id = datetime.datetime.now().strftime("%H%M%S%f")
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    message = f"Ambulance {vehicle_id} approaching {junction_name} ({distance_m}m). Green Wave ACTIVATED. Patrol units notified."
    
    c.execute("INSERT INTO alerts (id, time, junction_id, junction_name, vehicle_id, distance_m, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (alert_id, time_str, junction_id, junction_name, vehicle_id, distance_m, message))
    conn.commit()
    conn.close()
    
    return {
        "id": alert_id,
        "time": time_str,
        "junction_id": junction_id,
        "junction_name": junction_name,
        "vehicle_id": vehicle_id,
        "distance_m": distance_m,
        "message": message
    }

def get_recent_alerts(limit=10):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, time, junction_id, junction_name, vehicle_id, distance_m, message FROM alerts ORDER BY time DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    
    alerts = []
    for r in rows:
        alerts.append({
            "id": r[0], "time": r[1], "junction_id": r[2],
            "junction_name": r[3], "vehicle_id": r[4],
            "distance_m": r[5], "message": r[6]
        })
    return alerts

def clear_alerts():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
