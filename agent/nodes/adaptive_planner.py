"""
AdaptivePlanner Node
--------------------
Adjusts future plan dynamically based on performance and preferences.
"""

import json
from agent.state import AgentState
from agent.llm import call_llm

def adaptive_planner_node(state: AgentState) -> dict:
    current_plan = state.get("plan", {})
    metrics = state.get("progress_metrics", {})
    preferences = state.get("user_preferences", {})
    goal = state.get("goal", "")
    
    if not current_plan:
        return {}

    prompt = (
        f"You are an adaptive planning agent specialized in course-correcting roadmaps.\n\n"
        f"Goal: \"{goal}\"\n"
        f"Current Plan: {json.dumps(current_plan)}\n"
        f"Current Progress Metrics: {json.dumps(metrics)}\n"
        f"User Preferences: {json.dumps(preferences)}\n\n"
        f"TASK:\n"
        f"Modify the remaining periods of the roadmap to ensure it is achievable.\n"
        f"If the user is SLOW (low completion rate), reduce the scope or extend timelines.\n"
        f"If the user is FAST, increase the depth or accelerate future phases.\n"
        f"Maintain the overall structure and JSON format.\n\n"
        f"Respond ONLY with valid JSON (FULL PLAN structure)."
    )

    raw = call_llm(
        prompt,
        system_prompt="Adaptive re-planning agent. Return ONLY valid JSON.",
        expect_json=True,
    )

    try:
        new_plan = json.loads(_clean_json(raw))
        return {"plan": new_plan, "route": "completed"}
    except Exception as e:
        print(f"[AdaptivePlanner] Parse failed: {e}")
        return {"route": "completed"} # Do not change existing plan on failure

def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()
