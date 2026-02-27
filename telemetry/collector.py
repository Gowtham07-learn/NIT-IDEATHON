import time
import requests
import os
import logging
import csv
from collections import deque
from datetime import datetime

# Configuration
SERVICES = {
    "gateway": "http://127.0.0.1:8000/health",
    "upi": "http://127.0.0.1:8001/health",
    "bank": "http://127.0.0.1:8002/health"
}

DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "telemetry_realtime.csv")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Collector")

# Ensure Data Dir
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Using Deque for sliding window (Last 100 points per service)
# Total size = 3 services * 100 = 300
telemetry_buffer = deque(maxlen=300)

def collect_metrics():
    timestamp = datetime.now()
    
    for name, url in SERVICES.items():
        success = 0
        failure = 0
        latency = 0
        status_code = 0
        
        try:
            start = time.perf_counter()
            response = requests.get(url, timeout=10.0)
            # Debug print as requested
            print(f"DEBUG: {name} | Status: {response.status_code} | Text: {response.text[:100]}")
            
            latency = (time.perf_counter() - start) * 1000 # ms
            status_code = response.status_code
            
            if response.status_code == 200:
                success = 1
                failure = 0
            else:
                success = 0
                failure = 1
                logger.warning(f"{name} check failed with status {status_code}")
                
        except Exception as e:
            latency = 0
            success = 0
            failure = 1
            status_code = 503
            logger.error(f"{name} unreachable: {e}")

        # Add to buffer
        record = {
            "timestamp": timestamp,
            "service": name,
            "status": status_code,
            "latency_ms": latency,
            "success": success,
            "failure": failure,
            "error_rate": 1.0 if failure else 0.0,
            "health": 1.0 if success else 0.0
        }
        telemetry_buffer.append(record)

        # Incident Detection (Centralized Engine)
        try:
            # We need to import the engine dynamically or add to path
            import sys
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from backend.incident_engine import detect_incident

            # Check dependencies (mock logic: if UPI fails, Gateway sees it as 'dependency_down'?)
            # For now, simplistic view: just check current service metrics
            incident_result = detect_incident(record, dependencies=[])
            
            if incident_result["incident"]:
                logger.warning(f"Incident detected for {name}: {incident_result['reason']}")
                requests.post("http://127.0.0.1:8010/backend/log", json={
                    "service": name,
                    "event_type": incident_result["reason"],
                    "severity": incident_result["severity"],
                    "message": f"Detected {incident_result['reason']} in {name.upper()}",
                    "latency": latency,
                    "error_rate": record["error_rate"],
                    "health": record["health"],
                    "dependencies": [] 
                }, timeout=1)
        except Exception as e:
            logger.error(f"Error in incident check: {e}") 

    # Save to CSV
    try:
        keys = ["timestamp", "service", "status", "latency_ms", "success", "failure", "error_rate", "health"]
        with open(CSV_FILE, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(telemetry_buffer)
        logger.info(f"Updated CSV with {len(telemetry_buffer)} records")
    except Exception as e:
        logger.error(f"Failed to write to CSV: {e}")

if __name__ == "__main__":
    logger.info("Collector started. Polling every 5s...")
    while True:
        collect_metrics()
        time.sleep(5)
