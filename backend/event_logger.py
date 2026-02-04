import uuid
from datetime import datetime
from collections import deque
import threading

from copilot.advisor import AIAdvisor
import sys
import os

# Add parent directory if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class EventLogger:
    def __init__(self, max_events=5000):
        self.events = deque(maxlen=max_events)
        self.ai_insights = deque(maxlen=100) # Store recent AI results
        self.lock = threading.Lock()
        self.advisor = AIAdvisor()

    def run_ai_analysis(self, event):
        """Background worker to run AI analysis"""
        try:
            # Context builder
            context = {
                "service": event["service"],
                "reason": event["event_type"], # using event_type as proxy for reason
                "severity": event["severity"],
                "latency": event["latency"],
                "error_rate": event["error_rate"],
                "health": event["health"],
                "failed_dependencies": event["dependencies"],
                "injection_type": "None" # Can be refined if message contains injection info
            }
            if "injection" in event["message"].lower():
                context["injection_type"] = "Manual/Test Injection"

            insight = self.advisor.analyze_incident(context)
            
            if insight:
                with self.lock:
                    self.ai_insights.appendleft({
                        "event_id": event["id"],
                        "service": event["service"],
                        "timestamp": datetime.now().isoformat(),
                        "analysis": insight
                    })
        except Exception as e:
            print(f"Error in background AI analysis: {e}")

    def log_event(self, service, event_type, severity, message, latency=0.0, error_rate=0.0, health=1.0, dependencies=None):
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "event_type": event_type,
            "severity": severity,
            "latency": latency,
            "error_rate": error_rate,
            "health": health,
            "dependencies": dependencies or [],
            "message": message
        }
        with self.lock:
            self.events.appendleft(event)
        
        # Trigger AI Analysis immediately in background
        threading.Thread(target=self.run_ai_analysis, args=(event,), daemon=True).start()
        
        return event

    def get_events(self, limit=100, service=None, severity=None):
        with self.lock:
            filtered = list(self.events)
            if service:
                filtered = [e for e in filtered if e["service"].lower() == service.lower()]
            if severity:
                filtered = [e for e in filtered if e["severity"].lower() == severity.lower()]
            return filtered[:limit]

    def get_latest_insight(self, service=None):
        with self.lock:
            if not self.ai_insights:
                return None
            if service:
                for insight in self.ai_insights:
                    if insight["service"].lower() == service.lower():
                        return insight
                return None
            return self.ai_insights[0]

# Global instance
logger_instance = EventLogger()
