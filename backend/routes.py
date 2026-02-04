from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import pandas as pd
import os
import sys

# Add parent directory to path to allow running as script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.event_logger import logger_instance
from backend.rca_engine import rca_instance

app = FastAPI(title="DPI Incident & RCA Backend")

class Event(BaseModel):
    service: str
    event_type: str
    severity: str
    message: str
    latency: Optional[float] = 0.0
    error_rate: Optional[float] = 0.0
    health: Optional[float] = 1.0
    dependencies: Optional[List[str]] = []

@app.get("/timeline")
def get_timeline(
    limit: int = 100, 
    service: Optional[str] = None, 
    severity: Optional[str] = None
):
    return logger_instance.get_events(limit=limit, service=service, severity=severity)

@app.post("/backend/log")
def log_backend_event(event: Event):
    return logger_instance.log_event(
        service=event.service,
        event_type=event.event_type,
        severity=event.severity,
        message=event.message,
        latency=event.latency,
        error_rate=event.error_rate,
        health=event.health,
        dependencies=event.dependencies
    )

@app.get("/rca")
def get_rca():
    result = rca_instance.analyze_root_cause(logger_instance)
    if not result:
        return {"message": "No active incidents detected."}
    return result

@app.get("/metrics/live")
def get_live_metrics():
    # Use absolute path to ensure file is found regardless of CWD
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_FILE = os.path.join(BASE_DIR, "data", "telemetry_realtime.csv")
    
    if not os.path.exists(DATA_FILE):
        return []
    try:
        df = pd.read_csv(DATA_FILE)
        return df.tail(10).to_dict(orient="records")
    except:
        return []

@app.get("/ai/insight")
def get_ai_insight(service: Optional[str] = None):
    insight = logger_instance.get_latest_insight(service)
    if not insight:
        return {"message": "No analysis available yet."}
    return insight

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
