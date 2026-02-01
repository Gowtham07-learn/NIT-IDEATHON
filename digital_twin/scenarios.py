# digital_twin/scenarios.py

SCENARIOS = {
    "UIDAI_OUTAGE": {
        "trigger": "https://www.uidai.gov.in",
        "effect": "TOTAL_FAILURE",
        "description": "Aadhaar authentication service outage"
    },

    "TRAFFIC_SURGE_IRCTC": {
        "trigger": "https://www.irctc.co.in",
        "effect": "LATENCY_SPIKE",
        "latency_multiplier": 3,
        "description": "Festival booking traffic surge"
    },

    "BANKING_NETWORK_FAILURE": {
        "trigger": "https://www.onlinesbi.com",
        "effect": "NETWORK_FAILURE",
        "description": "Banking gateway unreachable"
    }
}
