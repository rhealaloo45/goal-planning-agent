"""
ProgressAnalyzer Node
---------------------
Computes completion rate, missed days, and overall pace.
"""

from agent.state import AgentState

def progress_analyzer_node(state: AgentState) -> dict:
    progress_history = state.get("progress_history", [])
    plan = state.get("plan", {})
    
    if not plan or not progress_history:
        return {"progress_metrics": {"rate": 0, "missed": 0, "pace": "normal"}}

    # Calculation logic for metrics
    completed_tasks = 0
    missed_tasks = 0
    
    # Simple history analysis: list of {"task": str, "status": "completed"|"missed", "date": str}
    for entry in progress_history:
        if entry.get("status") == "completed":
            completed_tasks += 1
        elif entry.get("status") == "missed":
            missed_tasks += 1
            
    total_entries = len(progress_history) if len(progress_history) > 0 else 1
    rate = (completed_tasks / total_entries) * 100
    
    pace = "normal"
    if rate < 70: pace = "slow"
    elif rate > 100: pace = "fast" # Maybe they do more tasks than planned/suggested
    
    metrics = {
        "completion_rate": round(rate, 2),
        "missed_days": missed_tasks,
        "pace": pace,
        "total_completed": completed_tasks
    }
    
    return {"progress_metrics": metrics}
