import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class ServicePredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        # Pre-initialize for services
        for s in ["gateway", "upi", "bank"]:
            self.models[s] = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=42)
            self.scalers[s] = StandardScaler()
            
    def train_and_predict(self, full_df):
        """
        Dynamic Training on the sliding window provided (last ~100 rows).
        Returns risk probability for the LATEST point.
        """
        predictions = {}
        
        if full_df.empty:
            return {s: {"prob": 0, "level": "Unknown"} for s in ["gateway", "upi", "bank"]}

        for service in ["gateway", "upi", "bank"]:
            # Filter for service
            svc_df = full_df[full_df['service'] == service].copy()
            if len(svc_df) < 5:
                predictions[service] = {"prob": 0, "level": "Low (No Data)"}
                continue
                
            # Feature Engineering
            # 1. Latency
            # 2. Status (binary failure)
            # 3. Rolling Mean Latency (Trend)
            svc_df['is_failure'] = svc_df['status'].apply(lambda x: 1 if x != 200 else 0)
            svc_df['rolling_lat'] = svc_df['latency_ms'].rolling(3).mean().fillna(0)
            
            # Prepare X (Features) and y (Target - effectively self-supervised or heuristic here)
            # For this demo, 'High Risk' class = (Latency > 2000ms OR Status != 200)
            svc_df['target'] = ((svc_df['latency_ms'] > 2000) | (svc_df['status'] != 200)).astype(int)
            
            feature_cols = ['latency_ms', 'rolling_lat']
            X = svc_df[feature_cols]
            y = svc_df['target']
            
            # Train on this window
            # If all targets are 0 (healthy), we can't train a binary classifier meaningfully to predict '1'
            if y.sum() > 0 and len(np.unique(y)) > 1:
                self.models[service].fit(X, y)
                
                # Predict on LATEST
                last_row = X.iloc[[-1]]
                prob = self.models[service].predict_proba(last_row)[0][1]
            else:
                # Fallback if mostly healthy or broken: Direct Heuristic
                last_val = svc_df.iloc[-1]
                if last_val['target'] == 1: prob = 1.0 # Currently failing
                else: prob = 0.0
                
            # Classify Level
            if prob > 0.7: level = "High"
            elif prob > 0.4: level = "Medium"
            else: level = "Low"
            
            predictions[service] = {"prob": prob, "level": level}
            
        return predictions
