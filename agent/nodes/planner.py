"""
Planner Node
-------------
Generates a complete, structured, week-by-week plan.
Uses the goal + any clarification answers as context.
"""

import json
from agent.state import AgentState
from agent.llm import call_llm

def planner_node(state: AgentState) -> dict:
    """Generate the full plan."""
    goal = state.get("goal", "")
    answers = state.get("clarification_answers", {})

    context = ""
    if answers:
        context = "\n\nAdditional context from user:\n"
        for q, a in answers.items():
            context += f"  Q: {q}\n  A: {a}\n"

    prompt = (
        f"You are an expert planning agent specialized in long-term career roadmaps.\n\n"
        f"Create a COMPLETE roadmap that matches the user's timeframe exactly.\n"
        f"User's Goal: \"{goal}\"\n{context}\n\n"
        f"Respond with JSON:\n"
        f"1. \"timeline_unit\": \"Week\" | \"Month\" | \"Year\" (based on overall duration)\n"
        f"2. \"goal_summary\": 2-3 sentence summary\n"
        f"3. \"assumptions\": Array of strings\n"
        f"4. \"timeline\": Array of period objects (MINIMUM 6, MAXIMUM 12 periods):\n"
        f"   - \"period\": e.g. \"Month 1\", \"Year 1\", \"Phase 1\"\n"
        f"   - \"title\": phase title\n"
        f"   - \"total_hours\": hours for this period\n"
        f"   - \"topics\": array of objects (name, hours, resource, resource_url, description)\n"
        f"   - \"milestone\": achievement\n"
        f"5. \"resources\": Array of {{\"category\": str, \"items\": [{{\"name\": str, \"url\": str}}]}}\n"
        f"6. \"time_commitment\": Summary string\n"
        f"7. \"execution_strategy\": High-level advice\n\n"
        f"Rules:\n"
        f"  - For long goals (e.g. 2 years), do NOT just give 2 years. Give 8 Quarters or 12-24 Months if possible.\n"
        f"  - Specify exact CERTIFICATIONS and COURSES in topics.\n"
        f"  - Return JSON only."
    )

    raw = call_llm(
        prompt,
        system_prompt="Comprehensive planning agent. Return ONLY valid JSON.",
        expect_json=True,
    )

    try:
        plan = json.loads(_clean_json(raw))
        _normalize(plan)
        
        # Robustly find unit
        unit = plan.get("timeline_unit", "Week")
        if not any(u in str(unit) for u in ["Week", "Month", "Year"]):
            unit = "Week"
            
        return {
            "plan": plan, 
            "timeline_unit": str(unit).title(),
            "iteration_count": 0, 
            "critic_score": 0
        }
    except Exception as e:
        print(f"[Planner] Parse failed: {e}")
        return {
            "plan": _fallback(goal), 
            "timeline_unit": "Week",
            "iteration_count": 0, 
            "critic_score": 0
        }


# ── Helpers ──

def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()


def _normalize(plan: dict):
    """Normalize LLM keys: phase/period → canonical field."""
    # We want to support 'week', 'month', 'year' or just 'period'
    # But the frontend often looks for these specific keys.
    # To keep things simple and unified while remaining unit-aware:
    unit = str(plan.get("timeline_unit", "Week")).title()
    key_to_use = unit.lower() if unit in ["Week", "Month", "Year"] else "period"
    
    for p in plan.get("timeline", []):
        # Consolidation logic: ensure we have a common key but also preserve labels
        labels = ["week", "period", "phase", "month", "year"]
        found_key = None
        for k in labels:
            if k in p: 
                found_key = k
                break
        
        # If we found a label but it's not our canonical key, alias it
        if found_key and found_key != key_to_use:
            p[key_to_use] = p.get(found_key)

        # Ensure topics are normalized
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


def _fallback(goal: str) -> dict:
    return {
        "goal_summary": f"Comprehensive plan for: {goal}",
        "assumptions": ["Starting from scratch.", "Standard resources available."],
        "timeline": [
            {
                "week": "Week 1-2", "title": "Research & Setup", "total_hours": 12,
                "topics": [
                    {"name": "Research", "hours": 4, "resource": "Google Scholar", "resource_url": "https://scholar.google.com", "description": "Understand scope."},
                    {"name": "Gather resources", "hours": 4, "resource": "Various", "resource_url": "#", "description": "Collect tools."},
                    {"name": "Plan milestones", "hours": 4, "resource": "Notion", "resource_url": "https://notion.so", "description": "Break into milestones."},
                ],
                "milestone": "Setup complete."
            },
            {
                "week": "Week 3-5", "title": "Core Execution", "total_hours": 20,
                "topics": [
                    {"name": "Primary tasks", "hours": 10, "resource": "Domain-specific", "resource_url": "#", "description": "Core deliverables."},
                    {"name": "Review & iterate", "hours": 6, "resource": "Peer review", "resource_url": "#", "description": "Feedback and improve."},
                    {"name": "Documentation", "hours": 4, "resource": "Google Docs", "resource_url": "https://docs.google.com", "description": "Document progress."},
                ],
                "milestone": "Core work validated."
            },
        ],
        "resources": [{"category": "Tools", "items": [{"name": "Notion", "url": "https://notion.so"}]}],
        "time_commitment": "8-12 hours per week",
        "execution_strategy": "Start with research, execute phase by phase.",
    }
