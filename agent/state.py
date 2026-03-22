"""
LangGraph State — Shared TypedDict
-----------------------------------
Single source of truth flowing through every node in the graph.
Each node reads what it needs and returns a partial update dict.
"""

from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    # ── User Input ──
    goal: str                           # Raw user goal
    user_instruction: str               # Refinement instruction (e.g. "make it faster")

    # ── Clarification ──
    status: str                         # "pending" | "needs_clarification" | "planning" | "completed"
    clarified: bool                     # Whether the goal has been clarified
    questions: list                     # Clarification questions with options
    clarification_answers: dict         # User's selected answers
    
    # ── Planning ──
    plan: Optional[dict]                # The structured plan
    timeline_unit: str                  # "Week" | "Month" | "Year"
    route: str                          # "clarify" | "plan" | "refine"

    # ── Critic / Optimizer Loop ──
    critic_score: int                   # Critic's quality score (1-10)
    critic_feedback: dict               # {"issues": [...], "suggestions": [...]}
    iteration_count: int                # Current critic↔optimizer iteration

    # ── Search & Events ──
    events: list                        # List of related events (online/in-person)

    # ── External Integrations ──
    google_task_ids: dict               # Map internal tasks → Google Task IDs
