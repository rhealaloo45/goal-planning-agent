"""
Goal-Based Planning Agent — Flask + LangGraph (Multi-Node)
==========================================================
All routes invoke compiled LangGraph StateGraphs.

Endpoints:
  POST /start    → Invoke main_graph (router → ...)
  POST /clarify  → Invoke continue_graph (plan → critic ↔ optimizer → formatter)
  POST /refine   → Invoke main_graph with user_instruction (router → refinement → formatter)
  POST /reset    → Clear state

Run: python app.py  |  http://localhost:1644
"""

import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv

from agent.graph import main_graph, continue_graph
from agent.nodes.task_sync import task_sync_node
from db import db
from datetime import datetime

load_dotenv()
app = Flask(__name__)

_last_state: dict | None = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    """
    Entry point. Invoke the main graph.
    Router decides: clarify | plan (with critic loop) | refine.
    """
    global _last_state
    data = request.get_json(force=True)
    goal = data.get("goal", "").strip()
    if not goal:
        return jsonify({"error": "Goal is required."}), 400

    initial_state = {
        "goal": goal,
        "status": "pending",
        "clarified": False,
        "questions": [],
        "clarification_answers": {},
        "plan": None,
        "critic_score": 0,
        "critic_feedback": {},
        "iteration_count": 0,
        "user_instruction": "",
        "route": "plan",
        "events": [],
        "timeline_unit": "Week",
        "google_task_ids": {},
    }

    print(f"\n{'='*50}")
    print(f"[/start] Goal: '{goal}'")
    print(f"{'='*50}")

    print(f"[/start] Running LangGraph pipeline...")
    try:
        result = main_graph.invoke(initial_state)
    except Exception as e:
        print(f"[/start] FATAL GRAPH ERROR: {e}")
        return jsonify({"error": f"Internal Graph Error: {e}"}), 500

    print(f"[/start] → Final Keys: {list(result.keys())}")
    print(f"[/start] → route={result.get('route')} | status={result.get('status')} | plan={'YES' if result.get('plan') else 'NO'}")

    print(f"[/start] → status={result.get('status')} | iterations={result.get('iteration_count', 0)} | score={result.get('critic_score', '-')}")
    _last_state = result

    return jsonify({
        "goal": result.get("goal", goal),
        "status": result.get("status", "completed"),
        "questions": result.get("questions", []),
        "plan": result.get("plan"),
        "events": result.get("events", []),
        "timeline_unit": result.get("timeline_unit", "Week"),
    })


@app.route("/clarify", methods=["POST"])
def clarify():
    """
    After user answers clarification questions.
    Invoke the continue graph: plan → critic ↔ optimizer → formatter.
    """
    global _last_state
    data = request.get_json(force=True)
    goal = data.get("goal", "").strip()
    answers = data.get("answers", {})
    if not goal:
        return jsonify({"error": "Goal is required."}), 400

    state = {
        "goal": goal,
        "status": "planning",
        "clarified": True,
        "questions": [],
        "clarification_answers": answers,
        "plan": None,
        "critic_score": 0,
        "critic_feedback": {},
        "iteration_count": 0,
        "user_instruction": "",
        "route": "plan",
        "events": [],
        "timeline_unit": "Week",
    }

    print(f"\n{'='*50}")
    print(f"[/clarify] Goal: '{goal}' | Answers: {len(answers)}")
    print(f"{'='*50}")

    result = continue_graph.invoke(state)

    print(f"[/clarify] → status={result.get('status')} | iterations={result.get('iteration_count', 0)} | score={result.get('critic_score', '-')}")
    _last_state = result

    return jsonify({
        "goal": result.get("goal", goal),
        "status": result.get("status", "completed"),
        "questions": [],
        "plan": result.get("plan"),
        "events": result.get("events", []),
        "timeline_unit": result.get("timeline_unit", "Week"),
    })


@app.route("/refine", methods=["POST"])
def refine():
    """
    User-driven refinement. Invoke the main graph with user_instruction set.
    Router detects this and routes to refinement → formatter.
    """
    global _last_state
    data = request.get_json(force=True)
    goal = data.get("goal", "").strip()
    plan = data.get("plan")
    message = data.get("message", "").strip()

    if not plan or not message:
        return jsonify({"error": "Plan and message are required."}), 400

    state = {
        "goal": goal,
        "status": "completed",
        "clarified": True,
        "questions": [],
        "clarification_answers": {},
        "plan": plan,
        "critic_score": 0,
        "critic_feedback": {},
        "iteration_count": 0,
        "user_instruction": message,
        "route": "",
        "events": data.get("events", []),
        "timeline_unit": data.get("timeline_unit", "Week"),
    }

    print(f"\n{'='*50}")
    print(f"[/refine] Instruction: '{message[:60]}'")
    print(f"{'='*50}")

    result = main_graph.invoke(state)

    if result.get("plan"):
        if _last_state:
            _last_state["plan"] = result["plan"]
        return jsonify({
            "success": True, 
            "plan": result["plan"], 
            "events": result.get("events", []),
            "timeline_unit": result.get("timeline_unit", "Week"),
            "message": "Plan updated successfully."
        })

    return jsonify({"success": False, "plan": plan, "message": "Could not apply changes."})


@app.route("/update-plan", methods=["POST"])
def update_plan():
    """Accept inline-edited plan from the frontend."""
    global _last_state
    data = request.get_json(force=True)
    plan = data.get("plan")
    if not plan:
        return jsonify({"error": "Plan data is required."}), 400
    if _last_state:
        _last_state["plan"] = plan
    return jsonify({"status": "updated", "plan": plan})


@app.route("/reset", methods=["POST"])
def reset():
    global _last_state
    _last_state = None
    return jsonify({"status": "reset"})


# ────── My Plans Persistence ──────

@app.route("/save", methods=["POST"])
def save():
    """Manual save that ALSO triggers Google Tasks sync."""
    data = request.get_json(force=True)
    goal = data.get("goal")
    plan = data.get("plan")
    if not goal or not plan:
        return jsonify({"error": "Goal and plan are required to save."}), 400
    
    # 1. Save to local DB
    plan_id = db.save_plan(goal, plan)
    
    # 2. Trigger Google Tasks Sync (only on manual save as requested)
    try:
        # We wrap in a partial state for the node
        state = {"goal": goal, "plan": plan, "google_task_ids": {}}
        sync_result = task_sync_node(state)
        
        # 3. Update DB with new task IDs if sync worked
        if sync_result.get("google_task_ids"):
            db.update_autonomous_fields(plan_id, {"google_task_ids": sync_result["google_task_ids"]})
            
    except Exception as e:
        print(f"[/save] Google Tasks sync failed but data is locally saved: {e}")

    return jsonify({"success": True, "id": plan_id})

@app.route("/plans", methods=["GET"])
def list_plans():
    plans = db.list_plans()
    return jsonify({"plans": plans})

@app.route("/plans/<plan_id>", methods=["GET"])
def get_plan(plan_id):
    plan_data = db.get_plan(plan_id)
    if not plan_data:
        return jsonify({"error": "Plan not found."}), 404
    return jsonify(plan_data)

@app.route("/plans/delete/<plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    db.delete_plan(plan_id)
    return jsonify({"success": True})

@app.route("/toggle-task", methods=["POST"])
def toggle_task():
    data = request.get_json(force=True)
    plan_id = data.get("id")
    completed = data.get("completed_tasks") # full array of IDs
    if not plan_id:
        return jsonify({"error": "ID is required."}), 400
    
    db.update_completed_tasks(plan_id, completed)
    return jsonify({"success": True})

@app.route("/save-refine", methods=["POST"])
def save_refine():
    """Refine a SAVED plan with AI logic."""
    data = request.get_json(force=True)
    plan_id = data.get("id")
    message = data.get("message")
    
    saved_data = db.get_plan(plan_id)
    if not saved_data: return jsonify({"error": "Plan not found"}), 404

    state = {
        "goal": saved_data["goal"],
        "plan": saved_data["plan"],
        "user_instruction": message,
        "route": "refine",
        "iteration_count": 0,
        "critic_score": 0,
        "events": [],
        "timeline_unit": saved_data["plan"].get("timeline_unit", "Week"),
        "status": "completed",
        "clarified": True,
        "questions": [],
        "clarification_answers": {}
    }

    result = main_graph.invoke(state)
    if result.get("plan"):
        db.update_full_plan(plan_id, result["plan"])
        return jsonify({"success": True, "plan": result["plan"]})
    
    return jsonify({"success": False, "message": "The AI could not refine your saved plan. Please try a different instruction."})


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 1644))
    print(f"\n[*] Goal Agent (LangGraph Multi-Node) at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
