"""
Critic Node
-----------
Reviews the generated plan and assigns a quality score.
If score < THRESHOLD, the graph loops to Optimizer.

Output format:
  {
    "score": 1-10,
    "issues": ["..."],
    "suggestions": ["..."]
  }
"""

import json
from agent.state import AgentState
from agent.llm import call_llm

SCORE_THRESHOLD = 8
MAX_ITERATIONS = 3


def critic_node(state: AgentState) -> dict:
    """Evaluate plan quality. Sets critic_score and critic_feedback."""
    plan = state.get("plan", {})
    iteration = state.get("iteration_count", 0)

    # Guard: max iterations reached — accept the plan as-is
    if iteration >= MAX_ITERATIONS:
        print(f"[Critic] Max iterations ({MAX_ITERATIONS}) reached. Accepting plan.")
        return {
            "critic_score": SCORE_THRESHOLD,
            "critic_feedback": {"issues": [], "suggestions": []},
        }

    plan_json = json.dumps(plan, indent=2)

    prompt = (
        f"You are a strict plan quality critic.\n\n"
        f"User's Goal: \"{state.get('goal', '')}\"\n\n"
        f"Plan (iteration {iteration + 1}):\n```json\n{plan_json}\n```\n\n"
        f"Evaluate on:\n"
        f"  1. SPECIFICITY — topics, hours, resources are concrete?\n"
        f"  2. FEASIBILITY — time estimates realistic?\n"
        f"  3. COMPLETENESS — covers the full goal?\n"
        f"  4. DURATION ALIGNMENT — does the timeline cover the user's requested timeframe? (e.g. if user said 2 years, does the plan span 2 years?)\n"
        f"  5. RESOURCE QUALITY — real URLs included?\n"
        f"  6. MILESTONES — actionable and measurable?\n\n"
        f"Respond with JSON:\n"
        f'{{"score": <1-10>, "issues": ["..."], "suggestions": ["..."]}}\n\n'
        f"Be extremely critical of duration mismatches. Score honestly."
    )

    raw = call_llm(
        prompt,
        system_prompt="You are a plan quality evaluator. Return JSON only.",
        expect_json=True,
    )

    try:
        result = json.loads(_clean_json(raw))
        score = int(result.get("score", 5))
        feedback = {
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", []),
        }
        print(f"[Critic] Score: {score}/10 | Issues: {len(feedback['issues'])}")
        return {
            "critic_score": score, 
            "critic_feedback": feedback,
            "status_message": "Reviewing the quality of your plan..."
        }
    except (json.JSONDecodeError, KeyError, ValueError):
        # Parse failed — accept the plan
        print("[Critic] Parse failed, accepting plan")
        return {
            "critic_score": SCORE_THRESHOLD,
            "critic_feedback": {"issues": [], "suggestions": []},
            "status_message": "Reviewing the quality of your plan..."
        }


def route_after_critic(state: AgentState) -> str:
    """Conditional edge: decide whether to optimize or accept."""
    score = state.get("critic_score", 0)
    iteration = state.get("iteration_count", 0)

    if score >= SCORE_THRESHOLD or iteration >= MAX_ITERATIONS:
        print(f"[Critic→] Accept (score={score}, iter={iteration})")
        return "accept"

    print(f"[Critic→] Optimize (score={score}, iter={iteration})")
    return "optimize"


def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()
