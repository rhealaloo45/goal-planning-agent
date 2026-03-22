"""
PreferenceLearner Node
---------------------
Learns user behavior patterns from performance history and updates preferences.
"""

import json
from agent.state import AgentState
from agent.llm import call_llm

def preference_learner_node(state: AgentState) -> dict:
    history = state.get("progress_history", [])
    current_prefs = state.get("user_preferences", {})
    
    if not history:
        return {}

    prompt = (
        f"You are a behavior learning agent.\n\n"
        f"Current User Task History: {json.dumps(history)}\n"
        f"Existing Preferences: {json.dumps(current_prefs)}\n\n"
        f"TASK:\n"
        f"1. Identify consistency patterns (time of day, days of week).\n"
        f"2. Note resource types the user engages with most (video, docs, interactive).\n"
        f"3. Note preferred task duration.\n"
        f"4. Update the user_preferences dictionary.\n\n"
        f"Return ONLY valid JSON for the updated object."
    )

    raw = call_llm(
        prompt,
        system_prompt="User Behavior Learner. Return ONLY valid JSON for the updated preferences.",
        expect_json=True,
    )

    try:
        updated_prefs = json.loads(_clean_json(raw))
        return {"user_preferences": updated_prefs}
    except Exception as e:
        print(f"[PreferenceLearner] Parse failed: {e}")
        return {}

def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()
