class RCAEngine:
    def __init__(self):
        # Service dependency graph: Dependent -> Dependency
        # Gateway depends on UPI PSP, UPI PSP depends on Issuer Bank
        self.dependencies = {
            "gateway": ["upi"],
            "upi": ["bank"],
            "bank": []
        }
        # Inverse mapping: Dependency -> Dependents
        self.service_graph = {
            "bank": ["upi"],
            "upi": ["gateway"],
            "gateway": []
        }

    def analyze_root_cause(self, event_logger):
        """
        Identify the root cause by looking at recent failures and traversing dependencies.
        """
        recent_events = event_logger.get_events(limit=50)
        
        # Get services currently reporting errors or high latency
        failing_services = {}
        for event in recent_events:
            if event["severity"] in ["warning", "critical"]:
                svc = event["service"].lower()
                if svc not in failing_services:
                    failing_services[svc] = event

        if not failing_services:
            return None

        # Find the "bottom-most" service in the dependency chain that is failing
        # We start with any failing service and follow the dependencies downstream
        # until we find a service that is failing but its dependencies are healthy OR
        # it has no dependencies.
        
        root_service = None
        
        # Simple heuristic: The root is the service failing that is furthest downstream (e.g. Bank)
        # Bank -> UPI -> Gateway
        if "bank" in failing_services:
            root_service = "bank"
        elif "upi" in failing_services:
            root_service = "upi"
        elif "gateway" in failing_services:
            root_service = "gateway"

        if not root_service:
            return None

        # Build cascade path (root to dependents)
        cascade_path = [root_service]
        current = root_service
        while True:
            dependents = self.service_graph.get(current, [])
            found_next = False
            for dep in dependents:
                if dep in failing_services:
                    cascade_path.append(dep)
                    current = dep
                    found_next = True
                    break
            if not found_next:
                break

        return {
            "root_service": root_service.upper(),
            "cascade_path": [s.upper() for s in cascade_path],
            "confidence": 0.85 if len(cascade_path) > 1 else 0.7,
            "explanation": f"The error started at {root_service.upper()} and propagated downstream to {', '.join([s.upper() for s in cascade_path[1:]])}."
        }

# Global instance
rca_instance = RCAEngine()
