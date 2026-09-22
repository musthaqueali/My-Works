import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    NEWSLETTER_NAME = os.getenv("NEWSLETTER_NAME", "ELECTRON")
    NEWSLETTER_TAGLINE = os.getenv("NEWSLETTER_TAGLINE", "The Daily Intelligence Broadsheet: Artificial Intelligence, Reliability & Energy Infrastructure")
    
    # Email settings: "simulation", "smtp", or "resend"
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "simulation").lower()
    
    # SMTP Configuration (Gmail, Outlook, etc.)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # Resend API Configuration
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    
    # Sender details
    FROM_EMAIL = os.getenv("FROM_EMAIL", "editor@electron-gazette.com")
    FROM_NAME = os.getenv("FROM_NAME", "ELECTRON Gazette")
    
    # Automated Daily Scheduler
    AUTO_SCHEDULE_ENABLED = os.getenv("AUTO_SCHEDULE_ENABLED", "true").lower() == "true"
    DAILY_SEND_HOUR = int(os.getenv("DAILY_SEND_HOUR", 8)) # 08:00 AM
    DAILY_SEND_MINUTE = int(os.getenv("DAILY_SEND_MINUTE", 0))

    # X / Twitter API Credentials
    X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY", "lGpbgxWRQZcp98Y5uQT7Ouk8l")
    X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET", "vXAj9buGRQlEla1nCr9jUJTHVBNch9cORlOVW5kdfMglq0C9Wq")
    X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "AAAAAAAAAAAAAAAAAAAAANB9%2FgEAAAAA5M7IC45pibXJYIOWEB0e6fvDaww%3DiEFfYWo9fYqomK56tKE0pHxnk5wyE3dzhGFQyZAVhV8uKPAyRq")

config = Config()
