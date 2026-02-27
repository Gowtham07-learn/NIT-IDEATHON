import streamlit as st
import pandas as pd
import time
import requests
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

# Fix path to allow importing from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import local AI stack
from prediction_engine.predictor import MetricsPredictor
from analytics.anomaly import AnomalyDetector
from copilot.advisor import AIAdvisor

# Page Config
st.set_page_config(page_title="Local AI DPI Observability", layout="wide", page_icon="🤖")

# Cache AI Components
@st.cache_resource
def init_ai():
    return {
        "predictors": {s: MetricsPredictor(s) for s in ["gateway", "upi", "bank"]},
        "anomaly": AnomalyDetector(),
        "advisor": AIAdvisor()
    }

ai_stack = init_ai()

# Constants
DATA_FILE = "data/telemetry_realtime.csv"
REFRESH_RATE = 5

def load_data():
    if not os.path.exists(DATA_FILE): 
        print(f"DEBUG Dashboard: {DATA_FILE} missing")
        return pd.DataFrame()
    try:
        df = pd.read_csv(DATA_FILE)
        if df.empty:
            print("DEBUG Dashboard: CSV is empty")
            return pd.DataFrame()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        print(f"DEBUG Dashboard: Error loading CSV: {e}")
        return pd.DataFrame()

def set_fault(port, latency=0, error=False):
    try:
        url = f"http://localhost:{port}/admin/fault"
        requests.post(url, params={"latency": latency, "error": error}, timeout=2)
        st.toast(f"✅ Fault Sent to port {port}")
    except Exception as e:
        st.error(f"Failed: {e}")

# --- HEADER ---
st.title("🤖 Local AI-Driven DPI Observability")
st.markdown("### 100% Offline • Predictive Analytics • AI Advisory (Mistral)")

# Load Data
df = load_data()
if df.empty:
    st.warning("⏳ Waiting for metrics... Ensure 'run_platform.bat' is active.")
    st.stop()

# --- PROCESSING ---
# 1. Anomaly Detection (Fit if enough data)
if len(df) > 50:
    ai_stack["anomaly"].fit(df)

# 2. Per-Service Analysis
results = {}
for svc in ["gateway", "upi", "bank"]:
    svc_df = df[df['service'] == svc].tail(50)
    latest = svc_df.iloc[-1].to_dict() if not svc_df.empty else {}
    
    # Anomaly
    ano_res = ai_stack["anomaly"].detect(latest) if latest else {"anomaly_flag": False, "anomaly_score": 0}
    
    # Prediction (Prophet)
    if len(svc_df) >= 20:
        ai_stack["predictors"][svc].train(svc_df)
        pred_res = ai_stack["predictors"][svc].predict()
    else:
        pred_res = {"risk_score": 0, "predicted_latency": 0, "predicted_error_rate": 0}
        
    # Advice (Ollama)
    # Removing blocking call from here. Automation happens below in UI section via Gateway API.
    results[svc] = {
        "latest": latest,
        "anomaly": ano_res,
        "prediction": pred_res,
    }

# --- UI LAYOUT ---

# Row 1: Fault Injection Panel
with st.expander("🛠️ Fault Injection Panel (Update Real-time)", expanded=True):
    cols = st.columns(3)
    s_map = [("Gateway", 8000), ("UPI PSP", 8001), ("Issuer Bank", 8002)]
    for i, (name, port) in enumerate(s_map):
        with cols[i]:
            st.write(f"**{name}**")
            c1, c2, c3 = st.columns(3)
            if c1.button("Reset", key=f"r_{port}"): set_fault(port, 0, False)
            if c2.button("Latency (3s)", key=f"l_{port}"): set_fault(port, 3000, False)
            if c3.button("Error (503)", key=f"e_{port}"): set_fault(port, 0, True)

# Row 2: Live Graphs
st.subheader("📈 Real-Time Latency Trends")
try:
    plt_df = df.pivot(index='timestamp', columns='service', values='latency_ms').tail(50)
    plt_df = plt_df.fillna(0) # Prevent Infinity errors in charting
    
    fig = px.line(plt_df, labels={"value": "Latency (ms)", "timestamp": "Time"},
                  template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.info("📊 Waiting for metrics to populate graphs...")

@st.cache_data(ttl=60) # Only refresh analysis every 1m or if data changes significantly
def get_dynamic_advice(svc_name, data):
    try:
        resp = requests.post("http://localhost:8000/ai/advise", json=data, timeout=30)
        if resp.status_code == 200:
            return resp.json()["solution"]
    except:
        return None
    return None

# Row 3: Service Health & AI Cards
st.subheader("🧠 Per-Service Local AI Analysis")
card_cols = st.columns(3)
for i, svc in enumerate(["gateway", "upi", "bank"]):
    res = results[svc]
    with card_cols[i]:
        with st.container(border=True):
            # Header
            status_color = "green"
            if res["anomaly"]["anomaly_flag"]: status_color = "red"
            elif res["prediction"]["risk_score"] > 0.4: status_color = "orange"
            
            st.markdown(f"#### :{status_color}[{svc.upper()}]")
            
            # Metrics
            st.write(f"Latency: {res['latest'].get('latency_ms', 0):.1f}ms")
            
            # Anomaly
            if res["anomaly"]["anomaly_flag"]:
                st.error(f"🚨 Anomaly Detected! (Score: {res['anomaly']['anomaly_score']})")
            
            # Prediction
            ris_val = res["prediction"].get("risk_score", 0) * 100
            st.write(f"**Forecast Risk: {ris_val:.0f}%**")
            st.progress(ris_val/100)
            st.caption(f"Next 5m: {res['prediction'].get('predicted_latency',0)}ms avg")

            # Advice (Local LLM via Gateway) - AUTOMATED
            st.divider()
            
            # Fetch latest insight from backend
            try:
                insight_resp = requests.get(f"http://localhost:8010/ai/insight?service={svc}", timeout=1)
                if insight_resp.status_code == 200:
                    insight_data = insight_resp.json()
                    if "analysis" in insight_data:
                        analysis = insight_data["analysis"]
                        st.write("**🤖 AI Incident Analysis:**")
                        with st.expander("See details", expanded=False):
                            st.markdown(f"**Root Cause:** {analysis.get('root_cause', 'N/A')}")
                            st.markdown(f"**Impact:** {analysis.get('impact_analysis', 'N/A')}")
                            st.markdown("**Suggested Fixes:**")
                            for fix in analysis.get('suggested_fix', []):
                                st.markdown(f"- {fix}")
                    else:
                         if res["anomaly"]["anomaly_flag"] or ris_val > 50:
                            st.caption("🤖 AI is analyzing...")
                         else:
                            st.caption("✅ System healthy.")
                else:
                    st.caption("⚠️ AI Service unreachable")
            except:
                st.caption("⚠️ AI Service unreachable")

# Dependency Logic (Footer)
st.divider()
st.subheader("🔗 Dependency Monitor & Topology")

# Generate Graphviz topology
def get_node_color(svc_name):
    res = results.get(svc_name, {})
    latest = res.get("latest", {})
    anomaly = res.get("anomaly", {})
    
    if anomaly.get("anomaly_flag"):
        return "red"
    # Assuming 'status' is present and 200 for healthy. 
    # If no data (latest is empty), defaults to 'gray'
    if latest.get('status') == 200:
        return "green"
    return "gray"

c_gw = get_node_color("gateway")
c_upi = get_node_color("upi")
c_bank = get_node_color("bank")

dot = f"""
digraph G {{
    rankdir=LR;
    bgcolor="transparent";
    node [shape=box, style=filled, fontname="Arial", fontsize=12, fontcolor="white", color="none"];
    edge [fontname="Arial", fontsize=10, color="#888888", fontcolor="#888888"];
    
    Gateway [label="Gateway", fillcolor="{c_gw}"];
    UPI [label="UPI PSP", fillcolor="{c_upi}"];
    Bank [label="Issuer Bank", fillcolor="{c_bank}"];
    
    Gateway -> UPI [label="HTTP/POST"];
    UPI -> Bank [label="HTTP/POST"];
    
    {{rank=same; UPI; Bank;}}
}}
"""
st.graphviz_chart(dot)

# Summary Alerts
gw_res = results["gateway"]["latest"]
upi_res = results["upi"]["latest"]
bank_res = results["bank"]["latest"]

issues = []
if bank_res.get('status', 200) != 200:
    issues.append("Issuer Bank is failing")
if upi_res.get('status', 200) != 200:
    issues.append("UPI PSP is failing")
if gw_res.get('latency_ms', 0) > 1000:
    issues.append("High Gateway latency")

if not issues:
    st.success("✅ Topology health check: Normal Service Operations.")
else:
    st.warning(f"⚠️ Issues detected: {', '.join(issues)}")

# --- AUTO REFRESH ---
time.sleep(REFRESH_RATE)
st.rerun()
