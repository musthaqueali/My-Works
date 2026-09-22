import asyncio
import logging
from datetime import datetime, timedelta
from database import get_connection
from notification_service import send_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PUCScheduler")

async def check_and_dispatch_reminders():
    """
    Checks vehicles expiring in <= 7 days or expired, and dispatches automated reminders.
    """
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().date()
    seven_days_later = today + timedelta(days=7)

    cursor.execute("""
    SELECT r.*, c.name as centre_name, c.phone as centre_phone
    FROM puc_records r
    JOIN puc_centres c ON r.centre_id = c.id
    WHERE r.sms_opt_in = 1
    AND date(r.expiry_date) <= date(?)
    """, (seven_days_later.isoformat(),))

    records = cursor.fetchall()
    dispatched_count = 0

    for r in records:
        # Check if already notified today
        cursor.execute("""
        SELECT COUNT(*) FROM notification_logs
        WHERE record_id = ? AND date(sent_at) = date(?)
        """, (r["id"], today.isoformat()))
        if cursor.fetchone()[0] == 0:
            await send_notification(
                centre_id=r["centre_id"],
                record_id=r["id"],
                plate_number=r["plate_number"],
                mobile_number=r["mobile_number"],
                owner_name=r["owner_name"],
                expiry_date=r["expiry_date"],
                channel="SMS"
            )
            dispatched_count += 1

    conn.close()
    logger.info(f"[CRON] Completed daily expiry scan. Reminders dispatched: {dispatched_count}")
    return {"dispatched_count": dispatched_count, "timestamp": datetime.now().isoformat()}

async def start_scheduler_loop():
    """
    Runs in background every 24 hours (or triggers daily check).
    """
    while True:
        try:
            await check_and_dispatch_reminders()
        except Exception as e:
            logger.error(f"[CRON ERROR] {e}")
        # Sleep for 24 hours (86400 seconds)
        await asyncio.sleep(86400)
