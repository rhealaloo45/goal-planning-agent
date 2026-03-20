import sqlite3
import json
import uuid
from datetime import datetime
import os

DB_PATH = "plans.db"

class PlanStore:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    goal TEXT,
                    plan_json TEXT,
                    completed_tasks_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def save_plan(self, goal, plan):
        plan_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO plans (id, goal, plan_json, completed_tasks_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (plan_id, goal, json.dumps(plan), json.dumps([]), now, now)
            )
            conn.commit()
        return plan_id

    def list_plans(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, goal, plan_json, completed_tasks_json, created_at, updated_at FROM plans ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            plans = []
            for r in rows:
                plan_data = json.loads(r["plan_json"])
                completed = json.loads(r["completed_tasks_json"])
                # Calculate progress
                total_tasks = 0
                for week in plan_data.get("timeline", []):
                    total_tasks += len(week.get("topics", []))
                
                progress = 0
                if total_tasks > 0:
                    progress = round((len(completed) / total_tasks) * 100)

                plans.append({
                    "id": r["id"],
                    "goal": r["goal"],
                    "summary": plan_data.get("goal_summary", ""),
                    "created_at": r["created_at"],
                    "progress": progress
                })
            return plans

    def get_plan(self, plan_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row["id"],
                "goal": row["goal"],
                "plan": json.loads(row["plan_json"]),
                "completed_tasks": json.loads(row["completed_tasks_json"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    def update_completed_tasks(self, plan_id, completed_tasks):
        now = datetime.now().isoformat()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "UPDATE plans SET completed_tasks_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(completed_tasks), now, plan_id)
            )
            conn.commit()

    def update_full_plan(self, plan_id, plan):
        now = datetime.now().isoformat()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "UPDATE plans SET plan_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(plan), now, plan_id)
            )
            conn.commit()

    def delete_plan(self, plan_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
            conn.commit()

db = PlanStore()
