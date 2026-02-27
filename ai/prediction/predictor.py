import os
import logging
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DPI_Gemini_Predictor")

class DPIPredictor:
    def __init__(self, api_key=None):
        # Prefer passed key, then env var
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            self.configure(self.api_key)
        else:
            logger.warning("No Gemini API Key found. AI features will be disabled.")
            
    def configure(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        # Using gemini-2.0-flash as requested (or fallback to compatible latest)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def predict(self, latest_data):
        """
        Uses Gemini to analyze telemetry and predict failure.
        Output: (prob, risk_level)
        """
        if not self.model:
            return 0.0, "AI Not Configured"
            
        prompt = f"""
        You are an AIOps expert monitoring a Digital Public Infrastructure.
        Analyze the following telemetry snapshot:
        
        Gateway Latency: {latest_data.get('gateway_latency_sum', 0)}s
        UPI Latency: {latest_data.get('upi_latency_sum', 0)}s
        Bank Latency: {latest_data.get('bank_latency_sum', 0)}s
        Gateway Status: {'UP' if latest_data.get('gateway_up') else 'DOWN'}
        UPI Status: {'UP' if latest_data.get('upi_up') else 'DOWN'}
        Bank Status: {'UP' if latest_data.get('bank_up') else 'DOWN'}
        
        Task:
        1. Predict the probability (0.0 to 1.0) of a major system outage in the next 15 minutes.
        2. Assign a Risk Level (Low/Medium/High).
        3. Explain the root cause briefly.
        
        Return ONLY valid JSON:
        {{
            "probability": 0.45,
            "risk_level": "Medium",
            "reason": "..."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Find the first { and last } to extract JSON strictly
            text = response.text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                data = json.loads(json_str)
            else:
                logger.error(f"No JSON found in response: {text}")
                return 0.0, "AI Error"
                
            return float(data.get("probability", 0)), data.get("risk_level", "Unknown")
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return 0.0, "AI Error"

    def get_detailed_analysis(self, latest_data):
        """Directly returns full analysis for the Copilot."""
        if not self.model:
            return None
            
        prob, level = self.predict(latest_data)
        
        # Simple fallback/mock if API fails or for speed but ideally we parse the JSON logic above
        # For simplicity, we just returned the tuple above, but let's improve the Copilot flow to reuse this.
        return {
            "risk_probability": prob,
            "risk_level": level
        }
