import streamlit as st
import pandas as pd
import plotly.express as px
import time
import numpy as np
from sklearn.linear_model import LinearRegression

# Dependency mapping (can expand later)
DEPENDENCIES = {
    "https://www.uidai.gov.in": ["https://www.digilocker.gov.in"],
    "https://www.onlinesbi.com": ["https://www.digilocker.gov.in"],
    "https://www.digilocker.gov.in": ["https://api.publicapis.org/entries"]
}

# ---------------- AI RISK PREDICTION ---------------- #

def predict_risk(service_df):
    if len(service_df) < 5:
        return "UNKNOWN", None

    service_df = service_df.sort_values("Timestamp")
    recent = service_df.tail(10)

    X = np.arange(len(recent)).reshape(-1, 1)
    y = recent["Response_Time"].fillna(5).values.reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0][0]
    predicted_next = model.predict([[len(recent)]])[0][0]

    if predicted_next > 3 or slope > 0.3:
        return "HIGH RISK", round(predicted_next, 2)
    elif predicted_next > 2 or slope > 0.15:
        return "MODERATE RISK", round(predicted_next, 2)
    else:
        return "LOW RISK", round(predicted_next, 2)

# ---------------- CASCADING RISK ---------------- #

def apply_cascading_risk(risk_df):
    cascaded = risk_df.copy()

    for parent, children in DEPENDENCIES.items():
        parent_row = cascaded[cascaded["Website"] == parent]

        if parent_row.empty:
            continue

        parent_risk = parent_row.iloc[0]["AI_Risk_Level"]

        if parent_risk == "HIGH RISK":
            for child in children:
                cascaded.loc[
                    cascaded["Website"] == child,
                    "AI_Risk_Level"
                ] = "HIGH RISK (CASCADING)"

        elif parent_risk == "MODERATE RISK":
            for child in children:
                if "LOW" in str(
                    cascaded.loc[
                        cascaded["Website"] == child,
                        "AI_Risk_Level"
                    ].values
                ):
                    cascaded.loc[
                        cascaded["Website"] == child,
                        "AI_Risk_Level"
                    ] = "MODERATE RISK (CASCADING)"

    return cascaded

# ---------------- STREAMLIT UI ---------------- #

st.set_page_config(
    page_title="DPI Observability",
    layout="wide"
)

st.title("DPI Services Observability Dashboard")

# Read CSV with Reason column
df = pd.read_csv(
    "dpi_monitor_data.csv",
    header=None,
    names=["Website", "Status", "Response_Time", "Reason", "Timestamp"]
)

df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Latest status per website
latest = df.sort_values("Timestamp").groupby("Website").tail(1)

# ---------------- CURRENT HEALTH ---------------- #

st.subheader("Current Service Health + AI Risk Prediction")

risk_rows = []

for site in df["Website"].unique():
    site_df = df[df["Website"] == site].copy()
    latest_row = site_df.sort_values("Timestamp").iloc[-1]

    risk, predicted = predict_risk(site_df)

    risk_rows.append({
        "Website": site,
        "Status": latest_row["Status"],
        "Current_Response_Time": latest_row["Response_Time"],
        "Predicted_Next_Response_Time": predicted,
        "AI_Risk_Level": risk
    })

risk_df = pd.DataFrame(risk_rows)
risk_df = apply_cascading_risk(risk_df)

st.dataframe(risk_df, use_container_width=True)

# ---------------- ALERTS ---------------- #

st.subheader("Live Alerts")

for _, row in latest.iterrows():
    if row["Status"] != "UP":
        st.error(
            f"{row['Website']} is DOWN\n"
            f"Reason: {row['Reason']}"
        )
    elif row["Response_Time"] is not None and row["Response_Time"] > 2:
        st.warning(
            f"{row['Website']} is SLOW ({row['Response_Time']} sec)"
        )

# ---------------- AI EARLY WARNING ---------------- #

st.subheader("AI Early Warning System")

for _, row in risk_df.iterrows():
    reason_row = latest[latest["Website"] == row["Website"]]
    reason_text = (
        reason_row.iloc[0]["Reason"]
        if not reason_row.empty
        else "No anomaly detected"
    )

    if "HIGH" in row["AI_Risk_Level"]:
        st.error(
            f"{row['Website']} predicted to FAIL soon!\n"
            f"Reason: {reason_text}\n"
            f"Predicted Response Time: {row['Predicted_Next_Response_Time']} sec"
        )

    elif "MODERATE" in row["AI_Risk_Level"]:
        st.warning(
            f"{row['Website']} under stress\n"
            f"Reason: {reason_text}\n"
            f"Predicted Response Time: {row['Predicted_Next_Response_Time']} sec"
        )

# ---------------- RESPONSE TIME GRAPH ---------------- #

st.subheader("Response Time Trend (All Services)")

fig = px.line(
    df,
    x="Timestamp",
    y="Response_Time",
    color="Website",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ---------------- AUTO REFRESH ---------------- #

st.caption("Auto refresh every 30 seconds")
time.sleep(30)
st.rerun()
