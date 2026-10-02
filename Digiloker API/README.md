# DigiLocker & Aadhaar eSign Verification Tool

This tool generates **shareable document verification and eSign links**. Users can open the link in any browser or mobile device, review the document, and complete electronic signature and verification.

---

## 🔑 Your Setu Credentials

Your credentials from the **Setu Bridge** dashboard have been configured in `.env`:

```ini
SETU_CLIENT_ID=604f367d-7887-4bd4-8eea-57358959380b
SETU_CLIENT_SECRET=94oYruDv98S4XTXDiyIVJtx9g6YDhqFH
SETU_PRODUCT_INSTANCE_ID=
SETU_ENV=sandbox
APP_BASE_URL=http://localhost:8000
```

> **Note on Product Instance ID**:  
> In the Setu Bridge dashboard, right next to the card showing your *Client ID* and *Client Secret*, there is a second card with your **Product Instance ID** (or instance configuration). Copy that ID into `SETU_PRODUCT_INSTANCE_ID` in `.env` to enable direct API requests to Setu's Aadhaar gateway.

---

## 🚀 How to Run the App

1. **Start the local server**:
   ```powershell
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Open the Dashboard**:
   Go to [http://localhost:8000](http://localhost:8000) in your web browser.

---

## 📋 Features

1. **Generate Shareable Links**:
   - Create a new document or upload any custom PDF.
   - Enter the recipient's name and email.
   - Get a unique shareable link (e.g. `http://localhost:8000/sign/DOC-XXXXX`).

2. **Recipient Signing Experience**:
   - The recipient opens the link on desktop or mobile.
   - Live PDF preview inside the browser.
   - IT Act (2000) electronic consent disclaimer.
   - Completes eSign & verification.

3. **Tamper-Proof Verification & Download**:
   - Stamped with a verified **Digital Signature Seal** and **SHA-256 hash**.
   - Download the signed PDF directly.
   - Dedicated `/verify/{doc_id}` certificate page for audits.

---

## 🌐 Making the Link Public (For Real Recipients)

To send the link to someone on WhatsApp, email, or a mobile phone outside your local network, you can use **ngrok** or **Cloudflare Tunnel**:

```powershell
# Using ngrok
ngrok http 8000
```
Then update `APP_BASE_URL` in `.env` with your public ngrok URL (e.g. `https://your-domain.ngrok-free.app`).
