"""
Billing & Subscription Module for 'I LOVE FILES' SaaS
Powered by Cashfree Payments Gateway (India & Global Cards, UPI, NetBanking).
Zero fixed monthly cost: pay-as-you-grow standard transaction fees only.
Includes seamless test sandbox integration and 1-click fallback.
"""
import os
import time
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
import httpx

import database
from auth import get_current_user, get_current_user_optional

logger = logging.getLogger("ILoveFiles.Billing")

# ---------------------------------------------------------------------
# Cashfree Configuration (.env or Environment Variables)
# ---------------------------------------------------------------------
CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID", "").strip()
CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY", "").strip()
CASHFREE_ENV = os.environ.get("CASHFREE_ENV", "TEST").strip().upper()

IS_SANDBOX = CASHFREE_ENV in ("TEST", "SANDBOX")
CASHFREE_BASE_URL = "https://sandbox.cashfree.com/pg" if IS_SANDBOX else "https://api.cashfree.com/pg"

# Standard SaaS Tier Prices in INR (₹)
PRICE_PRO_MONTHLY = float(os.environ.get("CASHFREE_PRICE_PRO_MONTHLY", "499"))
PRICE_PRO_ANNUAL = float(os.environ.get("CASHFREE_PRICE_PRO_ANNUAL", "3999"))
PRICE_ENTERPRISE_MONTHLY = float(os.environ.get("CASHFREE_PRICE_ENTERPRISE_MONTHLY", "1999"))
PRICE_ENTERPRISE_ANNUAL = float(os.environ.get("CASHFREE_PRICE_ENTERPRISE_ANNUAL", "15999"))

router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])

class CheckoutRequest(BaseModel):
    tier: str = "pro"       # "pro" or "enterprise"
    interval: str = "month" # "month" or "year"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class DemoUpgradeRequest(BaseModel):
    tier: str = "pro"

# ---------------------------------------------------------------------
# Plans Information Endpoint
# ---------------------------------------------------------------------
@router.get("/plans")
def get_pricing_plans():
    return {
        "currency": "INR",
        "symbol": "₹",
        "provider": "Cashfree Payments",
        "is_sandbox": IS_SANDBOX,
        "app_id_configured": bool(CASHFREE_APP_ID),
        "plans": [
            {
                "id": "free",
                "name": "Free Starter",
                "price_monthly": 0,
                "price_annual": 0,
                "description": "Essential file conversion and compression for daily light use.",
                "features": [
                    "5 free conversions / day",
                    "Max file size: 25 MB",
                    "All 45+ file formats supported",
                    "Standard conversion queue",
                    "100% Private local processing"
                ],
                "cta": "Current Plan",
                "popular": False
            },
            {
                "id": "pro",
                "name": "Pro Professional",
                "price_monthly": PRICE_PRO_MONTHLY,
                "price_annual": PRICE_PRO_ANNUAL,
                "savings": "Save 33%",
                "description": "Unrestricted CAD, PDF prepress & media conversions for engineers.",
                "features": [
                    "Unlimited conversions / day",
                    "Max file size: 500 MB",
                    "AutoCAD DWG/DXF Batch Plotting Studio",
                    "Custom CTB Plot Style Tables",
                    "Ultra-HD 600 DPI Print Vectors",
                    "PDF Redaction & AES-256 Encryption",
                    "Fast Priority Processing Queue",
                    "Developer REST API Access & Key"
                ],
                "cta": "Upgrade to Pro",
                "popular": True
            },
            {
                "id": "enterprise",
                "name": "Enterprise / Teams",
                "price_monthly": PRICE_ENTERPRISE_MONTHLY,
                "price_annual": PRICE_ENTERPRISE_ANNUAL,
                "savings": "Save 33%",
                "description": "Designed for engineering departments and high-volume operations.",
                "features": [
                    "Everything included in Pro",
                    "Unlimited file size processing",
                    "Dedicated conversion workers",
                    "Custom CTB font & xref auto-loading",
                    "Automated Webhook callbacks",
                    "99.9% Uptime SLA guarantee",
                    "Direct priority developer support"
                ],
                "cta": "Choose Enterprise",
                "popular": False
            }
        ]
    }

# ---------------------------------------------------------------------
# Create Cashfree Checkout Order Session
# ---------------------------------------------------------------------
@router.post("/create-checkout-session")
def create_checkout_session(req: CheckoutRequest, request: Request, user: Dict[str, Any] = Depends(get_current_user)):
    base_url = str(request.base_url).rstrip("/")
    tier = req.tier.lower() if req.tier else "pro"
    interval = req.interval.lower() if req.interval else "month"

    # Determine amount in INR
    if tier == "enterprise":
        amount = PRICE_ENTERPRISE_ANNUAL if interval in ("year", "annual") else PRICE_ENTERPRISE_MONTHLY
    else:
        amount = PRICE_PRO_ANNUAL if interval in ("year", "annual") else PRICE_PRO_MONTHLY

    order_id = f"ilf_{uuid.uuid4().hex[:12]}"
    clean_user_id = user["id"].replace("-", "")[:20]

    # Cashfree API Call
    if CASHFREE_APP_ID and CASHFREE_SECRET_KEY:
        try:
            headers = {
                "x-client-id": CASHFREE_APP_ID,
                "x-client-secret": CASHFREE_SECRET_KEY,
                "x-api-version": "2023-08-01",
                "Content-Type": "application/json"
            }
            order_payload = {
                "order_id": order_id,
                "order_amount": float(amount),
                "order_currency": "INR",
                "customer_details": {
                    "customer_id": f"cust_{clean_user_id}",
                    "customer_email": user["email"],
                    "customer_phone": "9999999999",
                    "customer_name": user.get("full_name") or user["email"].split("@")[0]
                },
                "order_meta": {
                    "return_url": f"{base_url}/?order_id={order_id}&checkout=cashfree_return",
                    "notify_url": f"{base_url}/api/billing/cashfree-webhook"
                },
                "order_note": f"I LOVE FILES {tier.upper()} ({interval})"
            }

            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{CASHFREE_BASE_URL}/orders", headers=headers, json=order_payload)
                
            if resp.status_code in (200, 201):
                order_data = resp.json()
                payment_session_id = order_data.get("payment_session_id")
                
                # Save pending order to user record
                database.update_user_subscription(
                    user_id=user["id"],
                    tier=user.get("tier", "free"),
                    cashfree_order_id=order_id,
                    cashfree_customer_id=f"cust_{clean_user_id}",
                    subscription_status="pending"
                )

                return {
                    "mode": "cashfree",
                    "environment": "sandbox" if IS_SANDBOX else "production",
                    "payment_session_id": payment_session_id,
                    "order_id": order_id,
                    "tier": tier,
                    "amount": amount,
                    "currency": "INR"
                }
            else:
                logger.error(f"Cashfree order creation error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Exception calling Cashfree API: {e}")

    # Fallback to Demo Mode if Cashfree credentials are empty or unreachable
    logger.info("Cashfree unavailable or demo fallback invoked.")
    end_timestamp = int(time.time()) + (365 * 86400 if interval in ("year", "annual") else 30 * 86400)
    database.update_user_subscription(
        user_id=user["id"],
        tier=tier,
        cashfree_order_id=order_id,
        subscription_status="active",
        current_period_end=end_timestamp
    )
    return {
        "mode": "demo",
        "tier": tier,
        "message": f"Demo Mode: Upgraded to {tier.upper()} plan for free testing."
    }

# ---------------------------------------------------------------------
# Verify Cashfree Payment
# ---------------------------------------------------------------------
@router.get("/verify-payment")
def verify_cashfree_payment(order_id: str, request: Request, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID is required.")

    # Target user can be authenticated session or matched by cashfree_order_id
    target_user = user
    if not target_user:
        with database.get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE cashfree_order_id = ?", (order_id,)).fetchone()
            if row:
                target_user = dict(row)

    if not target_user:
        raise HTTPException(status_code=404, detail="User account matching this order was not found.")

    # Inquire order status directly from Cashfree API
    is_paid = False
    order_data = {}
    if CASHFREE_APP_ID and CASHFREE_SECRET_KEY:
        try:
            headers = {
                "x-client-id": CASHFREE_APP_ID,
                "x-client-secret": CASHFREE_SECRET_KEY,
                "x-api-version": "2023-08-01"
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{CASHFREE_BASE_URL}/orders/{order_id}", headers=headers)
            if resp.status_code == 200:
                order_data = resp.json()
                status = order_data.get("order_status")
                if status == "PAID":
                    is_paid = True
                elif IS_SANDBOX and status == "ACTIVE":
                    # In sandbox testing environment, allow test verification
                    is_paid = True
        except Exception as e:
            logger.error(f"Error checking Cashfree order {order_id}: {e}")

    if is_paid:
        end_timestamp = int(time.time()) + (30 * 86400)
        database.update_user_subscription(
            user_id=target_user["id"],
            tier="pro",
            cashfree_order_id=order_id,
            subscription_status="active",
            current_period_end=end_timestamp
        )
        return {
            "status": "success",
            "tier": "pro",
            "order_id": order_id,
            "message": "Payment verified! Your account is now upgraded to PRO."
        }
    else:
        return {
            "status": "pending",
            "order_id": order_id,
            "order_status": order_data.get("order_status", "UNKNOWN"),
            "message": "Payment is not yet confirmed by Cashfree."
        }

def sync_user_subscription_status(user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Ensures user subscription state in SQLite is 100% synchronized:
    1. Checks if an active subscription has expired, downgrading to free.
    2. Reconciles any pending or existing Cashfree order with the Cashfree API.
    3. Automatically upgrades and persists PRO tier if payment is confirmed or active in sandbox.
    """
    if not user or not user.get("id"):
        return user

    user_id = user["id"]
    now_ts = int(time.time())
    updated = False

    # 1. Check expiration
    period_end = user.get("current_period_end")
    if period_end and period_end < now_ts and user.get("tier", "free") != "free":
        database.update_user_subscription(
            user_id=user_id,
            tier="free",
            subscription_status="expired"
        )
        updated = True

    # 2. Check pending or unconfirmed Cashfree order
    order_id = user.get("cashfree_order_id")
    if order_id and (user.get("tier") == "free" or user.get("subscription_status") == "pending"):
        if CASHFREE_APP_ID and CASHFREE_SECRET_KEY:
            try:
                headers = {
                    "x-client-id": CASHFREE_APP_ID,
                    "x-client-secret": CASHFREE_SECRET_KEY,
                    "x-api-version": "2023-08-01"
                }
                with httpx.Client(timeout=8.0) as client:
                    resp = client.get(f"{CASHFREE_BASE_URL}/orders/{order_id}", headers=headers)
                if resp.status_code == 200:
                    order_data = resp.json()
                    status = order_data.get("order_status")
                    if status == "PAID" or (IS_SANDBOX and status == "ACTIVE"):
                        new_period_end = now_ts + (30 * 86400)
                        database.update_user_subscription(
                            user_id=user_id,
                            tier="pro",
                            cashfree_order_id=order_id,
                            subscription_status="active",
                            current_period_end=new_period_end
                        )
                        updated = True
                        logger.info(f"Auto-synced and activated Pro tier for user {user.get('email')} (Order {order_id})")
            except Exception as e:
                logger.warning(f"Error checking Cashfree order during sync: {e}")

    if updated:
        fresh_user = database.get_user_by_id(user_id)
        return fresh_user or user

    return user

# ---------------------------------------------------------------------
# Cashfree Webhook Handler
# ---------------------------------------------------------------------
@router.post("/cashfree-webhook")
async def cashfree_webhook(request: Request):
    try:
        payload = await request.json()
        data = payload.get("data", {})
        order = data.get("order", {})
        order_id = order.get("order_id") or data.get("order_id") or payload.get("order_id")
        event_type = payload.get("type", "")

        if "PAYMENT_SUCCESS" in event_type or order.get("order_status") == "PAID":
            if order_id:
                with database.get_connection() as conn:
                    row = conn.execute("SELECT * FROM users WHERE cashfree_order_id = ?", (order_id,)).fetchone()
                    if row:
                        end_timestamp = int(time.time()) + (30 * 86400)
                        database.update_user_subscription(
                            user_id=row["id"],
                            tier="pro",
                            subscription_status="active",
                            current_period_end=end_timestamp
                        )
                        logger.info(f"Webhook upgraded user {row['email']} to Pro for order {order_id}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error", "detail": str(e)}

# ---------------------------------------------------------------------
# Demo Toggle / Customer Portal
# ---------------------------------------------------------------------
@router.post("/customer-portal")
def create_customer_portal(request: Request, user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "status": "active",
        "tier": user["tier"],
        "message": f"Your current plan: {user['tier'].upper()}. Payments are managed securely via Cashfree."
    }

@router.post("/demo-toggle-tier")
def demo_toggle_tier(req: DemoUpgradeRequest, user: Dict[str, Any] = Depends(get_current_user)):
    new_tier = req.tier.lower()
    status = "active" if new_tier in ("pro", "enterprise") else "none"
    period_end = int(time.time()) + (30 * 86400) if new_tier in ("pro", "enterprise") else None
    database.update_user_subscription(
        user_id=user["id"],
        tier=new_tier,
        subscription_status=status,
        current_period_end=period_end
    )
    return {"status": "success", "tier": new_tier, "message": f"Account tier updated to {new_tier.upper()}."}
