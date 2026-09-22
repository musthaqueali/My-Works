import os
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional
from database import get_connection

SMS_API_KEY = os.getenv("SMS_API_KEY", "")
SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "AIRPOL-KL")

def generate_reminder_message(plate_number: str, owner_name: str, expiry_date: str, centre_name: str = "Al-Madina Testing Station", phone: str = "9847012345") -> str:
    return (
        f"Dear {owner_name}, the Pollution Under Control (PUC) certificate for vehicle {plate_number} "
        f"expires on {expiry_date}. Please visit {centre_name} for a fast renewal to avoid traffic fines. "
        f"Contact: {phone}. - {SMS_SENDER_ID}"
    )

def generate_whatsapp_url(mobile_number: str, message: str) -> str:
    clean_mobile = mobile_number.replace("+", "").replace(" ", "").replace("-", "")
    if len(clean_mobile) == 10:
        clean_mobile = "91" + clean_mobile
    encoded_text = urllib.parse.quote(message)
    return f"https://wa.me/{clean_mobile}?text={encoded_text}"

async def send_notification(
    centre_id: int,
    record_id: Optional[int],
    plate_number: str,
    mobile_number: str,
    owner_name: str,
    expiry_date: str,
    channel: str = "SMS"
) -> Dict[str, Any]:
    message = generate_reminder_message(plate_number, owner_name, expiry_date)
    conn = get_connection()
    cursor = conn.cursor()

    status = "DELIVERED"
    if channel.upper() == "SMS":
        # Deduct 1 credit if available
        cursor.execute("SELECT sms_credits FROM puc_centres WHERE id = ?", (centre_id,))
        row = cursor.fetchone()
        current_credits = row["sms_credits"] if row else 0
        if current_credits > 0:
            cursor.execute("UPDATE puc_centres SET sms_credits = sms_credits - 1 WHERE id = ?", (centre_id,))
            status = "DELIVERED"
        else:
            status = "LOW_CREDIT"

    cursor.execute("""
    INSERT INTO notification_logs (centre_id, record_id, plate_number, mobile_number, channel, message, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (centre_id, record_id, plate_number, mobile_number, channel.upper(), message, status))

    conn.commit()
    conn.close()

    wa_url = generate_whatsapp_url(mobile_number, message)

    return {
        "success": True if status == "DELIVERED" else False,
        "channel": channel.upper(),
        "plate_number": plate_number,
        "mobile_number": mobile_number,
        "status": status,
        "whatsapp_url": wa_url,
        "message": message
    }
