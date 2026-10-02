import os
import uuid
import base64
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

import pdf_signer
import setu_service

load_dotenv()

app = FastAPI(title="DigiLocker & Setu eSign Tool")

# Templates directory
os.makedirs("templates", exist_ok=True)
os.makedirs("storage", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# In-memory document storage
DOCUMENTS = {}

# Pre-populate with a demo document
demo_id = "DOC-DEMO-01"
demo_pdf = pdf_signer.generate_sample_document(
    title="Non-Disclosure & Verification Agreement",
    recipient_name="Musthaque Ali"
)
DOCUMENTS[demo_id] = {
    "id": demo_id,
    "title": "Non-Disclosure & Verification Agreement",
    "recipient_name": "Musthaque Ali",
    "recipient_email": "musthaque@example.com",
    "status": "PENDING",
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "pdf_bytes": demo_pdf,
    "signed_pdf_bytes": None,
    "signed_at": None,
    "method": None,
    "setu_sign_url": None,
    "setu_doc_id": None
}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "documents": list(DOCUMENTS.values()),
            "base_url": base_url,
            "client_id": setu_service.CLIENT_ID,
            "product_instance_id": setu_service.PRODUCT_INSTANCE_ID
        }
    )

@app.post("/api/create-link")
async def create_document(
    request: Request,
    title: str = Form(...),
    recipient_name: str = Form(...),
    recipient_email: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    
    if file and file.filename and file.filename.endswith(".pdf"):
        pdf_bytes = await file.read()
    else:
        pdf_bytes = pdf_signer.generate_sample_document(title=title, recipient_name=recipient_name)

    base_url = str(request.base_url).rstrip("/")
    redirect_url = f"{base_url}/verify/{doc_id}"

    # Try creating Setu eSign request if credentials are functional
    setu_doc_id = None
    setu_sign_url = None
    
    upload_res = setu_service.upload_document_to_setu(pdf_bytes, f"{doc_id}.pdf")
    if upload_res.get("success"):
        setu_doc_id = upload_res["data"].get("id")
        req_res = setu_service.create_setu_signature_request(
            document_id=setu_doc_id,
            signer_name=recipient_name,
            signer_identifier=recipient_email,
            redirect_url=redirect_url
        )
        if req_res.get("success"):
            setu_sign_url = req_res["data"].get("url")

    DOCUMENTS[doc_id] = {
        "id": doc_id,
        "title": title,
        "recipient_name": recipient_name,
        "recipient_email": recipient_email,
        "status": "PENDING",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pdf_bytes": pdf_bytes,
        "signed_pdf_bytes": None,
        "signed_at": None,
        "method": None,
        "setu_sign_url": setu_sign_url,
        "setu_doc_id": setu_doc_id
    }

    return RedirectResponse(url="/", status_code=303)

@app.get("/sign/{doc_id}", response_class=HTMLResponse)
async def sign_page(request: Request, doc_id: str):
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    base_url = str(request.base_url).rstrip("/")
    pdf_base64 = base64.b64encode(doc["pdf_bytes"]).decode("utf-8")

    return templates.TemplateResponse(
        request=request,
        name="sign.html",
        context={
            "doc": doc,
            "base_url": base_url,
            "pdf_base64": pdf_base64,
            "has_setu_url": bool(doc.get("setu_sign_url"))
        }
    )

@app.post("/api/complete-sign/{doc_id}")
async def complete_sign(doc_id: str, method: str = Form("Aadhaar eSign")):
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Stamp the certified digital signature on the PDF
    signed_bytes = pdf_signer.stamp_digital_signature(
        doc["pdf_bytes"],
        signer_name=doc["recipient_name"],
        sign_method=f"DigiLocker / {method}"
    )

    doc["status"] = "SIGNED"
    doc["signed_pdf_bytes"] = signed_bytes
    doc["signed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    doc["method"] = method

    return RedirectResponse(url=f"/verify/{doc_id}", status_code=303)

@app.get("/verify/{doc_id}", response_class=HTMLResponse)
async def verify_page(request: Request, doc_id: str):
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_to_show = doc["signed_pdf_bytes"] if doc["status"] == "SIGNED" else doc["pdf_bytes"]
    pdf_base64 = base64.b64encode(pdf_to_show).decode("utf-8")

    return templates.TemplateResponse(
        request=request,
        name="verify.html",
        context={
            "doc": doc,
            "pdf_base64": pdf_base64
        }
    )

@app.get("/download/{doc_id}")
async def download_pdf(doc_id: str):
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    content = doc["signed_pdf_bytes"] if doc["status"] == "SIGNED" else doc["pdf_bytes"]
    filename = f"{doc_id}_{'signed' if doc['status'] == 'SIGNED' else 'original'}.pdf"

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/test-credentials")
async def test_credentials():
    """Diagnostic endpoint to test Setu credentials status."""
    import requests
    headers = setu_service.get_headers()
    try:
        r = requests.get(f"{setu_service.BASE_URL}/api/health", headers=headers, timeout=10)
        return {
            "sandbox_url": setu_service.BASE_URL,
            "status_code": r.status_code,
            "response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text,
            "client_id": setu_service.CLIENT_ID[:8] + "...",
            "has_product_instance_id": bool(setu_service.PRODUCT_INSTANCE_ID)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
