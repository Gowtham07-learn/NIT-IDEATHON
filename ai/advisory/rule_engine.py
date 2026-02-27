class RuleEngine:
    def __init__(self):
        pass

    def get_advice(self, service_name, risk_analysis, latest_metrics):
        """
        Returns a list of recommendations based on risk and status.
        """
        recommendations = []
        root_cause = "Normal Operation"
        
        prob = risk_analysis.get('prob', 0)
        level = risk_analysis.get('level', 'Low')
        
        # 1. UP/DOWN Check
        is_up = latest_metrics.get(f"{service_name}_up", 1)
        
        if is_up == 0:
            root_cause = f"{service_name} Service Down"
            if service_name == "gateway":
                recommendations = [
                    "Check Gateway Logs (502 Bad Gateway)",
                    "Restart Gateway Service",
                    "Verify Load Balancer Health Checks"
                ]
            elif service_name == "upi":
                recommendations = [
                    "Restart UPI Pods / Containers",
                    "Check Database Connection Pool",
                    "Scale up Replicas"
                ]
            elif service_name == "bank":
                recommendations = [
                    "Contact Core Banking Provider",
                    "Check Leased Line / MPLS Connectivity",
                    "Enable Circuit Breaker at Gateway"
                ]
            return root_cause, recommendations

        # 2. Latency / Degradation Check
        latency = latest_metrics.get(f"{service_name}_latency_sum", 0)
        if latency > 2.0 or level in ["High", "Critical"]:
            root_cause = f"High Latency Detected ({latency:.2f}s)"
            
            if service_name == "gateway":
                recommendations = [
                    "Investigate Downstream Dependencies (UPI/Bank)",
                    "Check Network Bandwidth Saturation",
                    "Enable Rate Limiting"
                ]
            elif service_name == "upi":
                recommendations = [
                    "Optimize Database Queries",
                    "Check for Deadlocks",
                    "Increase Thread Pool Size"
                ]
            elif service_name == "bank":
                recommendations = [
                    "Report Slow Response to Bank IT",
                    "Switch to Backup Payment Rail"
                ]
        
        # 3. Dependency Logic (Gateway Specific)
        if service_name == "gateway" and root_cause != "Normal Operation":
             upi_up = latest_metrics.get("upi_up", 1)
             bank_up = latest_metrics.get("bank_up", 1)
             if upi_up == 0:
                 root_cause = "Cascading Failure: UPI is Down"
                 recommendations.append("Fix UPI Service immediately to restore Gateway health.")
             elif bank_up == 0:
                 root_cause = "Cascading Failure: Bank is Down"
                 recommendations.append("Enable Circuit Breaker for Bank Routes.")

        if not recommendations and level == "Medium":
             recommendations.append("Monitor closely for further degradation.")

        return root_cause, recommendations
