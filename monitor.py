import requests
import time
import pandas as pd
from datetime import datetime
import os

websites = [
    "https://www.uidai.gov.in",
    "https://www.onlinesbi.com",
    "https://www.digilocker.gov.in",
    "https://api.publicapis.org/entries"
]

CSV_FILE = "dpi_monitor_data.csv"

def check_website(url):
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        latency = round(time.time() - start, 2)
        status = "UP" if response.status_code == 200 else "DOWN"
    except:
        latency = None
        status = "DOWN"
    return status, latency

while True:
    rows = []

    for site in websites:
        status, latency = check_website(site)
        rows.append({
            "Website": site,
            "Status": status,
            "Response_Time": latency,
            "Timestamp": datetime.now()
        })

    df = pd.DataFrame(rows)

    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

    print("Saved one round of data at", datetime.now())

    time.sleep(30)
