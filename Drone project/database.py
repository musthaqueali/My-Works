import sqlite3
import os
from datetime import datetime, timedelta
import openpyxl

DB_FILE = os.getenv("DATABASE_FILE", "puc_desk.db")
EXCEL_PATH = r"C:\Users\musthaque.mayalankot\Downloads\PUC_100_People_Dummy_Data_With_Validity (1).xlsx"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reload=False):
    conn = get_connection()
    cursor = conn.cursor()

    if force_reload:
        cursor.execute("DROP TABLE IF EXISTS puc_records")
        cursor.execute("DROP TABLE IF EXISTS puc_centres")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_id TEXT UNIQUE,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        name TEXT NOT NULL,
        picture TEXT,
        centre_id INTEGER DEFAULT 1,
        role TEXT DEFAULT 'OPERATOR',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Ensure password_hash exists if table was created previously
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [r[1] for r in cursor.fetchall()]
    if "password_hash" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS puc_centres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE,
        owner_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        sms_credits INTEGER DEFAULT 3420,
        subscription_status TEXT DEFAULT 'ACTIVE',
        subscription_plan TEXT DEFAULT '₹150/Month Basic',
        subscription_end_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("PRAGMA table_info(puc_centres)")
    centre_cols = [r[1] for r in cursor.fetchall()]
    if "subscription_end_date" not in centre_cols:
        cursor.execute("ALTER TABLE puc_centres ADD COLUMN subscription_end_date TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS puc_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        centre_id INTEGER NOT NULL DEFAULT 1,
        owner_name TEXT NOT NULL,
        plate_number TEXT NOT NULL,
        mobile_number TEXT NOT NULL,
        issue_date TEXT NOT NULL,
        expiry_date TEXT NOT NULL,
        validity_period TEXT DEFAULT '1 Year',
        fee_amount REAL DEFAULT 60.00,
        sms_opt_in INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notification_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        centre_id INTEGER NOT NULL DEFAULT 1,
        record_id INTEGER,
        plate_number TEXT NOT NULL,
        mobile_number TEXT NOT NULL,
        channel TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'SENT',
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        centre_id INTEGER NOT NULL DEFAULT 1,
        order_id TEXT NOT NULL UNIQUE,
        plan_name TEXT NOT NULL,
        amount REAL NOT NULL,
        sms_credits_added INTEGER DEFAULT 0,
        status TEXT DEFAULT 'PENDING',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check centre record
    cursor.execute("SELECT COUNT(*) FROM puc_centres")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO puc_centres (name, code, owner_name, phone, sms_credits, subscription_status, subscription_plan)
        VALUES ('Al-Madina Testing Station', 'KL-11-PUC-408', 'Musthaque Ali', '9847012345', 3420, 'ACTIVE', '₹150/Month Basic')
        """)

    # Populate 100 records from the user's Excel file
    cursor.execute("SELECT COUNT(*) FROM puc_records")
    existing_count = cursor.fetchone()[0]

    if existing_count == 0 or force_reload:
        cursor.execute("DELETE FROM puc_records")
        today = datetime.now().date()
        
        if os.path.exists(EXCEL_PATH):
            wb = openpyxl.load_workbook(EXCEL_PATH)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))[1:] # skip header

            records_to_insert = []
            for i, r in enumerate(rows):
                name = str(r[0]).strip() if r[0] else f"Customer {i+1}"
                plate = str(r[1]).strip().upper() if r[1] else f"KL11AZ{1000+i}"
                phone = str(r[2]).strip().replace(".0", "") if r[2] else "9847000000"
                
                # Parse dates
                cert_val = r[3]
                exp_val = r[4]
                validity = str(r[5]).strip() if len(r) > 5 and r[5] else "1 Year"

                # To demonstrate the user's specific requirement:
                # "sorting like expiring one week or expiring in one day"
                # We align a few records to today's date so the operator immediately sees live data for these filters:
                if i in (0, 1):
                    # Expiring in 1 Day (Tomorrow)
                    exp_date = today + timedelta(days=1)
                    cert_date = exp_date - timedelta(days=365)
                elif i in (2, 3, 4, 5, 6):
                    # Expiring in 1 Week (in 3 to 6 days)
                    exp_date = today + timedelta(days=i+1)
                    cert_date = exp_date - timedelta(days=365)
                elif i in (7, 8, 9):
                    # Expired (1 to 3 days ago)
                    exp_date = today - timedelta(days=i-6)
                    cert_date = exp_date - timedelta(days=365)
                else:
                    # Keep original expiry from Excel or standard 2027 date
                    if isinstance(exp_val, datetime):
                        exp_date = exp_val.date()
                    elif isinstance(exp_val, str) and exp_val[:10].replace("-", "").isdigit():
                        exp_date = datetime.strptime(exp_val[:10], "%Y-%m-%d").date()
                    else:
                        exp_date = today + timedelta(days=180 + i)

                    if isinstance(cert_val, datetime):
                        cert_date = cert_val.date()
                    elif isinstance(cert_val, str) and cert_val[:10].replace("-", "").isdigit():
                        cert_date = datetime.strptime(cert_val[:10], "%Y-%m-%d").date()
                    else:
                        cert_date = exp_date - timedelta(days=365)

                records_to_insert.append((
                    1, name, plate, phone,
                    cert_date.isoformat(), exp_date.isoformat(),
                    validity, 60.00, 1
                ))

            cursor.executemany("""
            INSERT INTO puc_records (
                centre_id, owner_name, plate_number, mobile_number,
                issue_date, expiry_date, validity_period, fee_amount, sms_opt_in
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records_to_insert)
            print(f"Successfully loaded {len(records_to_insert)} records from Excel.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db(force_reload=True)
    print("Database reloaded with Excel records.")
