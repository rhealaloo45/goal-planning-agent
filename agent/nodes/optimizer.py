"""
Optimizer Node
--------------
Takes the current plan + critic feedback and produces an improved version.
Increments iteration_count so the loop eventually terminates.
"""

import json
from agent.state import AgentState
from agent.llm import call_llm


def optimizer_node(state: AgentState) -> dict:
    """Improve the plan based on critic feedback."""
    plan = state.get("plan", {})
    feedback = state.get("critic_feedback", {})
    iteration = state.get("iteration_count", 0)
    goal = state.get("goal", "")

    issues = feedback.get("issues", [])
    suggestions = feedback.get("suggestions", [])
    plan_json = json.dumps(plan, indent=2)

    prompt = (
        f"You are a plan optimizer.\n\n"
        f"User's Goal: \"{goal}\"\n\n"
        f"Current plan:\n```json\n{plan_json}\n```\n\n"
        f"Critic Issues:\n"
        + "\n".join(f"  - {i}" for i in issues) + "\n\n"
        f"Critic Suggestions:\n"
        + "\n".join(f"  - {s}" for s in suggestions) + "\n\n"
        f"Improve the plan by addressing every issue and suggestion.\n"
        f"Return the COMPLETE updated plan as JSON with the SAME structure.\n"
        f"Be more specific with topics, hours, resources, and milestones.\n"
    )

    raw = call_llm(
        prompt,
        system_prompt="You are a plan optimizer. Return ONLY valid JSON.",
        expect_json=True,
    )

    try:
        improved = json.loads(_clean_json(raw))
        _normalize(improved)
        print(f"[Optimizer] Plan improved (iteration {iteration + 1})")
        return {"plan": improved, "iteration_count": iteration + 1}
    except (json.JSONDecodeError, KeyError):
        print("[Optimizer] Parse failed, keeping current plan")
        return {"iteration_count": iteration + 1}


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
