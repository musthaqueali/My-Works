"""
Database Module for 'I LOVE FILES' SaaS
Lightweight, ultra-fast embedded SQLite database with WAL mode.
Zero cloud costs, zero external database servers required.
"""
import os
import sqlite3
import datetime
import uuid
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("ILoveFiles.DB")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "ilovefiles.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrent read/write throughput
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Initializes the database schema if not already present."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            tier TEXT DEFAULT 'free',           -- 'free', 'pro', 'enterprise'
            cashfree_customer_id TEXT,
            cashfree_order_id TEXT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            subscription_status TEXT DEFAULT 'none', -- 'active', 'past_due', 'canceled', 'none'
            current_period_end INTEGER,        -- Unix timestamp
            daily_usage_count INTEGER DEFAULT 0,
            last_usage_date TEXT,              -- YYYY-MM-DD
            api_key TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Dynamic migration for existing databases
        columns = [col[1] for col in cursor.execute("PRAGMA table_info(users)").fetchall()]
        if "cashfree_customer_id" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN cashfree_customer_id TEXT;")
        if "cashfree_order_id" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN cashfree_order_id TEXT;")
        if "google_id" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT;")
        if "avatar_url" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT;")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_cf_cust ON users(cashfree_customer_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_cf_order ON users(cashfree_order_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);")

        # 2. Daily IP Guest Usage table (for anonymous non-registered visitors)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS guest_usage (
            ip_address TEXT PRIMARY KEY,
            daily_usage_count INTEGER DEFAULT 0,
            last_usage_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. Conversion history / usage log (for auditing and user dashboard)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversion_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            ip_address TEXT,
            operation TEXT NOT NULL,
            source_filename TEXT,
            target_format TEXT,
            file_size_bytes INTEGER,
            duration_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """)
        
        conn.commit()
    logger.info(f"SQLite database initialized at {DB_PATH}")

# Call init_db on import
init_db()

# =====================================================================
# USER DATA OPERATIONS
# =====================================================================

def create_user(email: str, hashed_password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
    user_id = str(uuid.uuid4())
    api_key = f"ilf_{uuid.uuid4().hex}"
    today_str = datetime.date.today().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, tier, daily_usage_count, last_usage_date, api_key)
            VALUES (?, ?, ?, ?, 'free', 0, ?, ?)
        """, (user_id, email.lower().strip(), hashed_password, full_name or "", today_str, api_key))
        conn.commit()
        
    return get_user_by_id(user_id)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
    return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
        if row:
            return dict(row)
    return None

def get_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE api_key = ?", (api_key.strip(),)).fetchone()
        if row:
            return dict(row)
    return None

def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id.strip(),)).fetchone()
        if row:
            return dict(row)
    return None

def create_or_update_google_user(
    email: str,
    google_id: str,
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new user via Google Sign-In or links Google ID to existing account."""
    clean_email = email.lower().strip()
    existing = get_user_by_email(clean_email) or get_user_by_google_id(google_id)
    
    if existing:
        with get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET google_id = COALESCE(?, google_id),
                    avatar_url = COALESCE(?, avatar_url),
                    full_name = CASE WHEN full_name IS NULL OR full_name = '' THEN ? ELSE full_name END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (google_id, avatar_url, full_name, existing["id"]))
            conn.commit()
        return get_user_by_id(existing["id"])
        
    # Brand new Google user: auto-create account
    user_id = str(uuid.uuid4())
    api_key = f"ilf_{uuid.uuid4().hex}"
    today_str = datetime.date.today().isoformat()
    dummy_hash = f"oauth_google_{uuid.uuid4().hex}"
    
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, tier, daily_usage_count, last_usage_date, api_key, google_id, avatar_url)
            VALUES (?, ?, ?, ?, 'free', 0, ?, ?, ?, ?)
        """, (user_id, clean_email, dummy_hash, full_name or clean_email.split("@")[0], today_str, api_key, google_id, avatar_url))
        conn.commit()
        
    return get_user_by_id(user_id)

def update_user_subscription(
    user_id: str,
    tier: str,
    cashfree_order_id: Optional[str] = None,
    cashfree_customer_id: Optional[str] = None,
    subscription_status: str = "active",
    current_period_end: Optional[int] = None,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None
) -> bool:
    with get_connection() as conn:
        conn.execute("""
            UPDATE users
            SET tier = ?,
                cashfree_order_id = COALESCE(?, cashfree_order_id),
                cashfree_customer_id = COALESCE(?, cashfree_customer_id),
                stripe_customer_id = COALESCE(?, stripe_customer_id),
                stripe_subscription_id = COALESCE(?, stripe_subscription_id),
                subscription_status = ?,
                current_period_end = COALESCE(?, current_period_end),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (tier, cashfree_order_id, cashfree_customer_id, stripe_customer_id, stripe_subscription_id, subscription_status, current_period_end, user_id))
        conn.commit()
    return True

# =====================================================================
# QUOTA & USAGE MANAGEMENT
# =====================================================================

FREE_USER_DAILY_LIMIT = 5
GUEST_DAILY_LIMIT = 3
MAX_FILE_SIZE_GUEST = 25 * 1024 * 1024     # 25 MB
MAX_FILE_SIZE_FREE = 50 * 1024 * 1024      # 50 MB
MAX_FILE_SIZE_PRO = 500 * 1024 * 1024      # 500 MB

def check_and_increment_quota(user: Optional[Dict[str, Any]], ip_address: str) -> Dict[str, Any]:
    """
    Validates if the user or guest IP is allowed to perform a conversion.
    If allowed, increments the counter and returns {allowed: True, remaining: int, tier: str}.
    If quota exceeded, returns {allowed: False, remaining: 0, limit: int, tier: str}.
    """
    today_str = datetime.date.today().isoformat()

    # 1. Registered User Check
    if user:
        tier = user.get("tier", "free").lower()
        
        # PRO and ENTERPRISE users have UNLIMITED conversions
        if tier in ("pro", "enterprise"):
            return {
                "allowed": True,
                "remaining": -1,  # -1 represents unlimited
                "limit": -1,
                "tier": tier,
                "used_today": user.get("daily_usage_count", 0),
                "max_file_size": MAX_FILE_SIZE_PRO
            }
            
        # Free registered user
        last_date = user.get("last_usage_date")
        current_count = user.get("daily_usage_count", 0)
        
        if last_date != today_str:
            current_count = 0
            
        if current_count >= FREE_USER_DAILY_LIMIT:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": FREE_USER_DAILY_LIMIT,
                "tier": "free",
                "used_today": current_count,
                "max_file_size": MAX_FILE_SIZE_FREE,
                "message": f"You have reached your daily limit of {FREE_USER_DAILY_LIMIT} free tasks. Upgrade to Pro for unlimited conversions!"
            }
            
        # Increment usage
        new_count = current_count + 1
        with get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET daily_usage_count = ?, last_usage_date = ?
                WHERE id = ?
            """, (new_count, today_str, user["id"]))
            conn.commit()
            
        return {
            "allowed": True,
            "remaining": FREE_USER_DAILY_LIMIT - new_count,
            "limit": FREE_USER_DAILY_LIMIT,
            "tier": "free",
            "used_today": new_count,
            "max_file_size": MAX_FILE_SIZE_FREE
        }

    # 2. Anonymous Guest Check (by IP Address)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM guest_usage WHERE ip_address = ?", (ip_address,)).fetchone()
        current_count = 0
        if row:
            if row["last_usage_date"] == today_str:
                current_count = row["daily_usage_count"]
            else:
                current_count = 0
                
        if current_count >= GUEST_DAILY_LIMIT:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": GUEST_DAILY_LIMIT,
                "tier": "guest",
                "used_today": current_count,
                "max_file_size": MAX_FILE_SIZE_GUEST,
                "message": f"You have reached your {GUEST_DAILY_LIMIT} daily guest conversions. Create a free account for more, or upgrade to Pro for unlimited!"
            }
            
        new_count = current_count + 1
        conn.execute("""
            INSERT INTO guest_usage (ip_address, daily_usage_count, last_usage_date)
            VALUES (?, ?, ?)
            ON CONFLICT(ip_address) DO UPDATE SET
                daily_usage_count = excluded.daily_usage_count,
                last_usage_date = excluded.last_usage_date
        """, (ip_address, new_count, today_str))
        conn.commit()

    return {
        "allowed": True,
        "remaining": GUEST_DAILY_LIMIT - new_count,
        "limit": GUEST_DAILY_LIMIT,
        "tier": "guest",
        "used_today": new_count,
        "max_file_size": MAX_FILE_SIZE_GUEST
    }

def get_quota_status(user: Optional[Dict[str, Any]], ip_address: str) -> Dict[str, Any]:
    """Retrieves current quota status without incrementing usage."""
    today_str = datetime.date.today().isoformat()
    if user:
        tier = user.get("tier", "free").lower()
        if tier in ("pro", "enterprise"):
            return {
                "allowed": True,
                "remaining": -1,
                "limit": -1,
                "tier": tier,
                "used_today": user.get("daily_usage_count", 0),
                "max_file_size": MAX_FILE_SIZE_PRO
            }
        
        last_date = user.get("last_usage_date")
        current_count = user.get("daily_usage_count", 0) if last_date == today_str else 0
        remaining = max(0, FREE_USER_DAILY_LIMIT - current_count)
        return {
            "allowed": remaining > 0,
            "remaining": remaining,
            "limit": FREE_USER_DAILY_LIMIT,
            "tier": "free",
            "used_today": current_count,
            "max_file_size": MAX_FILE_SIZE_FREE
        }
    
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM guest_usage WHERE ip_address = ?", (ip_address,)).fetchone()
        current_count = 0
        if row and row["last_usage_date"] == today_str:
            current_count = row["daily_usage_count"]
        remaining = max(0, GUEST_DAILY_LIMIT - current_count)
        return {
            "allowed": remaining > 0,
            "remaining": remaining,
            "limit": GUEST_DAILY_LIMIT,
            "tier": "guest",
            "used_today": current_count,
            "max_file_size": MAX_FILE_SIZE_GUEST
        }

def log_conversion(
    operation: str,
    source_filename: str,
    target_format: str,
    file_size_bytes: int,
    duration_ms: int,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Records conversion activity for auditing and analytics."""
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO conversion_logs (id, user_id, ip_address, operation, source_filename, target_format, file_size_bytes, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), user_id, ip_address, operation, source_filename, target_format, file_size_bytes, duration_ms))
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to log conversion: {e}")
