"""
Refinement Node
---------------
Accepts user instructions like "make it faster", "reduce workload", etc.
Modifies the existing plan accordingly via the LLM.
"""

import json
from agent.state import AgentState
from agent.llm import call_llm


def refinement_node(state: AgentState) -> dict:
    """Apply user's natural-language change request to the plan."""
    plan = state.get("plan", {})
    instruction = state.get("user_instruction", "")
    goal = state.get("goal", "")

    if not plan or not instruction:
        return {}

    plan_json = json.dumps(plan, indent=2)

    prompt = (
        f"You are a specialized planning AI that takes an existing roadmap and modifies it according to a user request.\n\n"
        f"USER GOAL: \"{goal}\"\n"
        f"CURRENT PLAN:\n```json\n{plan_json}\n```\n\n"
        f"USER CHANGE REQUEST: \"{instruction}\"\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. You MUST apply the change requested by the user even if it requires significant modifications to weeks, hours, or topics.\n"
        f"2. Return the COMPLETE updated plan as a single JSON object.\n"
        f"3. Use exactly the same JSON keys ('timeline', 'goal_summary', 'assumptions', etc.) as the current plan.\n"
        f"4. If the user asks for more/less time, add or remove weeks from the 'timeline' array accordingly.\n"
        f"5. If the user asks for more/less work, adjust the 'hours' per topic and 'total_hours' per week.\n\n"
        f"JSON OUTPUT:"
    )

    raw = call_llm(
        prompt,
        system_prompt="You apply surgical edits to JSON plans. Return ONLY valid JSON.",
        expect_json=True,
    )

    try:
        updated = json.loads(_clean_json(raw))
        _normalize(updated)
        print(f"[Refinement] Plan refined for: \"{instruction[:50]}\"")
        return {"plan": updated}
    except (json.JSONDecodeError, KeyError):
        print("[Refinement] Parse failed, plan unchanged")
        return {}


def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()


def _normalize(plan: dict):
    if not plan or "timeline" not in plan: return
    for p in plan.get("timeline", []):
        if "phase" in p and "week" not in p:
            p["week"] = p.pop("phase")
        if "title" not in p and "week" in p:
            p["title"] = p["week"]
        
        # If topics is missing, look for tasks
        if "topics" not in p and "tasks" in p:
            p["topics"] = p.pop("tasks")
        
        # Ensure topics shape
        if "topics" in p:
            for t in p["topics"]:
                if "title" in t and "name" not in t:
                    t["name"] = t.pop("title")
                if "hours" not in t: t["hours"] = 2
                if "resource_url" not in t: t["resource_url"] = "#"
                if "description" not in t: t["description"] = ""
