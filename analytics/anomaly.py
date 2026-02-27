from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("AnomalyDetection")

class AnomalyDetector:
    def __init__(self):
        # contamination is the proportion of outliers in the data set. 
        # 0.05 means we expect 5% of data points to be anomalous in 'normal' conditions.
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_fitted = False

    def fit(self, df):
        """
        Fits the model on historical metrics. 
        Features: latency_ms, failure (binary)
        """
        if len(df) < 50:
            logger.warning("Not enough data to train Anomaly Detector (need >50 rows)")
            return False

        try:
            X = df[['latency_ms', 'failure']]
            self.model.fit(X)
            self.is_fitted = True
            logger.info("Anomaly Detector fitted successfully")
            return True
        except Exception as e:
            logger.error(f"Fitting anomaly detector failed: {e}")
            return False

    def detect(self, latest_metrics):
        """
        Input: list of dicts or single dict with {'latency_ms', 'failure'}
        Returns list of results: {'anomaly_flag', 'anomaly_score'}
        """
        if not self.is_fitted:
            return {"anomaly_flag": False, "anomaly_score": 0}

        try:
            if isinstance(latest_metrics, dict):
                X = pd.DataFrame([latest_metrics])[['latency_ms', 'failure']]
            else:
                X = pd.DataFrame(latest_metrics)[['latency_ms', 'failure']]

            # decision_function returns the anomaly score (lower is more anomalous)
            # predict returns -1 for anomalies, 1 for normal
            scores = self.model.decision_function(X)
            preds = self.model.predict(X)

            # Convert to human-readable
            results = []
            for score, pred in zip(scores, preds):
                results.append({
                    "anomaly_flag": bool(pred == -1),
                    "anomaly_score": round(float(score), 4)
                })
            
            return results[0] if isinstance(latest_metrics, dict) else results
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {"anomaly_flag": False, "anomaly_score": 0}
