import pandas as pd
from prophet import Prophet
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger("PredictionEngine")
logging.basicConfig(level=logging.INFO)

class MetricsPredictor:
    def __init__(self, service_name):
        self.service_name = service_name
        self.model_latency = Prophet(changepoint_prior_scale=0.05, daily_seasonality=True)
        self.model_errors = Prophet(changepoint_prior_scale=0.05, daily_seasonality=True)
        self.is_trained = False

    def train(self, df):
        """
        Expects a dataframe with ['timestamp', 'latency_ms', 'failure']
        Prophet needs columns 'ds' and 'y'
        """
        if len(df) < 10:
            logger.warning(f"Not enough data to train Prophet for {self.service_name}")
            return False

        try:
            # Prepare Latency Data
            df_lat = df[['timestamp', 'latency_ms']].rename(columns={'timestamp': 'ds', 'latency_ms': 'y'})
            df_lat['ds'] = pd.to_datetime(df_lat['ds'])
            
            # Prepare Error Data
            df_err = df[['timestamp', 'failure']].rename(columns={'timestamp': 'ds', 'failure': 'y'})
            df_err['ds'] = pd.to_datetime(df_err['ds'])

            # Fit Models
            self.model_latency = Prophet(interval_width=0.95)
            self.model_latency.fit(df_lat)
            
            self.model_errors = Prophet(interval_width=0.95)
            self.model_errors.fit(df_err)
            
            self.is_trained = True
            logger.info(f"Prophet models trained for {self.service_name}")
            return True
        except Exception as e:
            logger.error(f"Training failed for {self.service_name}: {e}")
            return False

    def predict(self, horizon_minutes=5):
        if not self.is_trained:
            return None

        try:
            # Future dataframe for horizon
            future_lat = self.model_latency.make_future_dataframe(periods=horizon_minutes, freq='min')
            forecast_lat = self.model_latency.predict(future_lat)
            
            future_err = self.model_errors.make_future_dataframe(periods=horizon_minutes, freq='min')
            forecast_err = self.model_errors.predict(future_err)

            # Get the last predicted value
            pred_lat = max(0, forecast_lat.iloc[-1]['yhat'])
            pred_err = max(0, min(1, forecast_err.iloc[-1]['yhat']))
            
            # Simple risk score: weighted combination of predicted latency and error rate
            # (Heuristic: Latency > 1000ms is high risk, Error > 0.5 is high risk)
            risk_score = (min(pred_lat, 2000) / 2000) * 0.5 + (pred_err * 0.5)

            return {
                "service": self.service_name,
                "predicted_latency": round(pred_lat, 2),
                "predicted_error_rate": round(pred_err, 2),
                "risk_score": round(risk_score, 2),
                "forecast_lat": forecast_lat[['ds', 'yhat']].tail(10).to_dict('records'),
                "forecast_err": forecast_err[['ds', 'yhat']].tail(10).to_dict('records')
            }
        except Exception as e:
            logger.error(f"Prediction failed for {self.service_name}: {e}")
            return None
