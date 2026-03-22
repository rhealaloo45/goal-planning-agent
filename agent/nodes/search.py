"""
Search Node
-----------
Fetches related online or in-person events from the internet using DuckDuckGo Search.
Uses the LLM to filter, summarize, and identify why they are useful for the user.
"""

import json
from datetime import datetime
from duckduckgo_search import DDGS
from agent.state import AgentState
from agent.llm import call_llm


def search_events_node(state: AgentState) -> dict:
    """Find events related to the goal."""
    goal = state.get("goal", "")
    
    # Only skip if we already have a NON-EMPTY list of events
    if state.get("events") and len(state.get("events")) > 0:
        print("[SearchNode] Using already cached events.")
        return {}
    
    # 1. Search for online and in-person events
    # Broaden query to include variety of event types
    query = f"{goal} conferences webinars workshops 2026 online"
    print(f"[SearchNode] Executing search for: '{query}'")
    
    search_results = []
    try:
        # Direct call with DDGS (more resilient to initialization issues)
        results = DDGS().text(query, max_results=5)
        if results:
            for r in results:
                search_results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "url": r.get("href", r.get("link", ""))
                })
        print(f"[SearchNode] Found {len(search_results)} search results.")
    except Exception as e:
        print(f"[SearchNode] Search failed (continuing without live web results): {e}")

    # 2. Use LLM to extract or SUGGEST events if search is empty
    context = "\n\n".join([f"Source: {r['title']}\nSnippet: {r['snippet']}\nURL: {r['url']}" for r in search_results])
    
    current_date = datetime.now().strftime("%B %Y")
    
    prompt = (
        f"You are a professional event scout.\n\n"
        f"Goal: \"{goal}\"\n"
        f"Current Date: {current_date}\n\n"
        f"Search results found for 2026 events:\n{context if search_results else 'NO SEARCH RESULTS FOUND'}\n\n"
        f"TASK:\n"
        f"1. If search results contain actual events (conferences, webinars, etc.), extract 3-4 of them.\n"
        f"2. IMPORTANT: If search results are poor, empty, or irrelevant, use your internal knowledge to suggest 3 REAL-WORLD RECURRING events or workshops that happen in this field (e.g. PyCon, AWS Re:Invent, Coursera Live Sessions, etc.) even if the 2026 dates aren't fully confirmed. Users want to know WHERE to look.\n\n"
        f"For each event, provide:\n"
        f"- \"title\": Name\n"
        f"- \"summary\": 2-3 sentence description\n"
        f"- \"date\": Specific date OR 'Monthly', 'Annual - Q3', etc.\n"
        f"- \"organizer\": Who organises it\n"
        f"- \"why_useful\": Why this matters for the user's focus on \"{goal}\"\n"
        f"- \"url\": Reference URL or landing page\n"
        f"- \"type\": \"Online\" or \"In-Person\"\n\n"
        f"Respond ONLY with a JSON array of event objects."
    )

    raw = call_llm(
        prompt,
        system_prompt="You are a helpful event scout. Always find or suggest relevant events. Return JSON only.",
        expect_json=True,
    )

    try:
        events = json.loads(_clean_json(raw))
        if not isinstance(events, list):
            events = [events] if isinstance(events, dict) else []
        
        print(f"[SearchNode] Result: {len(events)} events found.")
        return {"events": events}
    except Exception as e:
        print(f"[SearchNode] LLM parse error: {e}")
        return {"events": []}


def _clean_json(raw: str) -> str:
    c = raw.strip()
    if c.startswith("```"):
        c = "\n".join(c.split("\n")[1:])
    if c.endswith("```"):
        c = "\n".join(c.split("\n")[:-1])
    return c.strip()
