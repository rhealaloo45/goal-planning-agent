"""
AutoAdjustTrigger Node
----------------------
Decides if we need to trigger the AdaptivePlanner based on drift.
"""

from agent.state import AgentState

def auto_adjust_trigger_node(state: AgentState) -> dict:
    drift = state.get("drift_status", "steady")
    
    # If drifting or at risk, indicate we should branch to adaptive re-planning
    should_adjust = drift in ["drifting", "at_risk"]
    
    # Returns a routing-ready key
    return {"route": "adaptive_plan" if should_adjust else "continue"}
