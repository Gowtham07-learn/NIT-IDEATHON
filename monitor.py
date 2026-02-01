import requests
import time
import pandas as pd
from datetime import datetime
import os
import socket
import ssl

# Add AS MANY websites as you want here
websites = [
    "https://www.uidai.gov.in",
    "https://www.onlinesbi.com",
    "https://www.digilocker.gov.in",
    "https://api.publicapis.org/entries",

    # More government & public services
    "https://www.india.gov.in",
    "https://www.incometax.gov.in",
    "https://www.epfindia.gov.in",
    "https://www.irctc.co.in",
    "https://data.gov.in",
    "https://www.meity.gov.in"
]

CSV_FILE = "dpi_monitor_data.csv"


def check_website(url):
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        latency = round(time.time() - start, 2)

        if response.status_code == 200:
            return "UP", latency, "Healthy"

        if 500 <= response.status_code < 600:
            return "DOWN", latency, "Backend service crashed (5xx)"

        if 400 <= response.status_code < 500:
            return "DOWN", latency, "Blocked / unauthorized / bad request (4xx)"

        return "DOWN", latency, f"Unexpected HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return "DOWN", None, "Network timeout (service overloaded)"

    except requests.exceptions.SSLError:
        return "DOWN", None, "SSL/TLS handshake failure"

    except requests.exceptions.ConnectionError as e:
        msg = str(e).lower()

        if "name or service not known" in msg:
            return "DOWN", None, "DNS resolution failed"

        if "connection refused" in msg:
            return "DOWN", None, "TCP connection refused (service not running)"

        if "network is unreachable" in msg:
            return "DOWN", None, "Network unreachable (routing / ISP issue)"

        return "DOWN", None, "Connection failure (firewall / infra issue)"

    except socket.gaierror:
        return "DOWN", None, "DNS lookup failed"

    except Exception as e:
        return "DOWN", None, f"Unknown failure: {str(e)}"


while True:
    rows = []

    for site in websites:
        status, latency, reason = check_website(site)

        rows.append({
            "Website": site,
            "Status": status,
            "Response_Time": latency,
            "Reason": reason,
            "Timestamp": datetime.now()
        })

    df = pd.DataFrame(rows)

    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

    print("Saved monitoring snapshot at", datetime.now())
    time.sleep(30)
