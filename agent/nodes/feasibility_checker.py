"""
FeasibilityChecker Node
-----------------------
Validates user goal + timeline before planning begins.
Outputs feasibility score and suggestions.
"""

import json
from agent.state import AgentState
from agent.llm import call_llm

def feasibility_checker_node(state: AgentState) -> dict:
    """Validate goal feasibility."""
    goal = state.get("goal", "")
    answers = state.get("clarification_answers", {})
    
    context = ""
    if answers:
        context = "\n\nAdditional context from user:\n"
        for q, a in answers.items():
            context += f"  Q: {q}\n  A: {a}\n"

    prompt = (
        f"You are a strategic feasibility analyst specialized in personal goal achievement.\n\n"
        f"Evaluate the following user goal and its associated constraints:\n"
        f"User's Goal: \"{goal}\"\n{context}\n\n"
        f"Analyze:\n"
        f"1. Is the goal realistically achievable within the implied or stated timeline?\n"
        f"2. Are the resources/constraints realistic for a human learner?\n"
        f"3. What are the primary risks to completion?\n\n"
        f"Respond with ONLY JSON:\n"
        f"{{\n"
        f"  \"score\": int (0-100),\n"
        f"  \"status\": \"Highly Feasible\" | \"Feasible with Adjustments\" | \"Unrealistic\",\n"
        f"  \"reasoning\": \"Short 2-3 sentence explanation\",\n"
        f"  \"suggestions\": [\"suggestion 1\", \"suggestion 2\"],\n"
        f"  \"risks\": [\"risk 1\", \"risk 2\"]\n"
        f"}}\n"
    )

    raw = call_llm(
        prompt,
        system_prompt="Strategic feasibility analyst. Return ONLY valid JSON.",
        expect_json=True,
    )

    try:
        status_data = json.loads(_clean_json(raw))
        return {
            "feasibility_status": status_data,
            "status_message": "Checking if your goal is realistic..."
        }
    except Exception as e:
        print(f"[FeasibilityChecker] Parse failed: {e}")
        return {
            "feasibility_status": {
                "score": 50,
                "status": "Unknown",
                "reasoning": "Could not parse feasibility analysis.",
                "suggestions": [],
                "risks": []
            },
            "status_message": "Checking if your goal is realistic..."
        }

def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()
