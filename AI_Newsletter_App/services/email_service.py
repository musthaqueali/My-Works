import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from typing import List, Dict, Optional
from config import config
from database import get_subscribers, mark_issue_sent

delivery_logs = []

def log_event(message: str, level: str = "INFO"):
    from datetime import datetime
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}"
    delivery_logs.append(entry)
    try:
        print(entry)
    except UnicodeEncodeError:
        print(entry.encode('ascii', 'replace').decode('ascii'))
    if len(delivery_logs) > 100:
        delivery_logs.pop(0)

def get_delivery_logs() -> List[str]:
    return list(reversed(delivery_logs))

def send_via_smtp(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be configured in .env")
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config.FROM_NAME} <{config.FROM_EMAIL}>"
    msg["To"] = to_email

    if text_content:
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        if config.SMTP_USE_TLS:
            server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(msg)
    return True

def send_via_resend(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    if not config.RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY must be configured in .env")
        
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {config.RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": f"{config.FROM_NAME} <{config.FROM_EMAIL}>",
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    if text_content:
        payload["text"] = text_content
        
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code in (200, 201):
        return True
    else:
        raise RuntimeError(f"Resend API Error ({resp.status_code}): {resp.text}")

def send_single_email(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    provider = config.EMAIL_PROVIDER.lower()
    
    if provider == "simulation":
        log_event(f"[SIMULATION] Mock email dispatched to: {to_email} | Subject: '{subject}'")
        return True
    elif provider == "smtp":
        send_via_smtp(to_email, subject, html_content, text_content)
        log_event(f"[SMTP] Successfully sent to {to_email}")
        return True
    elif provider == "resend":
        send_via_resend(to_email, subject, html_content, text_content)
        log_event(f"[RESEND] Successfully sent to {to_email}")
        return True
    else:
        raise ValueError(f"Unknown email provider: {provider}")

def broadcast_newsletter(issue_id: Optional[int], subject: str, html_content: str, text_content: Optional[str] = None) -> Dict:
    active_subscribers = get_subscribers(status="active")
    if not active_subscribers:
        log_event("Broadcast halted: No active subscribers found in database.", level="WARN")
        return {
            "success": False,
            "message": "No active subscribers found in database. Add subscribers first!",
            "total": 0,
            "sent": 0,
            "failed": 0,
            "provider": config.EMAIL_PROVIDER
        }

    sent_count = 0
    failed_count = 0
    errors = []

    log_event(f"Starting broadcast to {len(active_subscribers)} subscriber(s) using provider: '{config.EMAIL_PROVIDER}'")

    for sub in active_subscribers:
        email = sub["email"]
        try:
            send_single_email(email, subject, html_content, text_content)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            err_msg = f"Failed to send to {email}: {str(e)}"
            errors.append(err_msg)
            log_event(err_msg, level="ERROR")

    if issue_id:
        mark_issue_sent(issue_id, sent_count)

    log_event(f"Broadcast completed: {sent_count} sent, {failed_count} failed.")
    return {
        "success": True,
        "total": len(active_subscribers),
        "sent": sent_count,
        "failed": failed_count,
        "errors": errors,
        "provider": config.EMAIL_PROVIDER
    }
