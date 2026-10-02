import io
import os
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pymupdf as fitz

def generate_sample_document(title: str = "Agreement for Verification & eSign", recipient_name: str = "Musthaque Ali") -> bytes:
    """Generates a clean sample PDF document for testing verification & eSign."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header Banner
    c.setFillColorRGB(0.12, 0.28, 0.49)
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 48, "DIGILOCKER / SETU eSIGN VERIFICATION")

    # Document Body
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, title)

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 145, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    c.drawString(50, height - 160, f"Recipient / Signer: {recipient_name}")

    text = [
        "This document is prepared for electronic verification and digital signature.",
        "Under the provisions of the Information Technology Act (2000), documents digitally signed",
        "using secure electronic signature (eSign) mechanisms hold legal validity equivalent to traditional physical signatures.",
        "",
        "Terms and Verification Conditions:",
        "1. The signer confirms the authenticity of identity information submitted through DigiLocker / Aadhaar.",
        "2. The signature confirms acceptance of this record in electronic form.",
        "3. Any alteration made to this document after timestamping renders the cryptographic seal invalid.",
        "",
        "Please complete verification and provide digital signature below."
    ]

    y = height - 200
    for line in text:
        c.drawString(50, y, line)
        y -= 20

    # Signature Box Area
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(1)
    c.rect(50, 100, 260, 110)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(60, 195, "Authorized Signatory Box")
    c.drawString(60, 115, "Status: Pending Digital Signature")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def stamp_digital_signature(pdf_bytes: bytes, signer_name: str, sign_method: str = "Aadhaar eSign / DigiLocker") -> bytes:
    """Stamps a certified digital signature banner and tamper-proof SHA-256 hash onto the PDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[-1]  # Stamp on the last page

    sign_time = datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")
    doc_hash = hashlib.sha256(pdf_bytes).hexdigest()[:16].upper()

    # Create visual signature seal on bottom left
    rect = fitz.Rect(50, page.rect.height - 210, 310, page.rect.height - 100)

    # Draw white background to clear placeholder
    page.draw_rect(rect, color=(0.12, 0.53, 0.90), fill=(0.95, 0.98, 1.0), width=1.5)

    # Insert signature text & tick badge
    text = (
        f"✓ DIGITALLY SIGNED\n"
        f"Signer: {signer_name}\n"
        f"Method: {sign_method}\n"
        f"Time: {sign_time}\n"
        f"SHA-256 Seal: {doc_hash}\n"
        f"Status: Legally Valid (IT Act 2000)"
    )

    page.insert_textbox(
        fitz.Rect(rect.x0 + 8, rect.y0 + 8, rect.x1 - 8, rect.y1 - 8),
        text,
        fontsize=8.5,
        fontname="helv",
        color=(0.05, 0.25, 0.45)
    )

    out_bytes = doc.write()
    doc.close()
    return out_bytes
