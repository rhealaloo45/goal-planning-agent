"""
Reflection Node
---------------
Performs weekly/milestone reflections on what worked and what didn't.
Logs insights to reflection_logs.
"""

import json
from datetime import datetime
from agent.state import AgentState
from agent.llm import call_llm

def reflection_node(state: AgentState) -> dict:
    history = state.get("progress_history", [])
    logs = state.get("reflection_logs", [])
    goal = state.get("goal", "")
    
    if not history:
        return {}

    prompt = (
        f"You are a meta-cognitive reflection agent.\n"
        f"Goal: \"{goal}\"\n"
        f"Progress History: {json.dumps(history)}\n\n"
        f"Analyze this week's progress:\n"
        f"1. What worked based on completion patterns?\n"
        f"2. What didn't work based on missed tasks?\n"
        f"3. Recommendation for the NEXT week.\n\n"
        f"Respond with ONLY JSON:\n"
        f"{{\n"
        f"  \"insight\": \"Short analytical insight\",\n"
        f"  \"recommendation\": \"Specific plan recommendation\",\n"
        f"  \"timestamp\": str (current iso date)\n"
        f"}}\n"
    )

    raw = call_llm(
        prompt,
        system_prompt="Meta-cognitive Reflection Agent. Evaluate weekly performance.",
        expect_json=True,
    )

    try:
        new_log = json.loads(_clean_json(raw))
        new_log["timestamp"] = datetime.now().isoformat()
        return {"reflection_logs": logs + [new_log]}
    except Exception as e:
        print(f"[Reflection] Parse failed: {e}")
        return {}

def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()
