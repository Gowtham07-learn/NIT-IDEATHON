def detect_incident(service_metrics, injection_state=None, dependencies=None):
    """
    detect_incident(service_metrics, injection_state, dependencies):
    
    Check all:
    trigger if:
    latency > threshold (e.g. 1000ms)
    error_rate > threshold (e.g. 0.05)
    health < 1
    injected_error == True
    injected_latency == True
    dependency_down == True

    Return:
    {
    incident: True/False,
    reason: "latency | error | injection | dependency | health",
    severity: "warning | critical"
    }
    """
    
    # Defaults
    if injection_state is None:
        injection_state = {}
    if dependencies is None:
        dependencies = []

    # Unpack metrics
    latency = service_metrics.get("latency_ms", 0)
    error_rate = service_metrics.get("error_rate", 0)
    health = service_metrics.get("health", 1.0) # 1.0 is healthy, 0.0 is dead
    status_code = service_metrics.get("status", 200)

    # Thresholds
    LATENCY_THRESHOLD = 1000
    ERROR_RATE_THRESHOLD = 0.05 # 5%

    # 1. Injection Check
    if injection_state.get("injected_error") or injection_state.get("injected_latency"):
        return {
            "incident": True,
            "reason": "injection",
            "severity": "critical" if injection_state.get("injected_error") else "warning"
        }

    # 2. Dependency Check
    # dependencies is a list of statuses of downstream services? 
    # Or names of failed dependencies? 
    # Assuming list of failed dependency names based on prompt context "failed_dependencies"
    if dependencies:
        return {
            "incident": True,
            "reason": "dependency",
            "severity": "critical"
        }

    # 3. Health/Error Check
    if health < 1.0 or status_code != 200 or error_rate > ERROR_RATE_THRESHOLD:
        return {
            "incident": True,
            "reason": "error",
            "severity": "critical"
        }

    # 4. Latency Check
    if latency > LATENCY_THRESHOLD:
        return {
            "incident": True,
            "reason": "latency",
            "severity": "warning"
        }

    return {
        "incident": False,
        "reason": "normal",
        "severity": "info"
    }
