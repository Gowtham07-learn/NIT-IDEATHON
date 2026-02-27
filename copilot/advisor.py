import requests
import json
import logging

logger = logging.getLogger("AI_Advisor")

class AIAdvisor:
    def __init__(self, ollama_url="http://localhost:11434/api/generate"):
        self.url = ollama_url
        self.model = "mistral:7b"

    def analyze_incident(self, incident_context):
        """
        analyze_incident(context):
        Full context analysis triggering Mistral.
        Context includes: service, latency, error_rate, health, injection_type, failed_dependencies, historical_trend
        """
        service = incident_context.get("service")
        reason = incident_context.get("reason", "unknown")
        
        prompt = f"""
        [CRITICAL INCIDENT REPORT]
        Service: {service}
        Incident Type: {reason.upper()}
        Severity: {incident_context.get('severity', 'warning')}
        
        -- METRICS --
        Latency: {incident_context.get('latency', 0)} ms
        Error Rate: {incident_context.get('error_rate', 0) * 100}%
        Health Score: {incident_context.get('health', 1.0)}
        
        -- CONTEXT --
        Active Injection: {incident_context.get('injection_type', 'None')}
        Failed Dependencies: {incident_context.get('failed_dependencies', [])}
        
        Task: Analyze this incident. Predict the business impact and provide a technical recovery plan.
        Output MUST be valid JSON:
        {{
            "root_cause": "Detailed explanation of why this happened",
            "impact_analysis": "What is affected?",
            "suggested_fix": ["Step 1", "Step 2", "Step 3"],
            "risk_level": "High/Medium/Low"
        }}
        """

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            logger.info(f"Triggering AI Analysis for {service}...")
            response = requests.post(self.url, json=payload, timeout=10) # Longer timeout for detailed analysis
            response.raise_for_status()
            
            result = response.json()
            if 'response' in result:
                return json.loads(result['response'])
            return None
        except Exception as e:
            logger.error(f"AI Analysis Failed: {e}")
            return {
                "root_cause": f"AI unavailable: {str(e)}",
                "impact_analysis": "Unknown",
                "suggested_fix": ["Check logs manually", "Verify service health"],
                "risk_level": "Unknown"
            }

    def get_advice(self, service_name, metrics, anomaly_info):
        # Legacy wrapper or simple check
        context = {
            "service": service_name,
            "latency": metrics.get("latency_ms", 0),
            "error_rate": 1.0 if metrics.get("status") != 200 else 0.0,
            "health": 1.0 if metrics.get("status") == 200 else 0.0,
            "reason": "anomaly" if anomaly_info.get("anomaly_flag") else "metric_check"
        }
        return self.analyze_incident(context)
