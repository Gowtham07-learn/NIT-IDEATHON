import streamlit as st
import sys
import os

# Fix path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="DPI Incident Monitor", layout="wide", page_icon="🕵️")

st.sidebar.title("🕵️ Forensic Navigator")
st.sidebar.success("Select a module below.")

st.title("🛡️ DPI Forensic & Incident Platform")
st.markdown("""
Welcome to the real-time forensic analysis module for Digital Public Infrastructure. 
This platform provides deep insights into system failures, root cause analysis, and AI-driven remediation.

### 🚀 Getting Started
Use the sidebar to navigate between:
1. **Dashboard**: Real-time service health and latency monitoring.
2. **Incident Timeline**: Forensic event logs, RCA, and dependency impact graphs.

---
**System Status:** Running on Local AI (Mistral)
""")

# Note: Streamlit multi-page handles the sidebar links based on the files in pages/
