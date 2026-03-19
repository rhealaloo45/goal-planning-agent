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
        f"You are an expert planning AI.\n\n"
        f"User's goal: \"{goal}\"\n\n"
        f"Current plan:\n```json\n{plan_json}\n```\n\n"
        f"User's change request: \"{instruction}\"\n\n"
        f"Modify the plan to address the request.\n"
        f"Return the COMPLETE updated plan as JSON with the SAME structure.\n"
        f"Only change what the user asked. Keep everything else intact.\n"
    )

    raw = call_llm(
        prompt,
        system_prompt="You modify existing plans. Return ONLY valid JSON.",
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
    for p in plan.get("timeline", []):
        if "phase" in p and "week" not in p:
            p["week"] = p.pop("phase")
        if "tasks" in p and "topics" not in p:
            p["topics"] = [
                {
                    "name": t.get("title", t.get("name", "")),
                    "hours": t.get("hours", 2),
                    "resource": t.get("resource", ""),
                    "resource_url": t.get("resource_url", "#"),
                    "description": t.get("description", ""),
                }
                for t in p["tasks"]
            ]
            del p["tasks"]
