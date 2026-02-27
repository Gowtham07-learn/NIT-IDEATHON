import uvicorn
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from datetime import datetime
import time
import requests
import logging
import sys
import os

# Fix path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services.local_llm import ask_llm

# Configuration
PORT = 8000
SERVICE_NAME = "gateway"
UPI_URL = "http://127.0.0.1:8001/pay"
BANK_URL = "http://127.0.0.1:8002/authorize"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI()

@app.post("/ai/advise")
def ai_advise(data: dict):
    """
    Endpoint for getting AI-driven root cause and solution advice.
    """
    prompt = f"""
    You are a production DevOps engineer.
    Metrics Data: {data}

    Explain:
    1. Root cause
    2. Risk level
    3. Fix steps
    4. Prevention
    """
    result = ask_llm(prompt)
    return {"solution": result}

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
    logger.info(f"Fault injected: latency={latency}ms, error={error}")
    
    # Log event
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

@app.post("/transaction")
def transaction(response: Response):
    if force_error:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"error": "Injected Failure"}
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)
        
    try:
        # Business Logic: Call UPI and Bank
        requests.post(UPI_URL, timeout=5)
        requests.post(BANK_URL, timeout=5)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Transaction bit failed: {e}")
        response.status_code = 502
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
