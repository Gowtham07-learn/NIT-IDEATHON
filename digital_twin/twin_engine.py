# digital_twin/twin_engine.py

import pandas as pd
from digital_twin.dependency_graph import DEPENDENCY_GRAPH

def run_digital_twin(real_df, scenario):
    """
    Takes real monitoring data
    Simulates a failure scenario
    Returns simulated impact
    """

    twin_df = real_df.copy()
    trigger = scenario["trigger"]

    # Force trigger failure
    twin_df.loc[twin_df["Website"] == trigger, "Status"] = "DOWN"
    twin_df.loc[twin_df["Website"] == trigger, "Reason"] = (
        f"Simulated failure: {scenario['description']}"
    )
    twin_df.loc[twin_df["Website"] == trigger, "Response_Time"] = None

    # Cascading impact
    impacted = DEPENDENCY_GRAPH.get(trigger, [])

    for service in impacted:
        twin_df.loc[twin_df["Website"] == service, "Status"] = "DOWN"
        twin_df.loc[twin_df["Website"] == service, "Reason"] = (
            f"Cascaded failure due to {trigger}"
        )
        twin_df.loc[twin_df["Website"] == service, "Response_Time"] = None

    return twin_df
