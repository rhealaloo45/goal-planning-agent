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
from agent.graph import main_graph, continue_graph
from agent.nodes.task_sync import task_sync_node
from db import db
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template, Response, stream_with_context
from dotenv import load_dotenv

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

    def generate():
        global _last_state
        current_state = initial_state
        try:
            for event in main_graph.stream(initial_state):
                for node_name, updates in event.items():
                    current_state.update(updates)
                    if "status_message" in updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': updates['status_message']})}\n\n"
            
            _last_state = current_state
            result_data = {
                "goal": current_state.get("goal", goal),
                "status": current_state.get("status", "completed"),
                "questions": current_state.get("questions", []),
                "plan": current_state.get("plan"),
                "events": current_state.get("events", []),
                "timeline_unit": current_state.get("timeline_unit", "Week"),
            }
            yield f"data: {json.dumps({'type': 'result', 'data': result_data})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


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

    def generate():
        global _last_state
        current_state = state
        try:
            for event in continue_graph.stream(state):
                for node_name, updates in event.items():
                    current_state.update(updates)
                    if "status_message" in updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': updates['status_message']})}\n\n"
            
            _last_state = current_state
            result_data = {
                "goal": current_state.get("goal", goal),
                "status": current_state.get("status", "completed"),
                "questions": [],
                "plan": current_state.get("plan"),
                "events": current_state.get("events", []),
                "timeline_unit": current_state.get("timeline_unit", "Week"),
            }
            yield f"data: {json.dumps({'type': 'result', 'data': result_data})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


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

    def generate():
        global _last_state
        current_state = state
        try:
            for event in main_graph.stream(state):
                for node_name, updates in event.items():
                    current_state.update(updates)
                    if "status_message" in updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': updates['status_message']})}\n\n"
            
            if current_state.get("plan"):
                if _last_state:
                    _last_state["plan"] = current_state["plan"]
            
            result_data = {
                "success": bool(current_state.get("plan")),
                "plan": current_state.get("plan"),
                "events": current_state.get("events", []),
                "timeline_unit": current_state.get("timeline_unit", "Week"),
                "message": "Plan updated successfully." if current_state.get("plan") else "Could not apply changes."
            }
            yield f"data: {json.dumps({'type': 'result', 'data': result_data})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


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
    
    def generate():
        try:
            state = {"goal": goal, "plan": plan, "google_task_ids": {}}
            # We use stream here too just to provide the status message
            # Even though task_sync_node is a single function, we wrap it
            yield f"data: {json.dumps({'type': 'status', 'message': 'Syncing tasks with Google Tasks...'})}\n\n"
            
            sync_result = task_sync_node(state)
            
            if sync_result.get("google_task_ids"):
                db.update_autonomous_fields(plan_id, {"google_task_ids": sync_result["google_task_ids"]})
                
            yield f"data: {json.dumps({'type': 'result', 'data': {'success': True, 'id': plan_id}})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'id': plan_id})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

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

    def generate():
        current_state = state
        try:
            for event in main_graph.stream(state):
                for node_name, updates in event.items():
                    current_state.update(updates)
                    if "status_message" in updates:
                        yield f"data: {json.dumps({'type': 'status', 'message': updates['status_message']})}\n\n"
            
            if current_state.get("plan"):
                db.update_full_plan(plan_id, current_state["plan"])
            
            yield f"data: {json.dumps({'type': 'result', 'data': {'success': bool(current_state.get('plan')), 'plan': current_state.get('plan')}})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


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
