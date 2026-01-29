Running the Project Locally

Prerequisites:

Python 3.10 or later

Any OS that supports Python and Streamlit

Internet access for monitored websites

Create and activate a virtual environment:
python -m venv venv
Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate

Install dependencies:
pip install streamlit pandas numpy scikit-learn plotly

Run the monitor:
python monitor.py

Keep this running to continuously collect data.

Run the Streamlit app in a separate terminal:
streamlit run app.py

The dashboard will automatically refresh and display the latest data.

DPI Observability with AI Risk Prediction and Simulated Corrective Actions

This project is a proof-of-concept DPI observability system built using Python and Streamlit.

The goal of this project is to demonstrate how an AI-assisted observability loop can work by continuously monitoring public digital services, predicting potential failures, identifying possible root causes, and suggesting corrective actions. All corrective actions are simulated. There is no real infrastructure control in this project.

Important note:
This project does not perform any real remediation. All actions and improvements shown are simulated purely for demonstration and learning purposes.

What the Project Does

The system performs the following steps:

Monitors a set of public websites and records their status and response time.

Uses a simple and explainable machine learning model to predict future response times.

Assigns a risk level (LOW, MODERATE, HIGH) to each service.

Applies cascading risk using a predefined dependency graph.

Classifies the likely root cause using deterministic, rule-based logic.

Recommends corrective actions based on the identified root cause.

Simulates the impact of these actions on response time and risk level.

Displays all results in a Streamlit dashboard.

Architecture Overview

The architecture is intentionally lightweight and fully local.

Data flow:
monitor.py writes monitoring data to dpi_monitor_data.csv
app.py reads the CSV file and performs AI prediction, risk analysis, simulation, and visualization

There is no external database or cloud dependency.

Component Details

Monitoring (monitor.py)

The monitor.py script:

Periodically checks configured websites

Measures availability and response time

Appends records to dpi_monitor_data.csv

Each record contains:

Timestamp

Website

Status (UP or DOWN)

Response_Time in seconds

The monitor.py file is not modified as part of this PoC.

AI Risk Prediction (app.py)

The app.py script:

Loads monitoring data from dpi_monitor_data.csv

Groups data by service

Uses the most recent N data points to train a Linear Regression model

Predicts the next response time

Calculates the response time trend (slope)

Risk classification is based on clearly defined thresholds:

HIGH RISK if predicted response time or slope exceeds high-risk thresholds

MODERATE RISK if predicted response time or slope exceeds moderate thresholds

LOW RISK otherwise

All thresholds are defined as constants in the source code for transparency.

Cascading Risk Using Dependencies

The system uses a static dependency graph to model downstream impact.

Example dependencies:

UIDAI depends on DigiLocker

OnlineSBI depends on DigiLocker

DigiLocker depends on Public APIs

Cascading rules:

If a parent service is at HIGH risk, dependent services are marked as HIGH RISK (CASCADING)

If a parent service is at MODERATE risk, dependent LOW-risk services are upgraded to MODERATE RISK (CASCADING)

This helps visualize how failures can propagate across services.

Root Cause Classification

For each service with HIGH or MODERATE risk:

If the risk label indicates cascading, the root cause is classified as DOWNSTREAM_DEPENDENCY_FAILURE.

Otherwise, the response time trend is evaluated:

Strong positive trend indicates SERVER_OVERLOAD.

Mild positive trend indicates NETWORK_LATENCY.

Flat or insufficient data results in UNKNOWN.

This classification is rule-based, deterministic, and fully explainable.

Corrective Action Recommendation

Each root cause maps to predefined corrective actions using a policy dictionary.

SERVER_OVERLOAD:

Scale replicas

Enable rate limiting

NETWORK_LATENCY:

Reroute traffic

Check ISP

DOWNSTREAM_DEPENDENCY_FAILURE:

Isolate dependency

Enable fallback

UNKNOWN:

No specific recommendation

No machine learning or reinforcement learning is used for action selection.

Correction Impact Simulation

For services at HIGH or MODERATE risk, the system simulates the impact of applying corrective actions.

Simulation logic:

Starts from predicted next response time or the latest observed value

Applies a simple transformation based on root cause:

SERVER_OVERLOAD: response time reduced by a percentage

NETWORK_LATENCY: response time reduced by a fixed amount

DOWNSTREAM_DEPENDENCY_FAILURE: response time reduced by a fixed amount

UNKNOWN: no change

Using the simulated response time, the system recalculates the simulated risk level using the same thresholds as the original prediction.

All results are clearly marked as simulated.

Streamlit Dashboard

The Streamlit UI displays:

Current service health and availability

Response times and trends

Predicted next response times

AI-based risk levels (including cascading risk)

Alerts for DOWN services

Early warnings for HIGH and MODERATE risk services

Time-series response time charts

AI suggested corrective actions with:

Risk level

Root cause

Recommended actions

Simulated post-fix response time

Simulated post-fix risk level

Clear note indicating simulation only