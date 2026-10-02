import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SETU_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("SETU_CLIENT_SECRET", "").strip()
PRODUCT_INSTANCE_ID = os.getenv("SETU_PRODUCT_INSTANCE_ID", "").strip()
ENV = os.getenv("SETU_ENV", "sandbox").strip().lower()

BASE_URL = "https://dg-sandbox.setu.co" if ENV == "sandbox" else "https://dg.setu.co"

def get_headers() -> dict:
    headers = {
        "x-client-id": CLIENT_ID,
        "x-client-secret": CLIENT_SECRET,
    }
    if PRODUCT_INSTANCE_ID:
        headers["x-product-instance-id"] = PRODUCT_INSTANCE_ID
    return headers

def upload_document_to_setu(pdf_bytes: bytes, filename: str = "document.pdf") -> dict:
    """Uploads a PDF document to Setu for eSigning."""
    url = f"{BASE_URL}/api/documents"
    headers = get_headers()
    files = {
        "document": (filename, pdf_bytes, "application/pdf")
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, timeout=15)
        return {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_setu_signature_request(document_id: str, signer_name: str, signer_identifier: str, redirect_url: str) -> dict:
    """Creates an Aadhaar eSign signature request link via Setu."""
    url = f"{BASE_URL}/api/signature-requests"
    headers = get_headers()
    headers["Content-Type"] = "application/json"
    
    payload = {
        "documentId": document_id,
        "redirectUrl": redirect_url,
        "signers": [
            {
                "identifier": signer_identifier,
                "displayName": signer_name,
                "signaturePositions": [
                    {
                        "page": 1,
                        "x": 50,
                        "y": 100
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        return {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_setu_digilocker_request(redirect_url: str) -> dict:
    """Creates a DigiLocker document verification / consent link via Setu."""
    url = f"{BASE_URL}/api/digilocker"
    headers = get_headers()
    headers["Content-Type"] = "application/json"
    
    payload = {
        "redirectUrl": redirect_url
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        return {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
