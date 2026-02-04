from fastapi import FastAPI, Response, status
from datetime import datetime
import time
import uvicorn
import logging

# Configuration
PORT = 8001
SERVICE_NAME = "upi_psp"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI()

# Global State for Faults
latency_ms = 0
force_error = False

@app.get("/health")
def health(response: Response):
    global latency_ms, force_error
    if force_error:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"service": SERVICE_NAME, "status": "down"}
    
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)
        
    return {
        "service": SERVICE_NAME,
        "status": "healthy",
        "latency_injected": latency_ms > 0,
        "error_injected": force_error,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/admin/fault")
def inject_fault(latency: int = 0, error: bool = False):
    global latency_ms, force_error
    latency_ms = latency
    force_error = error
    import requests
    try:
        severity = "warning" if latency > 0 or error else "info"
        msg = f"User injected fault: latency={latency}ms, error={error}"
        requests.post("http://127.0.0.1:8010/backend/log", json={
            "service": SERVICE_NAME,
            "event_type": "fault_injection",
            "severity": severity,
            "message": msg,
            "latency": float(latency),
            "error_rate": 1.0 if error else 0.0
        }, timeout=1)
    except:
        pass
    return {"message": "fault updated", "latency": latency, "error": error}

@app.post("/pay")
def pay(response: Response):
    if force_error:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"error": "Injected Failure"}
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)
    
    time.sleep(0.1) # Simulate processing
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
