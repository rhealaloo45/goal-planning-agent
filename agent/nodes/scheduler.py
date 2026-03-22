import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from agent.state import AgentState

def scheduler_node(state: AgentState) -> dict:
    """Decide if we should send an email based on user status."""
    drift = state.get("drift_status", "steady")
    last_sent = state.get("last_email_sent", "")
    
    # Trigger logic: Send if drifting or if it's the very first cycle
    if drift != "steady" or not last_sent:
        print(f"[SchedulerNode] Goal status: {drift}. Triggering email agent.")
        return {"route": "send_email"}
        
    return {"route": "none"}

import base64
from agent.google_auth import get_google_service

def email_agent_node(state: AgentState) -> dict:
    """Send reminder emails, progress reports, or opportunity alerts via Gmail API (REST)."""
    drift = state.get("drift_status", "steady")
    metrics = state.get("progress_metrics", {})
    goal = state.get("goal", "Your Goal")
    user_email = os.getenv("SMTP_USER") # Use the same email from .env
    
    if not user_email:
        print("[EmailAgent] ERROR: SMTP_USER not set. Skipping.")
        return {}

    # ── Compose Email ──
    subject = f"Goal Update: {goal}"
    if drift != "steady":
        subject = f"⚠️ Action Required: Your {goal} Plan"
        body = (
            f"Hello!\n\nWe noticed your progress on '{goal}' is currently '{drift.upper()}'.\n"
            f"Completion Rate: {metrics.get('completion_rate', 0)}%\n\n"
            f"No worries! I have updated your roadmap with an 'Adaptive Plan' to better suit your pace.\n"
            f"Check your dashboard to see the adjustments."
        )
    else:
        body = (
            f"Great job!\n\nYou are stayin' steady with your '{goal}' plan.\n"
            f"Current Completion: {metrics.get('completion_rate', 0)}%\n\n"
            f"Keep up the momentum!"
        )

    # ── Convert to Gmail API Raw Format ──
    try:
        print(f"[EmailAgent] Building Gmail Service for {user_email}...")
        service = get_google_service("gmail", "v1")
        
        print("[EmailAgent] Creating MIME message...")
        message = MIMEMultipart()
        message['To'] = user_email
        message['From'] = f"Goal Agent <{user_email}>"
        message['Subject'] = f"{subject} ({datetime.now().strftime('%H:%M:%S')})"
        message.attach(MIMEText(body, 'plain'))

        print("[EmailAgent] Encoding raw payload...")
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        print(f"[EmailAgent] Executing Gmail Send API Call...")
        sent_msg = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        
        print(f"[EmailAgent] Gmail SUCCESS! Message ID: {sent_msg.get('id')}. Sent to: {user_email}")
        return {"last_email_sent": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - SUCCESS (API)"}
    except Exception as e:
        import traceback
        print(f"[EmailAgent] FATAL Gmail API ERROR: {e}")
        print(traceback.format_exc())
        return {"last_email_sent": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - FAILED (API: {str(e)[:50]})"}
