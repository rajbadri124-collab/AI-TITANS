import requests
import time
import random

API_URL = "http://127.0.0.1:5000/api/ingest"
JUNCTIONS = ["J1", "J2", "J3", "J4", "J5"]

def push_realtime_packet(jid, level):
    payload = {
        "junction_id": jid,
        "level": level,
        "confidence": round(random.uniform(0.94, 0.99), 2),
        "source": "REAL_TIME_SENSOR_X102"
    }
    try:
        res = requests.post(API_URL, json=payload)
        if res.status_code == 200:
            print(f"[SUCCESS] Pushed {level} congestion to {jid}")
        else:
            print(f"[ERROR] {res.text}")
    except Exception as e:
        print(f"[FAILED] {e}")

if __name__ == "__main__":
    print("🚀 AeroPath Live Data Ingestion Demo")
    print("Pushing HIGH congestion to MG Road (J1) to trigger AI Rerouting...")
    push_realtime_packet("J1", "HIGH")
    time.sleep(2)
    print("Pushing MEDIUM congestion to Koramangala (J2)...")
    push_realtime_packet("J2", "MEDIUM")
    print("\n✅ Check the 'Live Telemetric Feed' on your Dashboard!")
