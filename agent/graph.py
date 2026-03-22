"""
LangGraph Pipeline — Goal Planning Agent (Multi-Node)
=====================================================
Compiles the StateGraph with 7 nodes, conditional edges,
and a critic↔optimizer feedback loop.

Graph Structure:
    ┌─────────────────────────────────────────────────────────┐
    │ START → router → [conditional]                          │
    │          ├── "clarify"  → clarifier → END               │
    │          ├── "plan"     → planner → critic → [cond.]    │
    │          │                           ├── "accept"  → formatter → END
    │          │                           └── "optimize"→ optimizer ──┘
    │          │                                     (loops back to critic)
    │          └── "refine"  → refinement → formatter → END   │
    └─────────────────────────────────────────────────────────┘

Compiled graphs:
  - main_graph:     Full pipeline (START → router → ...)
  - continue_graph: After clarification (plan → critic ↔ optimizer → formatter)
"""

from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes.router import router_node, route_decision
from agent.nodes.clarifier import clarifier_node
from agent.nodes.planner import planner_node
from agent.nodes.search import search_events_node
from agent.nodes.critic import critic_node, route_after_critic
from agent.nodes.optimizer import optimizer_node
from agent.nodes.formatter import formatter_node
from agent.nodes.refinement import refinement_node

# ── New Integration Nodes ──
from agent.nodes.feasibility_checker import feasibility_checker_node
from agent.nodes.task_sync import task_sync_node


def build_main_graph() -> StateGraph:
    """
    Full planning pipeline with router, conditional edges,
    and critic↔optimizer loop.
    """
    g = StateGraph(AgentState)

    # ── Register all nodes ──
    g.add_node("router", router_node)
    g.add_node("clarifier", clarifier_node)
    g.add_node("planner", planner_node)
    g.add_node("search", search_events_node)
    g.add_node("critic", critic_node)
    g.add_node("optimizer", optimizer_node)
    g.add_node("formatter", formatter_node)
    g.add_node("refinement", refinement_node)

    # ── Entry ──
    g.set_entry_point("router")

    # ── Conditional: Router decides next node ──
    # ── Router decides next node ──
    g.add_conditional_edges(
        "router",
        route_decision,
        {
            "clarify": "clarifier",
            "plan": "feasibility",
            "refine": "refinement",
        },
    )

    g.add_node("feasibility", feasibility_checker_node)
    g.add_edge("feasibility", "planner")

    # ── Clarifier → END ──
    g.add_edge("clarifier", END)

    # ── Planner → Search → Critic ↔ Optimizer → Formatter → END ──
    g.add_edge("planner", "search")
    g.add_edge("search", "critic")

    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "accept": "formatter",
            "optimize": "optimizer",
        },
    )

    g.add_edge("optimizer", "critic")
    g.add_edge("formatter", END)

    # ── Refinement → Formatter → END ──
    g.add_edge("refinement", "formatter")

    return g


def build_continue_graph() -> StateGraph:
    """
    Post-clarification pipeline.
    Skips router & clarifier, goes directly to plan → search → critic loop.
    """
    g = StateGraph(AgentState)

    g.add_node("planner", planner_node)
    g.add_node("search", search_events_node)
    g.add_node("critic", critic_node)
    g.add_node("optimizer", optimizer_node)
    g.add_node("formatter", formatter_node)

    g.set_entry_point("planner")
    g.add_edge("planner", "search")
    g.add_edge("search", "critic")

    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "accept": "formatter",
            "optimize": "optimizer",
        },
    )

    g.add_edge("optimizer", "critic")
    g.add_edge("formatter", END)

    return g




# ── Compile once at import time ──
main_graph = build_main_graph().compile()
continue_graph = build_continue_graph().compile()
