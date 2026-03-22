"""
OpportunityWatcher Node
-----------------------
Periodically searches for new events/resources relevant to goals.
Suggests integration into the plan.
"""

from agent.state import AgentState
from agent.nodes.search import search_events_node

def opportunity_watcher_node(state: AgentState) -> dict:
    """
    Search for NEW opportunities based on the goal.
    This effectively re-triggers the search node, which finds fresh events.
    In a real system, this could track search_history to avoid duplicates.
    """
    print("[OpportunityWatcher] Checking for new opportunities...")
    # This currently populates state["events"] with new search results.
    return search_events_node(state)
