"""
Resizer & Optimizer Module for 'I LOVE FILES'
Provides dedicated resizing and compression algorithms for PDFs, Images, and Videos.
Supports targeting specific file size ranges in KB or MB.
"""
import os
import io
import logging
from PIL import Image
import fitz # PyMuPDF
import subprocess
import imageio_ffmpeg

logger = logging.getLogger(__name__)
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

PDF_PAGE_SIZES = {
    "a4": (595.28, 841.89),
    "letter": (612.0, 792.0),
    "a3": (841.89, 1190.55),
    "legal": (612.0, 1008.0),
    "a5": (419.53, 595.28)
}

def resize_pdf(
    input_path: str,
    output_path: str,
    target_size: str = "a4",
    compress_mode: str = "medium",
    target_max_bytes: int = None
) -> dict:
    """
    Resizes PDF page dimensions and compresses file size.
    If target_max_bytes is specified, adapts compression and DPI to fit under the target size.
    """
    doc = fitz.open(input_path)
    new_doc = fitz.open()

    target_size_key = target_size.lower().strip() if target_size else "a4"
    target_w, target_h = PDF_PAGE_SIZES.get(target_size_key, PDF_PAGE_SIZES["a4"])
    target_rect = fitz.Rect(0, 0, target_w, target_h)

    for page in doc:
        new_page = new_doc.new_page(width=target_w, height=target_h)
        new_page.show_pdf_page(target_rect, doc, page.number, keep_proportion=True)

    page_count = len(new_doc)
    doc.close()

    # Base save
    new_doc.save(
        output_path,
        garbage=4,
        deflate=True,
        clean=True,
        deflate_images=True,
        deflate_fonts=True
    )
    new_doc.close()

    current_size = os.path.getsize(output_path)
    orig_size = os.path.getsize(input_path)

    # Adaptive size reduction if target_max_bytes is specified and current size exceeds it
    if target_max_bytes and current_size > target_max_bytes:
        logger.info(f"Target size {target_max_bytes} bytes requested, current is {current_size}. Applying adaptive DPI reduction.")
        dpis = [120, 96, 72, 60]
        for dpi in dpis:
            temp_doc = fitz.open()
            src_doc = fitz.open(output_path)
            for page in src_doc:
                pix = page.get_pixmap(dpi=dpi)
                img_bytes = pix.tobytes("jpg")
                p = temp_doc.new_page(width=target_w, height=target_h)
                p.insert_image(target_rect, stream=img_bytes)
            src_doc.close()

            temp_doc.save(output_path, garbage=4, deflate=True)
            temp_doc.close()
            current_size = os.path.getsize(output_path)
            if current_size <= target_max_bytes:
                break

    savings = max(0, (orig_size - current_size) / orig_size * 100) if orig_size > 0 else 0

    return {
        "original_bytes": orig_size,
        "new_bytes": current_size,
        "savings_percent": round(savings, 1),
        "pages": page_count
    }


def resize_image(
    input_path: str,
    output_path: str,
    width: int = None,
    height: int = None,
    scale_percent: float = None,
    keep_aspect: bool = True,
    quality: int = 85,
    output_format: str = None,
    target_max_bytes: int = None
) -> dict:
    """
    Resizes image dimensions and applies quality compression.
    If target_max_bytes is specified (e.g. 200KB), dynamically adjusts quality and scale
    to guarantee the output file size is <= target_max_bytes.
    """
    with Image.open(input_path) as img:
        orig_w, orig_h = img.size
        orig_bytes = os.path.getsize(input_path)

        # Dimension calculation
        if scale_percent is not None and scale_percent > 0:
            factor = scale_percent / 100.0
            new_w = max(1, int(orig_w * factor))
            new_h = max(1, int(orig_h * factor))
        elif width and height:
            if keep_aspect:
                ratio = min(width / orig_w, height / orig_h)
                new_w = max(1, int(orig_w * ratio))
                new_h = max(1, int(orig_h * ratio))
            else:
                new_w, new_h = width, height
        elif width and not height:
            ratio = width / orig_w
            new_w = width
            new_h = max(1, int(orig_h * ratio))
        elif height and not width:
            ratio = height / orig_h
            new_w = max(1, int(orig_w * ratio))
            new_h = height
        else:
            new_w, new_h = orig_w, orig_h

        working_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        ext = (output_format or os.path.splitext(output_path)[1]).lower().lstrip(".")
        if ext in ("jpg", "jpeg") and working_img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", working_img.size, (255, 255, 255))
            if working_img.mode == "P":
                working_img = working_img.convert("RGBA")
            bg.paste(working_img, mask=working_img.split()[-1])
            working_img = bg

        # If user defined target file size (in KB / MB)
        if target_max_bytes and target_max_bytes > 0:
            best_quality = quality
            low_q, high_q = 15, 95
            chosen_img = working_img

            # Binary search for optimal quality
            for _ in range(7):
                mid_q = (low_q + high_q) // 2
                buf = io.BytesIO()
                _save_img_to_buffer(chosen_img, buf, ext, mid_q)
                size = buf.tell()

                if size <= target_max_bytes:
                    best_quality = mid_q
                    low_q = mid_q + 1 # try higher quality
                else:
                    high_q = mid_q - 1 # reduce quality

            # If still larger even at quality 15, scale down dimensions
            buf = io.BytesIO()
            _save_img_to_buffer(chosen_img, buf, ext, best_quality)
            current_size = buf.tell()

            scale_factor = 0.9
            while current_size > target_max_bytes and scale_factor >= 0.2:
                w_scaled = max(10, int(new_w * scale_factor))
                h_scaled = max(10, int(new_h * scale_factor))
                chosen_img = working_img.resize((w_scaled, h_scaled), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                _save_img_to_buffer(chosen_img, buf, ext, best_quality)
                current_size = buf.tell()
                scale_factor -= 0.1

            with open(output_path, "wb") as f:
                f.write(buf.getvalue())

            final_w, final_h = chosen_img.size
        else:
            # Standard single-pass save
            with open(output_path, "wb") as f:
                buf = io.BytesIO()
                _save_img_to_buffer(working_img, buf, ext, quality)
                f.write(buf.getvalue())
            final_w, final_h = working_img.size

        new_bytes = os.path.getsize(output_path)
        savings = max(0, (orig_bytes - new_bytes) / orig_bytes * 100) if orig_bytes > 0 else 0

        return {
            "original_width": orig_w,
            "original_height": orig_h,
            "new_width": final_w,
            "new_height": final_h,
            "original_bytes": orig_bytes,
            "new_bytes": new_bytes,
            "savings_percent": round(savings, 1)
        }


def _save_img_to_buffer(img: Image.Image, buf: io.BytesIO, ext: str, quality: int):
    if ext in ("jpg", "jpeg"):
        rgb = img.convert("RGB") if img.mode != "RGB" else img
        rgb.save(buf, "JPEG", quality=quality, optimize=True)
    elif ext == "webp":
        img.save(buf, "WEBP", quality=quality, method=6)
    elif ext == "png":
        img.save(buf, "PNG", optimize=True)
    else:
        img.save(buf, quality=quality)


def resize_video(input_path: str, output_path: str, resolution: str = "720p", crf: int = 28) -> dict:
    orig_bytes = os.path.getsize(input_path)
    res_map = {
        "480p": "scale=-2:480",
        "720p": "scale=-2:720",
        "1080p": "scale=-2:1080",
        "360p": "scale=-2:360"
    }
    scale_filter = res_map.get(resolution.lower(), "scale=-2:720")

    cmd = [
        FFMPEG_BIN, "-y", "-i", input_path,
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Video resize failed: {res.stderr[-300:]}")

    new_bytes = os.path.getsize(output_path)
    savings = max(0, (orig_bytes - new_bytes) / orig_bytes * 100) if orig_bytes > 0 else 0

    return {
        "original_bytes": orig_bytes,
        "new_bytes": new_bytes,
        "savings_percent": round(savings, 1),
        "target_resolution": resolution
    }
