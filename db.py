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
            # 1. Create base table if it doesn't exist at all
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

            # 2. Migration: Add new columns if missing from a previous version
            cursor = conn.execute("PRAGMA table_info(plans)")
            existing_cols = [row[1] for row in cursor.fetchall()]
            
            new_cols = {
                "user_preferences_json": "TEXT",
                "drift_status": "TEXT DEFAULT 'steady'",
                "reflection_logs_json": "TEXT",
                "google_task_ids_json": "TEXT",
                "last_email_sent": "TEXT",
                "progress_metrics_json": "TEXT"
            }
            
            for col, col_type in new_cols.items():
                if col not in existing_cols:
                    print(f"[DB] Migrating: Adding column {col} to plans table.")
                    conn.execute(f"ALTER TABLE plans ADD COLUMN {col} {col_type}")
            
            conn.commit()

    def save_plan(self, goal, plan):
        plan_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO plans (id, goal, plan_json, completed_tasks_json, user_preferences_json, drift_status, reflection_logs_json, google_task_ids_json, last_email_sent, progress_metrics_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (plan_id, goal, json.dumps(plan), json.dumps([]), json.dumps({}), "steady", json.dumps([]), json.dumps({}), "", json.dumps({}), now, now)
            )
            conn.commit()
        return plan_id

    def list_plans(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM plans ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            plans = []
            for r in rows:
                try:
                    # Defensive Loading
                    plan_json_str = r["plan_json"] or "{}"
                    completed_json_str = r["completed_tasks_json"] or "[]"
                    
                    plan_data = json.loads(plan_json_str)
                    if not isinstance(plan_data, dict):
                        plan_data = {}
                        
                    completed = json.loads(completed_json_str)
                    if not isinstance(completed, list):
                        completed = []

                    # Calculate progress
                    total_tasks = 0
                    for period in plan_data.get("timeline", []):
                        if isinstance(period, dict):
                            total_tasks += len(period.get("topics", []))
                    
                    progress = 0
                    if total_tasks > 0:
                        progress = round((len(completed) / total_tasks) * 100)

                    plans.append({
                        "id": r["id"],
                        "goal": r["goal"] or "Unnamed Goal",
                        "summary": plan_data.get("goal_summary", ""),
                        "created_at": r["created_at"],
                        "progress": progress
                    })
                except Exception as e:
                    print(f"[DB] Skipping malformed plan {r['id']}: {e}")
                    continue
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
                "plan": json.loads(row["plan_json"] or "{}"),
                "completed_tasks": json.loads(row["completed_tasks_json"] or "[]"),
                "user_preferences": json.loads(row["user_preferences_json"] or "{}"),
                "drift_status": row["drift_status"] or "steady",
                "reflection_logs": json.loads(row["reflection_logs_json"] or "[]"),
                "google_task_ids": json.loads(row["google_task_ids_json"] or "{}"),
                "last_email_sent": row["last_email_sent"] or "",
                "progress_metrics": json.loads(row["progress_metrics_json"] or "{}"),
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

    def update_autonomous_fields(self, plan_id, updates: dict):
        """Update multiple fields resulting from autonomous execution. ONLY updates columns provided."""
        now = datetime.now().isoformat()
        
        # Mapping of key names to column names
        mapping = {
            "plan": "plan_json",
            "user_preferences": "user_preferences_json",
            "drift_status": "drift_status",
            "reflection_logs": "reflection_logs_json",
            "google_task_ids": "google_task_ids_json",
            "last_email_sent": "last_email_sent",
            "progress_metrics": "progress_metrics_json"
        }
        
        set_clauses = []
        params = []
        
        for key, col in mapping.items():
            if key in updates:
                set_clauses.append(f"{col} = ?")
                val = updates[key]
                # Encode as JSON if it's a dict or list (the mapping targets _json cols mostly)
                if col.endswith("_json") or isinstance(val, (dict, list)):
                    params.append(json.dumps(val))
                else:
                    params.append(val)
        
        if not set_clauses:
            return
            
        set_clauses.append("updated_at = ?")
        params.append(now)
        params.append(plan_id)
        
        with sqlite3.connect(DB_PATH) as conn:
            query = f"UPDATE plans SET {', '.join(set_clauses)} WHERE id = ?"
            conn.execute(query, params)
            conn.commit()

    def delete_plan(self, plan_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
            conn.commit()

db = PlanStore()
