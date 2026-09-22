"""
Document Merger Module for 'I LOVE FILES'
Merges multiple files (PDF, DOCX, Images) into a single, unified PDF document.
"""
import os
import io
import logging
from PIL import Image
import fitz # PyMuPDF
from converters.doc_converter import convert_document

logger = logging.getLogger(__name__)

def merge_documents(file_paths: list[str], output_path: str) -> dict:
    """
    Combines an ordered list of files into a single unified PDF.
    Supports PDFs, Images (PNG, JPG, TIFF, WebP), DOCX, and Text files.
    """
    merged_doc = fitz.open()

    for path in file_paths:
        ext = os.path.splitext(path)[1].lower().lstrip(".")

        try:
            # 1. PDF Files
            if ext == "pdf":
                src_doc = fitz.open(path)
                merged_doc.insert_pdf(src_doc)
                src_doc.close()

            # 2. Image Files (PNG, JPG, JPEG, WebP, TIFF, BMP, GIF, ICO)
            elif ext in ("png", "jpg", "jpeg", "webp", "tif", "tiff", "bmp", "gif", "jfif", "ico"):
                try:
                    img_doc = fitz.open(path)
                    pdf_bytes = img_doc.convert_to_pdf()
                    img_pdf = fitz.open("pdf", pdf_bytes)
                    merged_doc.insert_pdf(img_pdf)
                    img_pdf.close()
                    img_doc.close()
                except Exception:
                    with Image.open(path) as img:
                        if img.mode in ("RGBA", "LA", "P"):
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == "P":
                                img = img.convert("RGBA")
                            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                            rgb_img = bg
                        else:
                            rgb_img = img.convert("RGB")

                        buf = io.BytesIO()
                        rgb_img.save(buf, format="PDF", resolution=150.0)
                        buf.seek(0)
                        sub_doc = fitz.open("pdf", buf.read())
                        merged_doc.insert_pdf(sub_doc)
                        sub_doc.close()

            # 3. CAD Drawings (DWG, DXF)
            elif ext in ("dwg", "dxf"):
                temp_pdf = path + ".cad.pdf"
                try:
                    from converters.cad_converter import convert_cad
                    ok = convert_cad(path, temp_pdf, "pdf")
                    if ok and os.path.exists(temp_pdf):
                        cad_doc = fitz.open(temp_pdf)
                        merged_doc.insert_pdf(cad_doc)
                        cad_doc.close()
                finally:
                    if os.path.exists(temp_pdf):
                        try: os.remove(temp_pdf)
                        except Exception: pass

            # 4. DOCX or Text Files
            elif ext in ("docx", "txt", "md"):
                temp_pdf = path + ".temp.pdf"
                try:
                    ok, final_pdf = convert_document(path, temp_pdf, "pdf")
                    if ok and os.path.exists(final_pdf):
                        temp_doc = fitz.open(final_pdf)
                        merged_doc.insert_pdf(temp_doc)
                        temp_doc.close()
                finally:
                    if os.path.exists(temp_pdf):
                        try: os.remove(temp_pdf)
                        except Exception: pass

            else:
                logger.warning(f"Skipping unsupported merge format: {ext}")

        except Exception as e:
            logger.error(f"Error merging file {path}: {e}")
            raise RuntimeError(f"Failed to merge {os.path.basename(path)}: {str(e)}")

    total_pages = len(merged_doc)
    if total_pages == 0:
        raise ValueError("No valid pages could be merged.")

    merged_doc.save(output_path, garbage=1, deflate=True)
    merged_doc.close()

    return {
        "pages": total_pages,
        "size_bytes": os.path.getsize(output_path)
    }
