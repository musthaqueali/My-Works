"""
Image Converter Module for 'I LOVE FILES'
Handles raster conversions (PNG, JPG, WebP, BMP, ICO, TIFF) and vector SVG conversions.
"""
import os
import logging
from PIL import Image
import fitz # PyMuPDF

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

logger = logging.getLogger(__name__)

def convert_image(input_path: str, output_path: str, target_format: str, quality: int = 90) -> bool:
    """
    Converts image files across raster and vector formats.
    """
    target_format = target_format.lower().lstrip(".")
    ext = os.path.splitext(input_path)[1].lower().lstrip(".")

    # 1. SVG inputs
    if ext == "svg":
        doc = fitz.open(input_path)
        page = doc[0]
        if target_format == "pdf":
            pdf_bytes = doc.convert_to_pdf()
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            return True
        elif target_format in ("png", "jpg", "jpeg", "webp"):
            pix = page.get_pixmap(dpi=300)
            if target_format == "png":
                pix.save(output_path)
            else:
                # Convert pixmap to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(output_path, quality=quality)
            return True

    # 2. Raster inputs using Pillow
    with Image.open(input_path) as img:
        # Convert RGBA to RGB if saving to formats without alpha (like JPEG)
        if target_format in ("jpg", "jpeg") and img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1]) # paste using alpha mask
            background.save(output_path, "JPEG", quality=quality)
            return True

        if target_format == "pdf":
            rgb_img = img.convert("RGB")
            rgb_img.save(output_path, "PDF", resolution=100.0)
            return True

        if target_format == "ico":
            # Icon format requires specific square dimensions
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(output_path, format="ICO", sizes=sizes)
            return True

        if target_format == "webp":
            img.save(output_path, "WEBP", quality=quality)
            return True

        if target_format == "png":
            img.save(output_path, "PNG", optimize=True)
            return True

        if target_format == "bmp":
            img.save(output_path, "BMP")
            return True

        if target_format == "tiff":
            img.save(output_path, "TIFF")
            return True

        # Fallback save
        img.save(output_path)
        return True
