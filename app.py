import streamlit as st
import pandas as pd
import plotly.express as px
import time
import numpy as np
from sklearn.linear_model import LinearRegression

DEPENDENCIES = {
    "https://www.uidai.gov.in": ["https://www.digilocker.gov.in"],
    "https://www.onlinesbi.com": ["https://www.digilocker.gov.in"],
    "https://www.digilocker.gov.in": ["https://api.publicapis.org/entries"],
}

TREND_WINDOW = 10

HIGH_RISK_RESPONSE_THRESHOLD = 3.0
MODERATE_RISK_RESPONSE_THRESHOLD = 2.0
HIGH_RISK_SLOPE_THRESHOLD = 0.3
MODERATE_RISK_SLOPE_THRESHOLD = 0.15

ROOT_CAUSE_SERVER_OVERLOAD = "SERVER_OVERLOAD"
ROOT_CAUSE_RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
ROOT_CAUSE_NETWORK_LATENCY = "NETWORK_LATENCY"
ROOT_CAUSE_DOWNSTREAM_DEPENDENCY_FAILURE = "DOWNSTREAM_DEPENDENCY_FAILURE"
ROOT_CAUSE_CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
ROOT_CAUSE_UNKNOWN = "UNKNOWN"

INCIDENT_ISOLATED = "ISOLATED"
INCIDENT_CASCADING = "CASCADING"
INCIDENT_UNKNOWN = "UNKNOWN"

CONFIDENCE_THRESHOLD = 0.5

CRS_THRESHOLD = 0.7

SERVICE_CRITICALITY = {
    "https://www.uidai.gov.in": 3,
    "https://www.onlinesbi.com": 3,
    "https://www.digilocker.gov.in": 2,
    "https://api.publicapis.org/entries": 1,
}

CORRECTIVE_POLICY = {
    ROOT_CAUSE_SERVER_OVERLOAD: ["Scale replicas", "Enable rate limiting"],
    ROOT_CAUSE_RESOURCE_EXHAUSTION: ["Increase resource limits", "Optimize resource usage", "Add capacity"],
    ROOT_CAUSE_NETWORK_LATENCY: ["Reroute traffic", "Check ISP", "Review network configuration"],
    ROOT_CAUSE_DOWNSTREAM_DEPENDENCY_FAILURE: ["Isolate dependency", "Enable fallback", "Implement circuit breaker"],
    ROOT_CAUSE_CONFIGURATION_ERROR: ["Review configuration", "Rollback recent changes", "Validate config schema"],
    ROOT_CAUSE_UNKNOWN: ["Collect additional metrics", "Review logs", "Check historical patterns", "Enable detailed monitoring"],
}

SERVER_OVERLOAD_RESPONSE_MULTIPLIER = 0.6
RESOURCE_EXHAUSTION_RESPONSE_MULTIPLIER = 0.65
NETWORK_LATENCY_RESPONSE_REDUCTION = 0.5
DEPENDENCY_FAILURE_RESPONSE_REDUCTION = 0.7
CONFIGURATION_ERROR_RESPONSE_REDUCTION = 0.8

def _compute_response_trend(service_df, window=TREND_WINDOW):
    if len(service_df) < 2:
        return None
    service_df = service_df.sort_values("Timestamp")
    recent = service_df.tail(window)
    if len(recent) < 2:
        return None
    X = np.arange(len(recent)).reshape(-1, 1)
    y = recent["Response_Time"].fillna(5).values.reshape(-1, 1)
    model = LinearRegression()
    model.fit(X, y)
    slope = model.coef_[0][0]
    return float(slope)

def predict_risk(service_df):
    if len(service_df) < 5:
        return "UNKNOWN", None
    service_df = service_df.sort_values("Timestamp")
    recent = service_df.tail(TREND_WINDOW)
    X = np.arange(len(recent)).reshape(-1, 1)
    y = recent["Response_Time"].fillna(5).values.reshape(-1, 1)
    model = LinearRegression()
    model.fit(X, y)
    slope = model.coef_[0][0]
    predicted_next = model.predict([[len(recent)]])[0][0]
    if predicted_next > HIGH_RISK_RESPONSE_THRESHOLD or slope > HIGH_RISK_SLOPE_THRESHOLD:
        return "HIGH RISK", round(predicted_next, 2)
    elif predicted_next > MODERATE_RISK_RESPONSE_THRESHOLD or slope > MODERATE_RISK_SLOPE_THRESHOLD:
        return "MODERATE RISK", round(predicted_next, 2)
    else:
        return "LOW RISK", round(predicted_next, 2)

def apply_cascading_risk(risk_df):
    cascaded = risk_df.copy()
    for parent, children in DEPENDENCIES.items():
        parent_row = cascaded[cascaded["Website"] == parent]
        if len(parent_row) == 0:
            continue
        parent_risk = parent_row.iloc[0]["AI_Risk_Level"]
        if parent_risk == "HIGH RISK":
            for child in children:
                cascaded.loc[cascaded["Website"] == child, "AI_Risk_Level"] = "HIGH RISK (CASCADING)"
        elif parent_risk == "MODERATE RISK":
            for child in children:
                if "LOW" in str(cascaded.loc[cascaded["Website"] == child, "AI_Risk_Level"].values):
                    cascaded.loc[cascaded["Website"] == child, "AI_Risk_Level"] = "MODERATE RISK (CASCADING)"
    return cascaded

def _compute_baseline_latency(service_df, window=TREND_WINDOW * 2):
    if len(service_df) < 5:
        return None
    service_df_sorted = service_df.sort_values("Timestamp")
    historical = service_df_sorted.head(-TREND_WINDOW)
    if len(historical) == 0:
        return None
    response_times = historical["Response_Time"].fillna(5).values
    return float(np.median(response_times))

def _compute_latency_deviation(current_latency, baseline_latency):
    if baseline_latency is None or baseline_latency == 0:
        return None
    if current_latency is None:
        return None
    return (current_latency - baseline_latency) / baseline_latency

def _compute_downstream_impact_ratio(website, risk_df):
    children_at_risk = 0
    total_children = 0
    for parent, children in DEPENDENCIES.items():
        if parent == website:
            total_children = len(children)
            for child in children:
                child_row = risk_df[risk_df["Website"] == child]
                if len(child_row) > 0:
                    child_risk = str(child_row.iloc[0]["AI_Risk_Level"])
                    if "HIGH" in child_risk or "MODERATE" in child_risk:
                        children_at_risk += 1
    if total_children == 0:
        return 0.0, 0, 0
    return children_at_risk / total_children, children_at_risk, total_children

def _compute_cascading_risk_score(website, service_df, risk_df, risk_label, latency_deviation, downstream_impact_ratio):
    label_str = str(risk_label)
    latency_score = 0.0
    if latency_deviation is not None:
        latency_score = min(abs(latency_deviation) / 0.5, 1.0) if latency_deviation != 0 else 0.0
    downstream_score = downstream_impact_ratio
    dependency_count = 0
    for parent, children in DEPENDENCIES.items():
        if parent == website:
            dependency_count = len(children)
    dependency_score = min(dependency_count / 5.0, 1.0)
    criticality = SERVICE_CRITICALITY.get(website, 1)
    criticality_score = (criticality - 1) / 2.0
    crs = (
        0.3 * latency_score +
        0.4 * downstream_score +
        0.1 * dependency_score +
        0.2 * criticality_score
    )
    return min(crs, 1.0)

def detect_incident_type(website, risk_df, risk_label, service_df):
    label_str = str(risk_label)
    if not ("HIGH" in label_str or "MODERATE" in label_str):
        return INCIDENT_UNKNOWN, 0.2
    current_latency = None
    baseline_latency = _compute_baseline_latency(service_df)
    service_row = risk_df[risk_df["Website"] == website]
    if len(service_row) > 0:
        current_latency = service_row.iloc[0].get("Current_Response_Time")
        if current_latency is None:
            current_latency = service_row.iloc[0].get("Predicted_Next_Response_Time")
    latency_deviation = _compute_latency_deviation(current_latency, baseline_latency)
    downstream_impact_ratio, impacted_count, total_downstream = _compute_downstream_impact_ratio(website, risk_df)
    crs = _compute_cascading_risk_score(website, service_df, risk_df, risk_label, latency_deviation, downstream_impact_ratio)
    criticality = SERVICE_CRITICALITY.get(website, 1)
    crs_threshold = CRS_THRESHOLD if criticality >= 2 else 0.8
    has_downstream_impact = downstream_impact_ratio > 0.0 or impacted_count > 0
    if crs >= crs_threshold and has_downstream_impact:
        confidence = min(0.5 + (crs - crs_threshold) * 0.5 + downstream_impact_ratio * 0.3, 0.95)
        return INCIDENT_CASCADING, confidence
    if "CASCADING" in label_str:
        if crs >= 0.6:
            return INCIDENT_CASCADING, min(0.85, 0.6 + crs * 0.25)
        elif has_downstream_impact:
            return INCIDENT_CASCADING, 0.55
        else:
            return INCIDENT_ISOLATED, 0.5
    if has_downstream_impact and crs >= 0.5:
        confidence = 0.4 + (crs - 0.5) * 0.4
        if confidence >= CONFIDENCE_THRESHOLD:
            return INCIDENT_CASCADING, confidence
    if "HIGH" in label_str or "MODERATE" in label_str:
        confidence = 0.6 if "HIGH" in label_str else 0.5
        return INCIDENT_ISOLATED, confidence
    return INCIDENT_UNKNOWN, 0.3

def classify_root_cause(website, service_df, risk_label, risk_df, incident_type, incident_confidence):
    if incident_confidence < CONFIDENCE_THRESHOLD:
        return ROOT_CAUSE_UNKNOWN, 0.2
    label_str = str(risk_label)
    if not ("HIGH" in label_str or "MODERATE" in label_str):
        return ROOT_CAUSE_UNKNOWN, 0.2
    if incident_type == INCIDENT_CASCADING and incident_confidence >= 0.7:
        root_cause_confidence = min(incident_confidence * 0.95, 0.9)
        return ROOT_CAUSE_DOWNSTREAM_DEPENDENCY_FAILURE, root_cause_confidence
    if incident_type == INCIDENT_CASCADING:
        return ROOT_CAUSE_DOWNSTREAM_DEPENDENCY_FAILURE, min(incident_confidence * 0.8, 0.6)
    slope = _compute_response_trend(service_df)
    if slope is None:
        return ROOT_CAUSE_UNKNOWN, 0.2
    service_df_sorted = service_df.sort_values("Timestamp")
    recent = service_df_sorted.tail(TREND_WINDOW)
    response_times = recent["Response_Time"].fillna(5).values
    if len(response_times) < 5:
        return ROOT_CAUSE_UNKNOWN, 0.2
    mean_response = np.mean(response_times)
    std_response = np.std(response_times)
    max_response = np.max(response_times)
    latest_response = response_times[-1]
    if std_response > 0:
        spike_ratio = (max_response - mean_response) / std_response
        if spike_ratio > 2.5 and slope < MODERATE_RISK_SLOPE_THRESHOLD:
            return ROOT_CAUSE_CONFIGURATION_ERROR, 0.7
        elif spike_ratio > 2.0 and slope < MODERATE_RISK_SLOPE_THRESHOLD:
            return ROOT_CAUSE_CONFIGURATION_ERROR, 0.55
    if slope > HIGH_RISK_SLOPE_THRESHOLD * 1.5:
        return ROOT_CAUSE_RESOURCE_EXHAUSTION, 0.75
    elif slope > HIGH_RISK_SLOPE_THRESHOLD:
        return ROOT_CAUSE_SERVER_OVERLOAD, 0.7
    elif slope > MODERATE_RISK_SLOPE_THRESHOLD:
        return ROOT_CAUSE_NETWORK_LATENCY, 0.6
    elif slope > 0:
        if latest_response and latest_response > HIGH_RISK_RESPONSE_THRESHOLD:
            return ROOT_CAUSE_SERVER_OVERLOAD, 0.5
        elif latest_response and latest_response > MODERATE_RISK_RESPONSE_THRESHOLD:
            return ROOT_CAUSE_NETWORK_LATENCY, 0.5
        else:
            return ROOT_CAUSE_UNKNOWN, 0.3
    else:
        if latest_response and latest_response > HIGH_RISK_RESPONSE_THRESHOLD:
            return ROOT_CAUSE_UNKNOWN, 0.4
        else:
            return ROOT_CAUSE_UNKNOWN, 0.3

def recommend_corrective_actions(root_cause, confidence):
    if root_cause == ROOT_CAUSE_UNKNOWN or confidence < CONFIDENCE_THRESHOLD:
        return CORRECTIVE_POLICY[ROOT_CAUSE_UNKNOWN]
    return CORRECTIVE_POLICY.get(root_cause, CORRECTIVE_POLICY[ROOT_CAUSE_UNKNOWN])

def simulate_correction_effect(current_response, predicted_response, root_cause, confidence):
    if root_cause == ROOT_CAUSE_UNKNOWN or confidence < CONFIDENCE_THRESHOLD:
        return None, "UNKNOWN (No simulation - insufficient confidence)"
    base = predicted_response if predicted_response is not None else current_response
    if base is None:
        return None, "UNKNOWN"
    simulated = float(base)
    if root_cause == ROOT_CAUSE_SERVER_OVERLOAD:
        simulated *= SERVER_OVERLOAD_RESPONSE_MULTIPLIER
    elif root_cause == ROOT_CAUSE_RESOURCE_EXHAUSTION:
        simulated *= RESOURCE_EXHAUSTION_RESPONSE_MULTIPLIER
    elif root_cause == ROOT_CAUSE_NETWORK_LATENCY:
        simulated = max(simulated - NETWORK_LATENCY_RESPONSE_REDUCTION, 0.0)
    elif root_cause == ROOT_CAUSE_DOWNSTREAM_DEPENDENCY_FAILURE:
        simulated = max(simulated - DEPENDENCY_FAILURE_RESPONSE_REDUCTION, 0.0)
    elif root_cause == ROOT_CAUSE_CONFIGURATION_ERROR:
        simulated = max(simulated - CONFIGURATION_ERROR_RESPONSE_REDUCTION, 0.0)
    if simulated > HIGH_RISK_RESPONSE_THRESHOLD:
        sim_risk = "HIGH RISK"
    elif simulated > MODERATE_RISK_RESPONSE_THRESHOLD:
        sim_risk = "MODERATE RISK"
    else:
        sim_risk = "LOW RISK"
    return round(simulated, 2), sim_risk

st.set_page_config(page_title="DPI Observability", layout="wide")
st.title("DPI Services Observability Dashboard")
df = pd.read_csv("dpi_monitor_data.csv")
df["Timestamp"] = pd.to_datetime(df["Timestamp"])
latest = df.sort_values("Timestamp").groupby("Website").tail(1)
st.subheader("Current Service Health + AI Risk Prediction")
risk_rows = []
for site in df["Website"].unique():
    site_df = df[df["Website"] == site]
    latest_row = site_df.sort_values("Timestamp").iloc[-1]
    risk, predicted = predict_risk(site_df)
    risk_rows.append(
        {
            "Website": site,
            "Status": latest_row["Status"],
            "Current_Response_Time": latest_row["Response_Time"],
            "Predicted_Next_Response_Time": predicted,
            "AI_Risk_Level": risk,
        }
    )
risk_df = pd.DataFrame(risk_rows)
risk_df = apply_cascading_risk(risk_df)
st.dataframe(risk_df, width="stretch")
st.subheader("Alerts")
for _, row in latest.iterrows():
    if row["Status"] != "UP":
        st.error(f"{row['Website']} is DOWN")
    elif row["Response_Time"] is not None and row["Response_Time"] > 2:
        st.warning(f"{row['Website']} is SLOW ({row['Response_Time']} sec)")
st.subheader("AI Early Warning System")
for _, row in risk_df.iterrows():
    if row["AI_Risk_Level"] == "HIGH RISK":
        st.error(f"{row['Website']} predicted to FAIL soon! (Predicted {row['Predicted_Next_Response_Time']} sec)")
    elif row["AI_Risk_Level"] == "MODERATE RISK":
        st.warning(f"{row['Website']} under stress (Predicted {row['Predicted_Next_Response_Time']} sec)")
st.subheader("AI Suggested Corrective Actions (Simulated)")
recommendation_rows = []
for _, row in risk_df.iterrows():
    ai_risk = str(row["AI_Risk_Level"])
    if not ("HIGH" in ai_risk or "MODERATE" in ai_risk):
        continue
    website = row["Website"]
    service_df = df[df["Website"] == website]
    incident_type, incident_confidence = detect_incident_type(website, risk_df, ai_risk, service_df)
    root_cause, root_cause_confidence = classify_root_cause(website, service_df, ai_risk, risk_df, incident_type, incident_confidence)
    if root_cause_confidence < CONFIDENCE_THRESHOLD:
        root_cause = ROOT_CAUSE_UNKNOWN
        root_cause_confidence = 0.3
    actions = recommend_corrective_actions(root_cause, root_cause_confidence)
    simulated_response, simulated_risk = simulate_correction_effect(current_response=row["Current_Response_Time"], predicted_response=row["Predicted_Next_Response_Time"], root_cause=root_cause, confidence=root_cause_confidence)
    recommendation_rows.append(
        {
            "Website": website,
            "Incident_Type": incident_type,
            "Root_Cause": root_cause,
            "Risk_Level": ai_risk,
            "Prediction_Confidence": f"{root_cause_confidence:.2f}",
            "Recommended_Actions": ", ".join(actions) if actions else "No clear action (UNKNOWN)",
            "Simulated_Post_Fix_Response_Time": simulated_response if simulated_response is not None else "N/A (UNKNOWN)",
            "Simulated_Post_Fix_Risk_Level": simulated_risk,
            "Note": "SIMULATED FIX – no real infrastructure changes performed" if simulated_response is not None else "SIMULATED FIX – No simulation (insufficient confidence or UNKNOWN root cause)",
        }
    )
if len(recommendation_rows) == 0:
    st.info("No HIGH or MODERATE risk services at the moment.")
else:
    recommendation_df = pd.DataFrame(recommendation_rows)
    column_order = ["Website", "Incident_Type", "Root_Cause", "Risk_Level", "Prediction_Confidence", "Recommended_Actions", "Simulated_Post_Fix_Response_Time", "Simulated_Post_Fix_Risk_Level", "Note"]
    recommendation_df = recommendation_df[column_order]
    st.dataframe(recommendation_df, width="stretch")
st.subheader("Response Time Trend")
fig = px.line(df, x="Timestamp", y="Response_Time", color="Website", markers=True)
st.plotly_chart(fig, use_container_width=True)
st.caption("Auto refresh every 30 seconds")
time.sleep(30)
st.rerun()
