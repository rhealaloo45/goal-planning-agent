import sqlite3
conn = sqlite3.connect("plans.db")
cursor = conn.cursor()
cursor.execute("SELECT id, last_email_sent, drift_status FROM plans ORDER BY created_at DESC LIMIT 5;")
for row in cursor.fetchall():
    print(f"ID: {row[0][:8]} | Drift: {row[2]} | Last Sent: {row[1]}")
conn.close()
