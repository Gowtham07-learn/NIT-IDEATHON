import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import sys
import os

# Try to import extra components, handle missing
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

try:
    from streamlit_agraph import agraph, Node, Edge, Config
except ImportError:
    agraph = None

# Fix path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# --- CONFIG ---
BACKEND_URL = "http://localhost:8010"
OLLAMA_URL = "http://localhost:11434/api/generate"

st.title("🕵️ Forensic Incident Timeline & RCA")

# A) Auto Refresh
if st_autorefresh:
    st_autorefresh(interval=5000, key="timelinecounter")
else:
    st.info("💡 Tip: Install `streamlit-autorefresh` for smoother updates.")

# Helper to fetch data
def fetch_json(endpoint, params=None):
    try:
        resp = requests.get(f"{BACKEND_URL}/{endpoint}", params=params, timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except:
        return None
    return None

# B) Timeline Table & D) Filters
st.subheader("📜 Event Timeline")
col1, col2, col3 = st.columns(3)

with col1:
    svc_filter = st.selectbox("Service", ["All", "Gateway", "UPI", "Bank"])
with col2:
    sev_filter = st.selectbox("Severity", ["All", "Info", "Warning", "Critical"])
with col3:
    limit = st.slider("Max Events", 10, 100, 50)

# Fetch timeline
params = {}
if svc_filter != "All": params["service"] = svc_filter.lower()
if sev_filter != "All": params["severity"] = sev_filter.lower()
params["limit"] = limit

events = fetch_json("timeline", params)

if events:
    df_events = pd.DataFrame(events)
    # Reorder columns for better view
    cols = ['timestamp', 'service', 'event_type', 'severity', 'message']
    df_display = df_events[cols] if all(c in df_events.columns for c in cols) else df_events
    
    # C) Severity Color Tags (using dataframe styling)
    def style_severity(val):
        color = 'white'
        if val == 'critical': color = 'red'
        elif val == 'warning': color = 'orange'
        elif val == 'info': color = 'green'
        return f'color: {color}'

    st.dataframe(df_display.style.applymap(style_severity, subset=['severity']), use_container_width=True)
else:
    st.info("No events recorded yet.")

# E) Live Metrics Graph
st.subheader("📈 Live Metrics Snapshot")
metrics = fetch_json("metrics/live")
if metrics:
    df_metrics = pd.DataFrame(metrics)
    if not df_metrics.empty:
        # Plot latency per service
        st.line_chart(df_metrics.pivot(columns='service', values='latency_ms'), height=250)
else:
    st.caption("Waiting for metrics...")

# F) Dependency Impact Graph
st.subheader("🔗 Dependency Impact & RCA")
rca_col, graph_col = st.columns([1, 1])

with graph_col:
    st.write("**System Topology**")
    if agraph:
        # Highlight failed services red
        # We check latest events for failures
        failed_svcs = []
        if events:
            failed_svcs = [e["service"].lower() for e in events[:5] if e["severity"] in ["warning", "critical"]]
        
        nodes = [
            Node(id="Gateway", label="Gateway", size=400, color="red" if "gateway" in failed_svcs else "green"),
            Node(id="UPI", label="UPI PSP", size=400, color="red" if "upi_psp" in failed_svcs or "upi" in failed_svcs else "green"),
            Node(id="Bank", label="Issuer Bank", size=400, color="red" if "issuer_bank" in failed_svcs or "bank" in failed_svcs else "green"),
        ]
        edges = [
            Edge(source="Gateway", target="UPI", label="HTTP/POST"),
            Edge(source="UPI", target="Bank", label="HTTP/POST"),
        ]
        config = Config(width=400, height=300, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6", staticGraph=False)
        agraph(nodes=nodes, edges=edges, config=config)
    else:
        st.info("Install `streamlit-agraph` for interactive dependency visualization.")
        # Fallback text graph
        st.code("Gateway -> UPI PSP -> Issuer Bank")

# G) RCA Panel
with rca_col:
    st.write("**Root Cause Analysis**")
    rca_data = fetch_json("rca")
    if rca_data and "root_service" in rca_data:
        with st.container(border=True):
            st.error(f"**Root Cause:** {rca_data['root_service']}")
            st.warning(f"**Cascade Path:** {' -> '.join(rca_data['cascade_path'])}")
            st.write(f"**Confidence:** {rca_data['confidence']*100:.0f}%")
            st.info(f"**Explanation:** {rca_data['explanation']}")
            
            # H) AI Prediction + Solution (Ollama) - AUTOMATED
            current_rca_key = f"{rca_data['root_service']}_{rca_data['explanation']}"
            
            if "last_rca_key" not in st.session_state:
                st.session_state.last_rca_key = ""
            if "ai_advice_cache" not in st.session_state:
                st.session_state.ai_advice_cache = ""

            if current_rca_key != st.session_state.last_rca_key:
                st.session_state.last_rca_key = current_rca_key
                prompt = f"System Incident at {rca_data['root_service']}. Path: {rca_data['cascade_path']}. {rca_data['explanation']} Predict risk and give a technical solution."
                try:
                    with st.spinner("🤖 Mistral is analyzing the incident..."):
                        # Get Ollama port from env or default
                        ollama_port = os.getenv("OLLAMA_PORT", "11434")
                        resp = requests.post(f"http://localhost:{ollama_port}/api/generate", json={
                            "model": "mistral",
                            "prompt": prompt,
                            "stream": False
                        }, timeout=30)
                        if resp.status_code == 200:
                            st.session_state.ai_advice_cache = resp.json()["response"]
                        else:
                            st.session_state.ai_advice_cache = "⚠️ Could not connect to Ollama for automated advice."
                except Exception as e:
                    st.session_state.ai_advice_cache = f"⚠️ Ollama Error: {e}"

            if st.session_state.ai_advice_cache:
                st.write("**Automated AI Remediation:**")
                st.success(st.session_state.ai_advice_cache)
    else:
        st.success("✅ System Health is Optimal. No active RCA needed.")

# Wait and refresh fallback
if not st_autorefresh:
    time.sleep(5)
    st.rerun()
