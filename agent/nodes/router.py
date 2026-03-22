"""
Router Node
-----------
First node in the graph. Inspects the state and decides where to go:
  - "clarify" → goal is vague, needs clarification questions
  - "plan"    → goal is clear enough, generate a plan
  - "refine"  → user sent a refinement instruction on an existing plan
"""

from agent.state import AgentState


from agent.llm import call_llm


def router_node(state: AgentState) -> dict:
    """Determine the next step using LLM for smart routing."""

    # 1. Refinement takes precedence
    if state.get("user_instruction") and state.get("plan"):
        print("[Router] → refine (active request)")
        return {"route": "refine"}

    # 2. If already clarified (by node or user skip), proceed to plan
    if state.get("clarified"):
        print("[Router] → plan (already clarified)")
        return {"route": "plan"}

    # 3. Use LLM to decide if clarification is needed
    goal = state.get("goal", "")
    
    prompt = (
        f"Goal: \"{goal}\"\n\n"
        f"Analyze if this goal is specific enough to build a multi-step roadmap.\n"
        f"If the goal is broad (e.g. 'Learn AI', 'Be successful'), return 'CLARIFY'.\n"
        f"If the goal has a specific target or timeframe (e.g. 'Learn Python in 2 months', '5-year plan for VP'), return 'PLAN'.\n\n"
        f"Return ONLY 'CLARIFY' or 'PLAN'."
    )
    
    decision = call_llm(
        prompt,
        system_prompt="You are a routing agent. Decide if a goal needs clarification or can be planned now.",
        expect_json=False
    ).strip().upper()

    if "CLARIFY" in decision:
        print("[Router] → clarify (LLM decision)")
        return {"route": "clarify"}
    
    print("[Router] → plan (LLM decision)")
    return {"route": "plan", "clarified": True}


def route_decision(state: AgentState) -> str:
    """Conditional edge function. Defaults to 'plan' if state is missing route."""
    route = state.get("route")
    if not route:
        return "plan"
    return route
