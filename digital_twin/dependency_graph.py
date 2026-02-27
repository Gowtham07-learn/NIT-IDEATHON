# digital_twin/dependency_graph.py

DEPENDENCY_GRAPH = {
    "https://www.uidai.gov.in": [
        "https://www.digilocker.gov.in",
        "https://www.incometax.gov.in"
    ],
    "https://www.onlinesbi.com": [
        "https://www.irctc.co.in"
    ],
    "https://www.digilocker.gov.in": [
        "https://api.publicapis.org/entries"
    ]
}
