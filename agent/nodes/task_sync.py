import os
import json
from datetime import datetime, timedelta
from agent.state import AgentState
from agent.google_auth import get_google_service

def task_sync_node(state: AgentState) -> dict:
    plan = state.get("plan", {})
    if not plan:
        print("[TaskSync] No plan found. Skipping sync.")
        return {}
    
    goal_name = state.get("goal", "Goal Roadmap")
    try:
        service = get_google_service("tasks", "v1")
        print(f"[TaskSync] Authenticated. Syncing to Google Tasks for: '{goal_name}'")
        
        # 1. Find or Create a Task List
        tasklists = service.tasklists().list().execute()
        target_list_id = None
        for tl in tasklists.get('items', []):
            if tl['title'] == goal_name:
                target_list_id = tl['id']
                break
        
        if not target_list_id:
            new_list = service.tasklists().insert(body={'title': goal_name}).execute()
            target_list_id = new_list['id']
        
        # 2. Sync Plan Topics
        google_task_ids = state.get("google_task_ids", {})
        unit = str(state.get("timeline_unit") or plan.get("timeline_unit") or "Week").title()
        start_date = datetime.now()
        
        # Day increment based on unit
        days_per_unit = 7
        if unit == "Month": days_per_unit = 30
        elif unit == "Year": days_per_unit = 365
        
        for i, period in enumerate(plan.get("timeline", [])):
            # Robustly find the period label (Week 1, Month 1, etc.)
            period_label = (
                period.get('week') or 
                period.get('month') or 
                period.get('year') or 
                period.get('period') or 
                period.get('phase') or 
                f"{unit} {i+1}"
            )
            
            # Calculate an approximate due date
            due_date = (start_date + timedelta(days=(i + 1) * days_per_unit)).strftime('%Y-%m-%dT23:59:59Z')
            
            for topic in period.get("topics", []):
                task_name = topic.get("name")
                if not task_name or task_name in google_task_ids:
                    continue
                
                resource = topic.get("resource", "Resources")
                url = topic.get("resource_url", "#")
                notes = f"Period: {period_label}\nResource: {resource}\nLink: {url}\n\n{topic.get('description', '')}"
                
                task_body = {
                    'title': f"[{period_label}] {task_name}",
                    'notes': notes,
                    'due': due_date
                }
                
                print(f"  - Adding Google Task: {task_name}")
                new_task = service.tasks().insert(tasklist=target_list_id, body=task_body).execute()
                google_task_ids[task_name] = new_task['id']
                
        return {
            "google_task_ids": google_task_ids,
            "status_message": "Syncing tasks with Google Tasks..."
        }
        
    except Exception as e:
        print(f"[TaskSync] Sync failed: {e}")
        return {
            "google_task_ids": {},
            "status_message": "Syncing tasks with Google Tasks..."
        }
