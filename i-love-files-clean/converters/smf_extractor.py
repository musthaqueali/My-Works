"""
SAP SMF (SmartForms / Spool) Drawing Extractor
Extracts embedded engineering drawings, schematics, and graphics from SAP SMF files
into high-resolution TIFF, PNG, or PDF.
"""
import os
import io
import re
import logging
from PIL import Image
import fitz # PyMuPDF

logger = logging.getLogger(__name__)

def extract_smf_drawing(input_path: str, output_path: str, target_format: str) -> bool:
    """
    Extracts embedded engineering drawings from SAP SMF files.
    Supports binary TIFF/BMP streams and ASCII/Hex OTF spool records.
    """
    target_format = target_format.lower().lstrip(".")

    with open(input_path, "rb") as f:
        data = f.read()

    extracted_image = None

    # Strategy 1: Check for direct TIFF header (Little-endian 'II*\x00' or Big-endian 'MM\x00*')
    tiff_idx = data.find(b"II*\x00")
    if tiff_idx == -1:
        tiff_idx = data.find(b"MM\x00*")

    if tiff_idx != -1:
        try:
            stream = io.BytesIO(data[tiff_idx:])
            extracted_image = Image.open(stream)
        except Exception as e:
            logger.warning(f"TIFF header parse failed: {e}")

    # Strategy 2: Check for embedded PDF ('%PDF-')
    if extracted_image is None:
        pdf_idx = data.find(b"%PDF-")
        if pdf_idx != -1:
            try:
                pdf_data = data[pdf_idx:]
                doc = fitz.open(stream=pdf_data, filetype="pdf")
                if target_format == "pdf":
                    with open(output_path, "wb") as out_f:
                        out_f.write(pdf_data)
                    return True
                else:
                    pix = doc[0].get_pixmap(dpi=300)
                    if target_format == "png":
                        pix.save(output_path)
                    elif target_format in ("tif", "tiff"):
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img.save(output_path, "TIFF", compression="tiff_deflate")
                    return True
            except Exception as e:
                logger.warning(f"PDF stream extraction failed: {e}")

    # Strategy 3: Check for embedded BMP ('BM')
    if extracted_image is None:
        bmp_idx = data.find(b"BM")
        if bmp_idx != -1:
            try:
                stream = io.BytesIO(data[bmp_idx:])
                extracted_image = Image.open(stream)
            except Exception as e:
                logger.warning(f"BMP parse failed: {e}")

    # Strategy 4: Parse SAP OTF / Hex-encoded raster drawing records
    if extracted_image is None:
        try:
            text_content = data.decode("latin1", errors="ignore")
            # Extract hex streams commonly found in SAP SmartForms bitmap definitions
            hex_matches = re.findall(r"([0-9A-Fa-f]{32,})", text_content)
            if hex_matches:
                combined_hex = "".join(hex_matches)
                raw_bytes = bytes.fromhex(combined_hex)
                # Check for image magic in raw bytes
                if raw_bytes.startswith(b"II*\x00") or raw_bytes.startswith(b"MM\x00*"):
                    extracted_image = Image.open(io.BytesIO(raw_bytes))
                elif raw_bytes.startswith(b"BM"):
                    extracted_image = Image.open(io.BytesIO(raw_bytes))
        except Exception as e:
            logger.warning(f"OTF hex decode failed: {e}")

    # If an image was extracted, save to target format
    if extracted_image is not None:
        if target_format in ("tif", "tiff"):
            extracted_image.save(output_path, "TIFF", compression="tiff_deflate")
            return True
        elif target_format == "png":
            extracted_image.save(output_path, "PNG")
            return True
        elif target_format == "pdf":
            rgb_img = extracted_image.convert("RGB")
            rgb_img.save(output_path, "PDF", resolution=150.0)
            return True

    # Fallback: Render text drawing / spool dump into clean PDF/TIFF
    try:
        text = data.decode("utf-8", errors="ignore")
        pdf_doc = fitz.open()
        page = pdf_doc.new_page(width=842, height=595) # A4 landscape
        rect = fitz.Rect(40, 40, 802, 555)
        page.insert_textbox(rect, text[:4000], fontsize=8, fontname="couri")
        
        if target_format == "pdf":
            pdf_doc.save(output_path)
            return True
        else:
            pix = page.get_pixmap(dpi=150)
            if target_format == "png":
                pix.save(output_path)
            else:
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(output_path, "TIFF")
            return True
    except Exception as e:
        raise RuntimeError(f"Failed to extract SAP SMF drawing: {str(e)}")
