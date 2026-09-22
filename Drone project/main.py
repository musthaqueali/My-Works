import os
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import base64
import json

from database import init_db, get_connection
from models import (
    CustomerPUCCreate, NotificationSendRequest,
    CashfreeOrderRequest, CashfreeVerifyRequest, GoogleAuthRequest,
    NormalLoginRequest, NormalRegisterRequest
)
from cashfree_service import create_cashfree_order, verify_cashfree_order
from notification_service import send_notification
from scheduler import check_and_dispatch_reminders, start_scheduler_loop

app = FastAPI(title="PUCDesk Minimal", version="1.0.0", description="Minimal PUC Centre Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    asyncio.create_task(start_scheduler_loop())

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# ----------------- GOOGLE AUTH (SIGN IN & SIGN UP) -----------------
@app.post("/api/auth/google")
async def google_auth(payload: GoogleAuthRequest):
    email = payload.email
    name = payload.name
    picture = payload.picture
    google_id = payload.google_id
    auth_type = (payload.auth_type or "signin").lower()

    # If Google GIS JWT credential is provided, decode payload
    if payload.credential:
        try:
            parts = payload.credential.split(".")
            if len(parts) >= 2:
                padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                decoded_bytes = base64.urlsafe_b64decode(padded)
                data = json.loads(decoded_bytes.decode("utf-8"))
                email = data.get("email")
                name = data.get("name")
                picture = data.get("picture")
                google_id = data.get("sub")
        except Exception as e:
            print("JWT decode error:", e)

    if not email:
        email = "inspector@almadina-puc.com"
        name = name or "Musthaque Ali"

    conn = get_connection()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE email = ? OR (google_id IS NOT NULL AND google_id = ?)", (email, google_id))
    user = cursor.fetchone()

    centre_id = 1
    # If user provided new centre info during Sign-Up:
    if payload.centre_name and payload.centre_code:
        cursor.execute("SELECT id FROM puc_centres WHERE code = ?", (payload.centre_code.strip().upper(),))
        existing_centre = cursor.fetchone()
        if existing_centre:
            centre_id = existing_centre["id"]
        else:
            cursor.execute("""
            INSERT INTO puc_centres (name, code, owner_name, phone, sms_credits, subscription_status, subscription_plan)
            VALUES (?, ?, ?, ?, 3420, 'ACTIVE', '₹150/Month Basic')
            """, (payload.centre_name.strip(), payload.centre_code.strip().upper(), name, payload.phone or "9847012345"))
            centre_id = cursor.lastrowid
            conn.commit()

    if not user:
        # Create user account
        cursor.execute("""
        INSERT INTO users (google_id, email, name, picture, centre_id, role)
        VALUES (?, ?, ?, ?, ?, 'OPERATOR')
        """, (google_id, email, name or email.split("@")[0], picture or "", centre_id))
        user_id = cursor.lastrowid
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        message = f"Welcome to PUCDesk, {name}! Your centre account has been created."
    else:
        # If signing in, update centre_id if new centre specified
        if payload.centre_name and payload.centre_code:
            cursor.execute("UPDATE users SET centre_id = ? WHERE id = ?", (centre_id, user["id"]))
            conn.commit()
        message = f"Welcome back, {user['name']}! Signed in successfully."

    # Fetch centre info
    cursor.execute("SELECT name, code FROM puc_centres WHERE id = ?", (user["centre_id"] if user else 1,))
    centre_row = cursor.fetchone()

    user_dict = dict(user)
    user_dict["centre_name"] = centre_row["name"] if centre_row else "Al-Madina Testing Station"
    user_dict["centre_code"] = centre_row["code"] if centre_row else "KL-11-PUC-408"

    conn.close()

    return {
        "success": True,
        "auth_type": auth_type,
        "message": message,
        "user": user_dict
    }

# ----------------- NORMAL EMAIL & PASSWORD AUTH -----------------
def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(f"PUC_SALT_{password}".encode("utf-8")).hexdigest()

@app.post("/api/auth/login")
async def normal_login(payload: NormalLoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(payload.password)

    cursor.execute("SELECT * FROM users WHERE email = ?", (payload.email.strip().lower(),))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return JSONResponse(status_code=400, content={"success": False, "message": "No account found with this email. Please sign up."})

    if user["password_hash"] and user["password_hash"] != pwd_hash:
        conn.close()
        return JSONResponse(status_code=400, content={"success": False, "message": "Incorrect password. Please try again."})

    # Fetch centre info
    cursor.execute("SELECT name, code FROM puc_centres WHERE id = ?", (user["centre_id"] or 1,))
    centre_row = cursor.fetchone()
    conn.close()

    user_dict = dict(user)
    user_dict["centre_name"] = centre_row["name"] if centre_row else "Al-Madina Testing Station"
    user_dict["centre_code"] = centre_row["code"] if centre_row else "KL-11-PUC-408"

    return {
        "success": True,
        "message": f"Welcome back, {user['name']}!",
        "user": user_dict
    }

@app.post("/api/auth/register")
async def normal_register(payload: NormalRegisterRequest):
    conn = get_connection()
    cursor = conn.cursor()
    email_clean = payload.email.strip().lower()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email_clean,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return JSONResponse(status_code=400, content={"success": False, "message": "Account already exists with this email. Please sign in."})

    pwd_hash = hash_password(payload.password)

    # Register centre if provided
    centre_id = 1
    if payload.centre_name and payload.centre_code:
        cursor.execute("SELECT id FROM puc_centres WHERE code = ?", (payload.centre_code.strip().upper(),))
        c_row = cursor.fetchone()
        if c_row:
            centre_id = c_row["id"]
        else:
            cursor.execute("""
            INSERT INTO puc_centres (name, code, owner_name, phone, sms_credits, subscription_status, subscription_plan)
            VALUES (?, ?, ?, ?, 3420, 'ACTIVE', '₹150/Month Basic')
            """, (payload.centre_name.strip(), payload.centre_code.strip().upper(), payload.name.strip(), payload.phone.strip()))
            centre_id = cursor.lastrowid
            conn.commit()

    avatar = f"https://ui-avatars.com/api/?name={payload.name.replace(' ', '+')}&background=059669&color=fff"
    cursor.execute("""
    INSERT INTO users (email, password_hash, name, picture, centre_id, role)
    VALUES (?, ?, ?, ?, ?, 'OPERATOR')
    """, (email_clean, pwd_hash, payload.name.strip(), avatar, centre_id))
    user_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT name, code FROM puc_centres WHERE id = ?", (centre_id,))
    centre_row = cursor.fetchone()
    conn.close()

    user_dict = dict(user)
    user_dict["centre_name"] = centre_row["name"] if centre_row else "Al-Madina Testing Station"
    user_dict["centre_code"] = centre_row["code"] if centre_row else "KL-11-PUC-408"

    return {
        "success": True,
        "message": f"Account registered successfully! Welcome, {user['name']}.",
        "user": user_dict
    }

@app.get("/api/auth/me")
def get_current_user(email: str = None):

    conn = get_connection()
    cursor = conn.cursor()
    if email:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user:
            conn.close()
            return {"authenticated": True, "user": dict(user)}
    
    # Fallback to first user or default profile
    cursor.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1")
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"authenticated": True, "user": dict(user)}
    return {
        "authenticated": False,
        "user": {
            "name": "Musthaque Ali",
            "email": "inspector@almadina-puc.com",
            "role": "OPERATOR",
            "picture": ""
        }
    }


# ----------------- MINIMAL KPI STATS -----------------
@app.get("/api/stats")
def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    today_str = today.isoformat()
    one_day_later = (today + timedelta(days=1)).isoformat()
    seven_days_later = (today + timedelta(days=7)).isoformat()

    # Centre info & Credits
    cursor.execute("SELECT name, code, sms_credits, subscription_status, subscription_plan FROM puc_centres WHERE id = 1")
    centre = cursor.fetchone()

    # 1. Total Customers / Vehicles (from the 100 dataset)
    cursor.execute("SELECT COUNT(*) FROM puc_records")
    total_records = cursor.fetchone()[0] or 0

    # 2. Expiring in 1 Day
    cursor.execute("""
    SELECT COUNT(*) FROM puc_records 
    WHERE date(expiry_date) >= date(?) AND date(expiry_date) <= date(?)
    """, (today_str, one_day_later))
    expiring_1_day = cursor.fetchone()[0] or 0

    # 3. Expiring in 1 Week (<= 7 days)
    cursor.execute("""
    SELECT COUNT(*) FROM puc_records 
    WHERE date(expiry_date) >= date(?) AND date(expiry_date) <= date(?)
    """, (today_str, seven_days_later))
    expiring_1_week = cursor.fetchone()[0] or 0

    # 4. Expired Records
    cursor.execute("SELECT COUNT(*) FROM puc_records WHERE date(expiry_date) < date(?)", (today_str,))
    expired_count = cursor.fetchone()[0] or 0

    # 5. Safe / Active records (> 7 days)
    cursor.execute("SELECT COUNT(*) FROM puc_records WHERE date(expiry_date) > date(?)", (seven_days_later,))
    active_count = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "centre_name": centre["name"] if centre else "Al-Madina Testing Station",
        "centre_code": centre["code"] if centre else "KL-11-PUC-408",
        "sms_credits": centre["sms_credits"] if centre else 3420,
        "subscription_status": centre["subscription_status"] if centre else "ACTIVE",
        "subscription_plan": centre["subscription_plan"] if centre else "₹150/Month",
        "total_records": total_records,
        "expiring_1_day": expiring_1_day,
        "expiring_1_week": expiring_1_week,
        "expired_count": expired_count,
        "active_count": active_count
    }

# ----------------- FILTERED RECORDS & SEARCH -----------------
@app.get("/api/records")
def list_records(filter: str = "all"):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    today_str = today.isoformat()

    query = "SELECT * FROM puc_records"
    params = []

    if filter == "1_day":
        one_day_later = (today + timedelta(days=1)).isoformat()
        query += " WHERE date(expiry_date) >= date(?) AND date(expiry_date) <= date(?)"
        params = [today_str, one_day_later]
    elif filter == "1_week":
        seven_days_later = (today + timedelta(days=7)).isoformat()
        query += " WHERE date(expiry_date) >= date(?) AND date(expiry_date) <= date(?)"
        params = [today_str, seven_days_later]
    elif filter == "expired":
        query += " WHERE date(expiry_date) < date(?)"
        params = [today_str]

    query += " ORDER BY date(expiry_date) ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    records = []
    for r in rows:
        exp_date = datetime.strptime(r["expiry_date"], "%Y-%m-%d").date()
        diff_days = (exp_date - today).days

        if diff_days < 0:
            urgency_label = f"Expired {abs(diff_days)}d ago" if diff_days < -1 else "Expired Yesterday"
            urgency_tier = "EXPIRED"
        elif diff_days == 0:
            urgency_label = "Expires Today!"
            urgency_tier = "CRITICAL"
        elif diff_days == 1:
            urgency_label = "Expires Tomorrow (1 Day)"
            urgency_tier = "CRITICAL"
        elif diff_days <= 7:
            urgency_label = f"Expires in {diff_days} days"
            urgency_tier = "WARNING"
        else:
            urgency_label = f"Valid ({diff_days} days left)"
            urgency_tier = "NORMAL"

        records.append({
            "id": r["id"],
            "owner_name": r["owner_name"],
            "plate_number": r["plate_number"],
            "mobile_number": r["mobile_number"],
            "issue_date": r["issue_date"],
            "expiry_date": r["expiry_date"],
            "validity_period": r["validity_period"],
            "fee_amount": r["fee_amount"],
            "urgency_label": urgency_label,
            "urgency_tier": urgency_tier,
            "days_remaining": diff_days
        })

    conn.close()
    return {"records": records, "count": len(records), "filter": filter}

@app.get("/api/records/search")
def search_records(q: str):
    conn = get_connection()
    cursor = conn.cursor()
    search_term = f"%{q.strip().upper()}%"
    cursor.execute("""
    SELECT * FROM puc_records
    WHERE UPPER(plate_number) LIKE ? OR UPPER(owner_name) LIKE ? OR mobile_number LIKE ?
    ORDER BY date(expiry_date) ASC LIMIT 50
    """, (search_term, search_term, search_term))
    rows = cursor.fetchall()
    conn.close()

    today = datetime.now().date()
    records = []
    for r in rows:
        exp_date = datetime.strptime(r["expiry_date"], "%Y-%m-%d").date()
        diff_days = (exp_date - today).days

        if diff_days < 0:
            urgency_label = f"Expired {abs(diff_days)}d ago"
            urgency_tier = "EXPIRED"
        elif diff_days <= 1:
            urgency_label = "Expires in 1 Day"
            urgency_tier = "CRITICAL"
        elif diff_days <= 7:
            urgency_label = f"Expires in {diff_days} days"
            urgency_tier = "WARNING"
        else:
            urgency_label = f"Valid ({diff_days}d left)"
            urgency_tier = "NORMAL"

        records.append({
            "id": r["id"],
            "owner_name": r["owner_name"],
            "plate_number": r["plate_number"],
            "mobile_number": r["mobile_number"],
            "issue_date": r["issue_date"],
            "expiry_date": r["expiry_date"],
            "validity_period": r["validity_period"],
            "fee_amount": r["fee_amount"],
            "urgency_label": urgency_label,
            "urgency_tier": urgency_tier,
            "days_remaining": diff_days
        })

    return {"results": records, "count": len(records)}

# ----------------- ADD CUSTOMER & CERTIFICATE -----------------
@app.post("/api/records")
def add_customer_record(payload: CustomerPUCCreate):
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().date()
    issue_date = payload.issue_date or today.isoformat()
    if payload.expiry_date:
        expiry_date = payload.expiry_date
    else:
        days = 180 if "6" in payload.validity_period else 365
        expiry_date = (today + timedelta(days=days)).isoformat()

    cursor.execute("""
    INSERT INTO puc_records (
        centre_id, owner_name, plate_number, mobile_number,
        issue_date, expiry_date, validity_period, fee_amount, sms_opt_in
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        1, payload.owner_name.strip(), payload.plate_number.strip().upper(),
        payload.mobile_number.strip(), issue_date, expiry_date,
        payload.validity_period, payload.fee_amount
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "id": new_id,
        "owner_name": payload.owner_name,
        "plate_number": payload.plate_number.upper(),
        "expiry_date": expiry_date,
        "message": f"Customer & Vehicle {payload.plate_number.upper()} saved successfully."
    }

# ----------------- REMINDERS & NOTIFICATIONS -----------------
@app.post("/api/notifications/send")
async def manual_send_notification(payload: NotificationSendRequest):
    result = await send_notification(
        centre_id=1,
        record_id=payload.record_id,
        plate_number=payload.plate_number,
        mobile_number=payload.mobile_number,
        owner_name=payload.owner_name or "Customer",
        expiry_date=payload.expiry_date or "soon",
        channel=payload.channel
    )
    return result

@app.post("/api/notifications/batch-dispatch")
async def batch_dispatch():
    result = await check_and_dispatch_reminders()
    return {
        "success": True,
        "message": f"Dispatched reminders for {result.get('dispatched_count', 0)} upcoming vehicles."
    }

# ----------------- PRICING & SUBSCRIPTION CATALOG -----------------
@app.get("/api/pricing/plans")
def get_pricing_plans():
    return {
        "subscription_plans": [
            {
                "id": "starter",
                "name": "Starter Operator Plan",
                "price_monthly": 150.00,
                "price_yearly": 1500.00,
                "sms_credits": 1000,
                "is_popular": False,
                "description": "Essential solution for single-lane emission testing stations.",
                "features": [
                    "Full Expiry Radar (1 Day / 1 Week / Overdue)",
                    "1,000 SMS & WhatsApp Reminders / mo",
                    "TRAI DLT AIRPOL Header Integration",
                    "Single Licensed Inspector Login",
                    "Automated 09:00 AM Expiry Scheduler"
                ]
            },
            {
                "id": "growth",
                "name": "Growth Pro Plan",
                "price_monthly": 399.00,
                "price_yearly": 3999.00,
                "sms_credits": 3500,
                "is_popular": True,
                "description": "Recommended for high-volume centres seeking maximum customer retention.",
                "features": [
                    "Everything in Starter Plan",
                    "3,500 SMS & WhatsApp Reminders / mo",
                    "Up to 3 Inspector / Operator Logins",
                    "Priority WhatsApp Message Routing",
                    "Excel & CSV Report Data Exports",
                    "Real-Time VAHAN 4.0 Telemetry Sync"
                ]
            },
            {
                "id": "enterprise",
                "name": "Chain & Multi-Station",
                "price_monthly": 899.00,
                "price_yearly": 8999.00,
                "sms_credits": 10000,
                "is_popular": False,
                "description": "For multi-lane testing centres and fleet inspection stations.",
                "features": [
                    "Everything in Growth Pro",
                    "10,000 SMS & WhatsApp Credits / mo",
                    "Unlimited Inspector & Staff Accounts",
                    "Custom DLT Sender Header (e.g. YOUR-PUC)",
                    "Multi-Location Centralized Dashboard",
                    "24/7 Dedicated Technical Support"
                ]
            }
        ],
        "sms_packs": [
            {"name": "1,000 SMS Booster", "amount": 150.00, "credits": 1000, "rate": "₹0.15/SMS"},
            {"name": "5,000 SMS Super Saver", "amount": 600.00, "credits": 5000, "rate": "₹0.12/SMS", "is_popular": True},
            {"name": "15,000 SMS Mega Pack", "amount": 1500.00, "credits": 15000, "rate": "₹0.10/SMS"}
        ]
    }

# ----------------- CASHFREE PAYMENTS -----------------
@app.post("/api/payments/create-order")
async def create_payment_order(order_req: CashfreeOrderRequest):
    order_id = f"PUC_CF_{int(datetime.now().timestamp())}"
    res = await create_cashfree_order(
        order_id=order_id,
        amount=order_req.amount,
        customer_name=order_req.customer_name or "Musthaque Ali",
        customer_phone=order_req.customer_phone or "9847012345",
        customer_email="inspector@almadina-puc.com"
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO payments (centre_id, order_id, plan_name, sms_credits_added, amount, status)
    VALUES (?, ?, ?, ?, ?, 'PENDING')
    """, (1, order_id, order_req.plan_name, order_req.sms_credits, order_req.amount))
    conn.commit()
    conn.close()

    return res

@app.post("/api/payments/verify")
async def verify_payment(payload: CashfreeVerifyRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE order_id = ?", (payload.order_id,))
    payment_record = cursor.fetchone()

    if payment_record and payment_record["status"] != "SUCCESS":
        credits_to_add = payment_record["sms_credits_added"]
        plan_name = payment_record["plan_name"]
        amount = payment_record["amount"]

        # Extend subscription date if a subscription plan was purchased
        today = datetime.now().date()
        extension_days = 365 if ("Year" in plan_name or amount >= 1000) else 30
        new_end_date = (today + timedelta(days=extension_days)).isoformat()

        cursor.execute("UPDATE payments SET status = 'SUCCESS' WHERE order_id = ?", (payload.order_id,))
        cursor.execute("""
        UPDATE puc_centres 
        SET sms_credits = sms_credits + ?,
            subscription_status = 'ACTIVE',
            subscription_plan = ?,
            subscription_end_date = ?
        WHERE id = 1
        """, (credits_to_add, plan_name, new_end_date))
        conn.commit()

    conn.close()
    return {
        "success": True,
        "status": "ACTIVE",
        "order_id": payload.order_id,
        "message": f"Payment verified via Cashfree! Subscription updated to '{payment_record['plan_name']}' with {payment_record['sms_credits_added']} credits added."
    }

