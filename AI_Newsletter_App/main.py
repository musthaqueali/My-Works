import os
import asyncio
from datetime import datetime, time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator
from typing import Optional, List
import re

from config import config
import database
from pipeline.generator import get_research_file, save_research_file, update_arxiv_file_with_live_data
from pipeline.synthesizer import generate_newsletter_issue, markdown_to_email_html
from services.email_service import send_single_email, broadcast_newsletter, get_delivery_logs, log_event

app = FastAPI(title=config.NEWSLETTER_NAME)

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

current_draft = None
last_automated_run = None

def get_or_create_draft():
    global current_draft
    if not current_draft:
        current_draft = generate_newsletter_issue()
    return current_draft

def validate_email_format(email: str) -> str:
    email = email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Invalid email format")
    return email

# Pydantic Request Models
class SubscribeRequest(BaseModel):
    email: str
    name: Optional[str] = ""

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        return validate_email_format(v)

class StreamSaveRequest(BaseModel):
    content: str

class TestEmailRequest(BaseModel):
    email: str
    subject: Optional[str] = None

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        return validate_email_format(v)

class BroadcastRequest(BaseModel):
    subject: Optional[str] = None

class SettingsUpdateRequest(BaseModel):
    email_provider: str
    from_email: str
    from_name: str
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = ""
    smtp_password: Optional[str] = ""
    resend_api_key: Optional[str] = ""

# --- BACKGROUND AUTOMATED DAILY SCHEDULER ---

async def run_daily_automated_cycle():
    """Fetches latest ArXiv papers, synthesizes ELECTRON, and broadcasts to subscribers."""
    global current_draft, last_automated_run
    log_event("⏰ [DAILY AUTOMATION] Triggered daily cycle: Fetching arXiv papers and synthesizing ELECTRON...")
    try:
        current_draft = generate_newsletter_issue()
        broadcast_res = broadcast_newsletter(
            issue_id=current_draft.get("issue_id"),
            subject=current_draft["subject"],
            html_content=current_draft["html"],
            text_content=current_draft["markdown"]
        )
        last_automated_run = datetime.now()
        log_event(f"✅ [DAILY AUTOMATION COMPLETED] Sent to {broadcast_res.get('sent', 0)} subscriber(s) via {config.EMAIL_PROVIDER}.")
        return broadcast_res
    except Exception as e:
        log_event(f"❌ [DAILY AUTOMATION ERROR] {str(e)}", level="ERROR")
        raise e

async def daily_scheduler_worker():
    """Background worker that executes daily at configured hour/minute (e.g. 08:00 AM)."""
    global last_automated_run
    while True:
        try:
            if config.AUTO_SCHEDULE_ENABLED:
                now = datetime.now()
                target_hour = config.DAILY_SEND_HOUR
                target_minute = config.DAILY_SEND_MINUTE
                
                # Check if it's the scheduled minute and hasn't run in the last hour
                if now.hour == target_hour and now.minute == target_minute:
                    if not last_automated_run or (now - last_automated_run).total_seconds() > 3600:
                        await run_daily_automated_cycle()
            await asyncio.sleep(45) # Check every 45 seconds
        except Exception as e:
            print("Scheduler worker exception:", e)
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(daily_scheduler_worker())
    log_event(f"ELECTRON Engine initialized. Daily scheduler active for {config.DAILY_SEND_HOUR:02d}:{config.DAILY_SEND_MINUTE:02d} AM/PM.")

# --- WEB PAGE ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"config": config}
    )

# --- SUBSCRIBER API ROUTES ---

@app.post("/api/subscribe")
async def subscribe(req: SubscribeRequest):
    res = database.add_subscriber(req.email, req.name)
    return res

@app.get("/api/subscribers")
async def list_subscribers():
    return database.get_subscribers()

@app.delete("/api/subscribers/{subscriber_id}")
async def delete_subscriber(subscriber_id: int):
    success = database.delete_subscriber(subscriber_id)
    return {"success": success}

@app.get("/api/stats")
async def get_stats():
    stats = database.get_stats()
    stats["auto_schedule_enabled"] = config.AUTO_SCHEDULE_ENABLED
    stats["daily_send_time"] = f"{config.DAILY_SEND_HOUR:02d}:{config.DAILY_SEND_MINUTE:02d}"
    stats["last_automated_run"] = last_automated_run.strftime("%Y-%m-%d %H:%M:%S") if last_automated_run else "Pending"
    return stats

# --- NEWSLETTER GENERATION & PREVIEW ROUTES ---

@app.get("/api/newsletter/current")
async def get_current_newsletter():
    draft = get_or_create_draft()
    return draft

@app.post("/api/newsletter/generate")
async def trigger_generate():
    global current_draft
    current_draft = generate_newsletter_issue()
    return {
        "success": True,
        "message": "ELECTRON broadsheet issue synthesized with fresh arXiv papers!",
        "issue": current_draft
    }

# --- AUTOMATION & BROADCAST ROUTES ---

@app.post("/api/scheduler/run-now")
async def trigger_scheduler_now():
    """Manual trigger to execute the daily automated cycle on-demand."""
    res = await run_daily_automated_cycle()
    return {
        "success": True,
        "message": "Daily automated cycle executed! Live arXiv papers fetched, issue synthesized, and dispatched to subscribers.",
        "results": res
    }

@app.post("/api/newsletter/test-send")
async def test_send(req: TestEmailRequest):
    draft = get_or_create_draft()
    subject = req.subject or draft["subject"]
    try:
        send_single_email(
            to_email=req.email,
            subject=subject,
            html_content=draft["html"],
            text_content=draft["markdown"]
        )
        return {
            "success": True,
            "message": f"Test dispatch transmitted to {req.email} via {config.EMAIL_PROVIDER}!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/newsletter/broadcast")
async def broadcast(req: BroadcastRequest):
    draft = get_or_create_draft()
    subject = req.subject or draft["subject"]
    result = broadcast_newsletter(
        issue_id=draft.get("issue_id"),
        subject=subject,
        html_content=draft["html"],
        text_content=draft["markdown"]
    )
    return result

# --- SETTINGS ROUTES ---

@app.get("/api/settings")
async def get_settings():
    return {
        "email_provider": config.EMAIL_PROVIDER,
        "from_email": config.FROM_EMAIL,
        "from_name": config.FROM_NAME,
        "smtp_host": config.SMTP_HOST,
        "smtp_port": config.SMTP_PORT,
        "smtp_user": config.SMTP_USER,
        "smtp_password_set": bool(config.SMTP_PASSWORD),
        "resend_api_key_set": bool(config.RESEND_API_KEY)
    }

@app.post("/api/settings")
async def update_settings(req: SettingsUpdateRequest):
    env_path = os.path.join(BASE_DIR, ".env")
    
    config.EMAIL_PROVIDER = req.email_provider.lower()
    config.FROM_EMAIL = req.from_email.strip()
    config.FROM_NAME = req.from_name.strip()
    config.SMTP_HOST = req.smtp_host.strip()
    config.SMTP_PORT = int(req.smtp_port)
    config.SMTP_USER = req.smtp_user.strip()
    if req.smtp_password:
        config.SMTP_PASSWORD = req.smtp_password.strip().replace(" ", "")
    if req.resend_api_key:
        config.RESEND_API_KEY = req.resend_api_key.strip()
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f'NEWSLETTER_NAME="{config.NEWSLETTER_NAME}"\n')
        f.write(f'NEWSLETTER_TAGLINE="{config.NEWSLETTER_TAGLINE}"\n')
        f.write(f'EMAIL_PROVIDER={config.EMAIL_PROVIDER}\n')
        f.write(f'FROM_EMAIL={config.FROM_EMAIL}\n')
        f.write(f'FROM_NAME="{config.FROM_NAME}"\n')
        f.write(f'SMTP_HOST={config.SMTP_HOST}\n')
        f.write(f'SMTP_PORT={config.SMTP_PORT}\n')
        f.write(f'SMTP_USER={config.SMTP_USER}\n')
        f.write(f'SMTP_PASSWORD={config.SMTP_PASSWORD}\n')
        f.write(f'SMTP_USE_TLS=true\n')
        f.write(f'RESEND_API_KEY={config.RESEND_API_KEY}\n')
        f.write(f'AUTO_SCHEDULE_ENABLED={str(config.AUTO_SCHEDULE_ENABLED).lower()}\n')
        f.write(f'DAILY_SEND_HOUR={config.DAILY_SEND_HOUR}\n')
        f.write(f'DAILY_SEND_MINUTE={config.DAILY_SEND_MINUTE}\n')
        
    return {"success": True, "message": f"ELECTRON configuration saved! Active provider: {config.EMAIL_PROVIDER}"}

# --- RESEARCH STREAM MANAGEMENT ROUTES ---

@app.get("/api/streams/{filename}")
async def get_stream(filename: str):
    try:
        content = get_research_file(filename)
        return {"filename": filename, "content": content}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/streams/{filename}")
async def save_stream(filename: str, req: StreamSaveRequest):
    try:
        save_research_file(filename, req.content)
        return {"success": True, "message": f"{filename} saved successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/logs")
async def get_logs():
    return get_delivery_logs()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
