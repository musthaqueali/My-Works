# ⚡ The AI Dispatch — Automated Newsletter Platform

A complete, production-grade AI Newsletter platform featuring an automated **5-stream research pipeline**, an **Editor-in-Chief LLM synthesis engine**, a **modern web UI** (Reader Landing Page & Admin Studio), and a **pluggable email broadcast dispatcher**.

---

## 🌟 Key Architecture & Capabilities

1. **5 Sourcing Streams (`research_data/`)**:
   - `newsletter_web_research_results.md`: Major industry breakthroughs, funding, and tech moves.
   - `newsletter_ai_products.md`: Top AI tool launches and application updates.
   - `newsletter_github_repos.md`: Trending open-source repositories and open-weights releases.
   - `newsletter_research_papers.md`: Breakthrough arXiv papers explained in plain English.
   - `newsletter_twitter_highlights.md`: Viral debates, engineering takes, and community sentiment.

2. **Synthesis Engine (`pipeline/synthesizer.py`)**:
   - Compiles findings from the 5 streams into a cohesive, high-converting newsletter issue.
   - Generates both clean Markdown and a responsive, bulletproof HTML email.

3. **Modern Web UI (`templates/index.html`)**:
   - **Reader Landing Page**: High-converting subscriber signup page with instant feedback.
   - **Admin Studio**:
     - **Live Email Previewer**: Toggle between Desktop (640px) and Mobile (375px) email simulation.
     - **Research Streams Editor**: In-browser Markdown editor to review and update any of the 5 files in real time.
     - **Subscribers Table**: View, search, add, and remove subscribers.
     - **Delivery Logs**: Real-time event log for test emails and broadcasts.

4. **Pluggable Email Dispatcher (`services/email_service.py`)**:
   - **Simulation Mode** (Default): Logs outgoing emails locally without requiring credentials.
   - **SMTP Mode**: Send via Gmail, Outlook, or corporate mail servers using an App Password.
   - **Resend Mode**: Send via Resend's high-deliverability email API.

---

## 🚀 How to Launch the Application

### Option 1: Double-Click the Launcher
Simply double-click:
```
AI_Newsletter_App\run_app.bat
```

### Option 2: From Terminal
```bash
cd AI_Newsletter_App
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Once running, open your web browser at:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## ⚙️ How to Enable Live Email Sending

Open `.env` in `AI_Newsletter_App/` and configure your preferred provider:

### To Send via Gmail (Free SMTP):
1. In your Google Account, enable 2-Step Verification.
2. Go to **Security > App Passwords** and generate an App Password.
3. In `.env`, set:
   ```env
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_16_digit_app_password
   SMTP_USE_TLS=true
   FROM_EMAIL=your_email@gmail.com
   FROM_NAME="The AI Dispatch"
   ```

### To Send via Resend (Modern API):
1. Sign up at [https://resend.com](https://resend.com) (free 3,000 emails/month).
2. Generate an API Key.
3. In `.env`, set:
   ```env
   EMAIL_PROVIDER=resend
   RESEND_API_KEY=re_1234567890abcdef
   FROM_EMAIL=newsletter@yourverifieddomain.com
   FROM_NAME="The AI Dispatch"
   ```

---

## 📁 Project Structure

```
AI_Newsletter_App/
├── .env                              # Environment configuration (active)
├── .env.example                      # Configuration template
├── database.py                       # SQLite database for subscriber management
├── config.py                         # App configuration
├── main.py                           # FastAPI application & API endpoints
├── requirements.txt                  # Python dependencies
├── run_app.bat                       # One-click startup script
├── pipeline/
│   ├── generator.py                  # Research stream reader & writer
│   └── synthesizer.py                # Master synthesis & HTML builder
├── services/
│   └── email_service.py              # Email dispatcher (Simulation / SMTP / Resend)
├── research_data/                    # The 5 intelligence markdown streams
│   ├── newsletter_ai_products.md
│   ├── newsletter_github_repos.md
│   ├── newsletter_research_papers.md
│   ├── newsletter_twitter_highlights.md
│   └── newsletter_web_research_results.md
├── templates/
│   ├── email_newsletter.html         # Responsive HTML email newsletter template
│   └── index.html                    # Modern Reader Landing & Admin Studio Web UI
└── static/
    ├── css/style.css
    └── js/app.js                     # Interactive dashboard logic
```
