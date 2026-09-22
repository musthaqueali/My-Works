import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "subscribers.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newsletter_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_number INTEGER,
                title TEXT,
                subject TEXT,
                content_markdown TEXT,
                content_html TEXT,
                status TEXT DEFAULT 'draft',
                recipient_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP
            )
        """)
        conn.commit()

def add_subscriber(email: str, name: Optional[str] = "") -> Dict:
    email = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO subscribers (email, name, status) VALUES (?, ?, 'active')",
                (email, name.strip() if name else "")
            )
            conn.commit()
            return {"success": True, "message": "Subscribed successfully!", "email": email}
        except sqlite3.IntegrityError:
            # Check if reactivating an unsubscribed user
            cursor.execute("SELECT status FROM subscribers WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row and row["status"] != "active":
                cursor.execute("UPDATE subscribers SET status = 'active' WHERE email = ?", (email,))
                conn.commit()
                return {"success": True, "message": "Subscription reactivated!", "email": email}
            return {"success": False, "message": "This email is already subscribed.", "email": email}

def get_subscribers(status: Optional[str] = None) -> List[Dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM subscribers WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM subscribers ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def remove_subscriber(email: str) -> bool:
    email = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE subscribers SET status = 'unsubscribed' WHERE email = ?", (email,))
        conn.commit()
        return cursor.rowcount > 0

def delete_subscriber(subscriber_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subscribers WHERE id = ?", (subscriber_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_stats() -> Dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM subscribers WHERE status = 'active'")
        active = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as total FROM subscribers WHERE status = 'unsubscribed'")
        unsub = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as total FROM newsletter_issues WHERE status = 'sent'")
        issues_sent = cursor.fetchone()["total"]
        return {
            "active_subscribers": active,
            "unsubscribed": unsub,
            "total_issues_sent": issues_sent
        }

def save_draft_issue(title: str, subject: str, content_markdown: str, content_html: str) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(issue_number) as max_num FROM newsletter_issues")
        max_num = cursor.fetchone()["max_num"] or 0
        issue_number = max_num + 1
        
        cursor.execute("""
            INSERT INTO newsletter_issues (issue_number, title, subject, content_markdown, content_html, status)
            VALUES (?, ?, ?, ?, ?, 'draft')
        """, (issue_number, title, subject, content_markdown, content_html))
        conn.commit()
        return cursor.lastrowid

def mark_issue_sent(issue_id: int, recipient_count: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE newsletter_issues 
            SET status = 'sent', sent_at = CURRENT_TIMESTAMP, recipient_count = ?
            WHERE id = ?
        """, (recipient_count, issue_id))
        conn.commit()

# Initialize upon module load
init_db()
