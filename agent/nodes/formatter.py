"""
Formatter Node
--------------
Final node before output. Ensures the plan has a consistent,
frontend-friendly structure. Normalizes any remaining quirks.
"""

from agent.state import AgentState


def formatter_node(state: AgentState) -> dict:
    """Clean up the plan for frontend consumption."""
    plan = state.get("plan", {})

    if not plan:
        return {"status": "completed"}

    # Ensure every week has consistent shape
    for week in plan.get("timeline", []):
        week.setdefault("week", "Week ?")
        week.setdefault("title", "Untitled Phase")
        week.setdefault("total_hours", 0)
        week.setdefault("milestone", "")
        week.setdefault("topics", [])

        # Ensure every topic in the week has all fields
        for topic in week["topics"]:
            topic.setdefault("name", "Untitled")
            topic.setdefault("hours", 0)
            topic.setdefault("resource", "")
            topic.setdefault("resource_url", "#")
            topic.setdefault("description", "")

        # Recalculate total_hours from topics if they don't match
        topic_hours = sum(t.get("hours", 0) for t in week["topics"])
        if topic_hours > 0:
            week["total_hours"] = topic_hours

    # Ensure top-level keys
    plan.setdefault("goal_summary", "")
    plan.setdefault("assumptions", [])
    plan.setdefault("resources", [])
    plan.setdefault("time_commitment", "")
    plan.setdefault("execution_strategy", "")

    print(f"[Formatter] Plan formatted: {len(plan.get('timeline', []))} weeks")
    return {"plan": plan, "status": "completed"}
