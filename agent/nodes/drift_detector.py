"""
DriftDetector Node
------------------
Detects declining engagement or consistency based on metrics.
"""

from agent.state import AgentState

def drift_detector_node(state: AgentState) -> dict:
    metrics = state.get("progress_metrics", {})
    rate = metrics.get("completion_rate", 100)
    
    status = "steady"
    if rate < 70:
        status = "drifting"
    if rate < 40:
        status = "at_risk"
        
    return {"drift_status": status}
