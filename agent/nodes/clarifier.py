"""
Clarifier Node
--------------
Generates structured clarification questions with selectable options.
Returns to the user (graph ends) so the frontend can collect answers.
"""

import json
from agent.state import AgentState
from agent.llm import call_llm


def clarifier_node(state: AgentState) -> dict:
    """Generate clarification questions with options."""
    goal = state.get("goal", "")

    prompt = (
        f"You are an expert goal-analysis agent.\n\n"
        f"A user submitted this goal:\n\"{goal}\"\n\n"
        f"You need more information to create a detailed weekly plan.\n"
        f"Generate 2-4 focused clarification questions.\n"
        f"Each question MUST have 3-5 selectable options.\n\n"
        f"Respond with JSON:\n"
        f'{{"needs_clarification": true, "questions": [\n'
        f'  {{"question": "What is your timeline?", "options": ["1 month", "3 months", "6 months"]}},\n'
        f'  {{"question": "Experience level?", "options": ["Beginner", "Intermediate", "Advanced"]}}\n'
        f"]}}\n\n"
        f"Tailor questions to the specific goal domain."
    )

    raw = call_llm(prompt, system_prompt="You are a goal-analysis AI.", expect_json=True)

    try:
        data = json.loads(_clean_json(raw))
        questions = data.get("questions", [])
        print(f"[Clarifier] Generated {len(questions)} questions")
        return {
            "questions": questions,
            "status": "needs_clarification",
        }
    except Exception as e:
        print(f"[Clarifier] Parse failed ({e}), using default questions...")
        return {
            "status": "needs_clarification",
            "questions": [
                {"question": "What is your primary focus area within this goal?", "options": ["Acquiring skills", "Completing a project", "Certification/Exam"]},
                {"question": "How much time per week can you realistically commit?", "options": ["5-10 hours", "10-20 hours", "Full-time immersion"]}
            ]
        }


def _clean_json(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[1:])
    if cleaned.endswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[:-1])
    return cleaned.strip()
