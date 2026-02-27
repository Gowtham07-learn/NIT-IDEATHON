from ai.prediction.service_predictor import ServicePredictor

class AdvisoryCopilot:
    def __init__(self):
        self.predictor = ServicePredictor()
    
    def analyze(self, df):
        """
        Full analysis pipeline:
        1. Train/Predict Risk
        2. Analyze Dependencies
        3. Generate Advice
        """
        # 1. Prediction
        risks = self.predictor.train_and_predict(df)
        
        # 2. Latest State
        latest_df = df.groupby('service').last().reset_index()
        results = {}
        
        # Helper to get service status from latest_df
        def get_status(svc):
            row = latest_df[latest_df['service'] == svc]
            if row.empty: return 200
            return row.iloc[0]['status']

        for service in ["gateway", "upi", "bank"]:
            prob = risks[service]["prob"]
            level = risks[service]["level"]
            status = get_status(service)
            
            recommendations = []
            cause = "Normal Operation"
            
            # --- DEPENDENCY LOGIC ---
            if service == "gateway":
                if get_status("upi") != 200:
                    cause = "Dependency Failure (UPI PSP)"
                    level = "Critical"
                    recommendations.append("Isolate UPI Route")
                elif get_status("bank") != 200:
                    cause = "Dependency Failure (Issuer Bank)"
                    level = "Critical"
                    recommendations.append("Enable Circuit Breaker for Bank")
            
            # --- DIRECT LOGIC (Overrides dependency if self is broken) ---
            if status != 200:
                cause = "Service Down / Unreachable"
                level = "Critical"
                recommendations.append("Restart Service Immediately")
            elif prob > 0.6:
                cause = "High Latency Detected"
                recommendations.append("Scale Out Replicas")
            
            results[service] = {
                "risk_probability": prob,
                "risk_level": level,
                "root_cause": cause,
                "recommendations": recommendations
            }
            
        return results
