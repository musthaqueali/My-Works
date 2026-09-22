"""
HP-GL/2 Plot Converter Module for 'I LOVE FILES'
Converts HP-GL/2 vector plot files (.000, .plt, .hpgl, .hp) into high-resolution PDF, PNG, TIFF, SVG, and DXF.
"""
import os
import io
import logging
from PIL import Image
import ezdxf.addons.hpgl2.api as hpgl_api

logger = logging.getLogger(__name__)

def convert_hpgl(input_path: str, output_path: str, target_format: str) -> bool:
    """
    Converts HP-GL/2 plot files (.plt, .000, .hpgl) into modern formats.
    Supported targets: pdf, png, jpg, jpeg, tiff, tif, svg, dxf.
    """
    target_format = target_format.lower().lstrip(".")

    with open(input_path, "rb") as f:
        data = f.read()

    if not data:
        raise ValueError("HP-GL/2 plot file is empty.")

    # Prepare data for ezdxf tokenizer:
    if not (data.startswith(b"\x1b") or data.startswith(b"BP") or data.startswith(b"IN")):
        in_pos = data.find(b"IN;")
        if in_pos != -1:
            data = b"\x1b%-1B" + data[in_pos:]
        else:
            data = b"\x1b%-1BIN;" + data
    elif not data.startswith(b"\x1b"):
        data = b"\x1b%-1B" + data

    # 1. PDF
    if target_format == "pdf":
        pdf_bytes = hpgl_api.to_pdf(data)
        if not pdf_bytes:
            raise RuntimeError("HP-GL/2 conversion to PDF produced no data.")
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return True

    # 2. PNG or JPEG
    elif target_format in ("png", "jpg", "jpeg"):
        png_bytes = hpgl_api.to_pixmap(data, fmt="png", dpi=150)
        if not png_bytes:
            raise RuntimeError("HP-GL/2 conversion to image produced no data.")
        if target_format == "png":
            with open(output_path, "wb") as f:
                f.write(png_bytes)
        else:
            img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            img.save(output_path, "JPEG", quality=92)
        return True

    # 3. TIFF (High-Resolution Archival)
    elif target_format in ("tiff", "tif"):
        png_bytes = hpgl_api.to_pixmap(data, fmt="png", dpi=300)
        if not png_bytes:
            raise RuntimeError("HP-GL/2 conversion to TIFF produced no data.")
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        img.save(output_path, "TIFF", compression="tiff_deflate")
        return True

    # 4. SVG (Web Vector Graphics)
    elif target_format == "svg":
        svg_content = hpgl_api.to_svg(data)
        if not svg_content:
            raise RuntimeError("HP-GL/2 conversion to SVG produced no data.")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        return True

    # 5. DXF (CAD Interoperability)
    elif target_format == "dxf":
        dxf_doc = hpgl_api.to_dxf(data)
        dxf_doc.saveas(output_path)
        return True

    raise ValueError(f"Unsupported target format for HP-GL/2: {target_format}")
