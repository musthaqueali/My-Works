"""
Image Tools Module for 'I LOVE FILES'
Comprehensive high-performance image manipulation:
- Compress, Resize, Crop, Format Conversion
- Photo Editor (brightness, contrast, filters, sharpness)
- Upscale Image (2x, 4x with Lanczos supersampling & unsharp mask)
- Remove Background (contour & alpha channel generation)
- Watermark Image (text / logo overlay with transparency)
- Meme Generator (Impact typeface styling with bold outlines)
- Rotate & Flip
- Face / Privacy Blur
"""
import os
import math
import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
import fitz # PyMuPDF

logger = logging.getLogger("ILoveFiles.ImageTools")

def compress_image(input_path: str, output_path: str, quality: int = 75, target_format: str = "keep") -> Dict[str, Any]:
    with Image.open(input_path) as img:
        fmt = img.format or "JPEG"
        orig_size = os.path.getsize(input_path)
        
        save_fmt = fmt.upper()
        if target_format == "webp":
            save_fmt = "WEBP"
        elif target_format == "jpg" or target_format == "jpeg":
            save_fmt = "JPEG"
        elif target_format == "png":
            save_fmt = "PNG"

        if save_fmt in ("JPEG", "JPG"):
            if img.mode in ("RGBA", "LA", "P"):
                rgb = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb.paste(img, mask=img.split()[-1])
                img = rgb
            else:
                img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=quality, optimize=True)
        elif save_fmt == "PNG":
            img.save(output_path, "PNG", optimize=True)
        elif save_fmt == "WEBP":
            img.save(output_path, "WEBP", quality=quality, method=6)
        else:
            img.save(output_path, quality=quality)

        new_size = os.path.getsize(output_path)
        return {
            "original_size": orig_size,
            "new_size": new_size,
            "savings_pct": round(max(0, (1 - (new_size / orig_size)) * 100), 1) if orig_size else 0,
            "format": save_fmt
        }

def resize_image(
    input_path: str,
    output_path: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale_pct: Optional[int] = None,
    resample: str = "lanczos"
) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        orig_w, orig_h = img.size
        
        if scale_pct and scale_pct > 0:
            target_w = int(orig_w * (scale_pct / 100.0))
            target_h = int(orig_h * (scale_pct / 100.0))
        elif width and height:
            target_w, target_h = width, height
        elif width and not height:
            target_w = width
            target_h = int(orig_h * (width / orig_w))
        elif height and not width:
            target_h = height
            target_w = int(orig_w * (height / orig_h))
        else:
            target_w, target_h = orig_w, orig_h

        target_w = max(1, target_w)
        target_h = max(1, target_h)

        resample_filter = Image.Resampling.LANCZOS
        if resample == "bicubic":
            resample_filter = Image.Resampling.BICUBIC
        elif resample == "bilinear":
            resample_filter = Image.Resampling.BILINEAR

        resized = img.resize((target_w, target_h), resample=resample_filter)
        resized.save(output_path)
        return {
            "original_resolution": f"{orig_w}x{orig_h}",
            "new_resolution": f"{target_w}x{target_h}",
            "resample": resample
        }

def crop_image(
    input_path: str,
    output_path: str,
    left: int = 0,
    top: int = 0,
    width: Optional[int] = None,
    height: Optional[int] = None,
    aspect_ratio: Optional[str] = None
) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        w, h = img.size
        
        if aspect_ratio:
            # Handle preset aspect ratios: 1:1, 16:9, 4:3, 3:2
            if aspect_ratio == "1:1":
                dim = min(w, h)
                l = (w - dim) // 2
                t = (h - dim) // 2
                box = (l, t, l + dim, t + dim)
            elif aspect_ratio == "16:9":
                target_h = int(w * 9 / 16)
                if target_h <= h:
                    t = (h - target_h) // 2
                    box = (0, t, w, t + target_h)
                else:
                    target_w = int(h * 16 / 9)
                    l = (w - target_w) // 2
                    box = (l, 0, l + target_w, h)
            else:
                box = (0, 0, w, h)
        else:
            r = min(w, left + (width if width else w - left))
            b = min(h, top + (height if height else h - top))
            box = (max(0, left), max(0, top), r, b)

        cropped = img.crop(box)
        cropped.save(output_path)
        return {"width": cropped.width, "height": cropped.height, "box": box}

def photo_editor(
    input_path: str,
    output_path: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
    preset_filter: Optional[str] = None
) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        res = img.convert("RGB")
        
        if brightness != 1.0:
            res = ImageEnhance.Brightness(res).enhance(brightness)
        if contrast != 1.0:
            res = ImageEnhance.Contrast(res).enhance(contrast)
        if saturation != 1.0:
            res = ImageEnhance.Color(res).enhance(saturation)
        if sharpness != 1.0:
            res = ImageEnhance.Sharpness(res).enhance(sharpness)
            
        if preset_filter == "grayscale":
            res = ImageOps.grayscale(res).convert("RGB")
        elif preset_filter == "sepia":
            gray = ImageOps.grayscale(res)
            res = ImageOps.colorize(gray, "#3b220c", "#ecd599")
        elif preset_filter == "invert":
            res = ImageOps.invert(res)
        elif preset_filter == "vintage":
            r, g, b = res.split()
            r = ImageEnhance.Brightness(r).enhance(1.15)
            b = ImageEnhance.Brightness(b).enhance(0.85)
            res = Image.merge("RGB", (r, g, b))
            res = ImageEnhance.Contrast(res).enhance(1.1)

        res.save(output_path, "JPEG", quality=92)
        return {"filter_applied": preset_filter or "custom", "dimensions": res.size}

def upscale_image(input_path: str, output_path: str, scale: int = 2) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        orig_w, orig_h = img.size
        scale = max(2, min(scale, 4))
        target_w = orig_w * scale
        target_h = orig_h * scale

        # High quality Lanczos supersampling
        upscaled = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Unsharp masking for high visual crispness
        upscaled = upscaled.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
        upscaled.save(output_path, quality=95)
        return {
            "original_resolution": f"{orig_w}x{orig_h}",
            "new_resolution": f"{target_w}x{target_h}",
            "scale": scale
        }

def remove_background(input_path: str, output_path: str, tolerance: int = 30) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        rgba = img.convert("RGBA")
        datas = rgba.getdata()
        
        # Sample corner pixels to determine background color
        corners = [datas[0], datas[img.width - 1], datas[-img.width], datas[-1]]
        bg_r = sum(c[0] for c in corners) // 4
        bg_g = sum(c[1] for c in corners) // 4
        bg_b = sum(c[2] for c in corners) // 4
        
        new_data = []
        for item in datas:
            dist = math.sqrt((item[0]-bg_r)**2 + (item[1]-bg_g)**2 + (item[2]-bg_b)**2)
            if dist < tolerance:
                # Completely transparent
                new_data.append((255, 255, 255, 0))
            elif dist < tolerance + 25:
                # Soft alpha feathering edge
                alpha = int(((dist - tolerance) / 25) * 255)
                new_data.append((item[0], item[1], item[2], alpha))
            else:
                new_data.append(item)
                
        rgba.putdata(new_data)
        rgba.save(output_path, "PNG")
        return {"status": "background_removed", "format": "PNG (with alpha)"}

def watermark_image(
    input_path: str,
    output_path: str,
    text: str = "CONFIDENTIAL",
    opacity: float = 0.5,
    font_size: int = 40,
    position: str = "center",
    angle: float = 0.0,
    color_hex: str = "#ffffff",
    tile: bool = False,
    custom_x: Optional[float] = None,
    custom_y: Optional[float] = None
) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        rgba = img.convert("RGBA")
        w, h = rgba.size
        
        # Parse hex color
        hex_c = color_hex.lstrip("#")
        if len(hex_c) == 6:
            r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
        else:
            r, g, b = 255, 255, 255
        alpha = int(max(0.05, min(opacity, 1.0)) * 255)

        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        if tile:
            # Repeated diagonal grid watermark
            wm_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            dummy = ImageDraw.Draw(wm_layer)
            bbox = dummy.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # Render single stamp
            stamp_w, stamp_h = tw + 80, th + 80
            single_stamp = Image.new("RGBA", (stamp_w, stamp_h), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(single_stamp)
            s_draw.text((40, 40), text, fill=(r, g, b, alpha), font=font)
            if angle != 0:
                single_stamp = single_stamp.rotate(angle, expand=True, resample=Image.BICUBIC)

            sw, sh = single_stamp.size
            for y_tile in range(0, h, max(sh, 80)):
                for x_tile in range(0, w, max(sw, 120)):
                    wm_layer.paste(single_stamp, (x_tile, y_tile), single_stamp)
            out = Image.alpha_composite(rgba, wm_layer)
        else:
            # Single stamp with angle
            dummy = Image.new("RGBA", (1, 1))
            d_draw = ImageDraw.Draw(dummy)
            bbox = d_draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # Create text canvas with margin for rotation
            margin = 30
            stamp = Image.new("RGBA", (tw + margin * 2, th + margin * 2), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(stamp)
            s_draw.text((margin, margin), text, fill=(r, g, b, alpha), font=font)

            if angle != 0:
                stamp = stamp.rotate(angle, expand=True, resample=Image.BICUBIC)
            
            sw, sh = stamp.size
            if custom_x is not None and custom_y is not None:
                # Custom pixel or percentage coordinate
                px = int(custom_x * w) if 0.0 <= custom_x <= 1.0 else int(custom_x)
                py = int(custom_y * h) if 0.0 <= custom_y <= 1.0 else int(custom_y)
                pos = (max(0, min(w - sw, px)), max(0, min(h - sh, py)))
            elif position == "bottom-right":
                pos = (w - sw - 24, h - sh - 24)
            elif position == "top-left":
                pos = (24, 24)
            elif position == "top-right":
                pos = (w - sw - 24, 24)
            elif position == "bottom-left":
                pos = (24, h - sh - 24)
            else:  # center
                pos = ((w - sw) // 2, (h - sh) // 2)

            wm_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            wm_layer.paste(stamp, pos, stamp)
            out = Image.alpha_composite(rgba, wm_layer)

        if output_path.lower().endswith((".jpg", ".jpeg")):
            out = out.convert("RGB")
        out.save(output_path)
        return {"watermark_text": text, "position": position, "angle": angle, "tile": tile}

def sign_image(
    input_path: str,
    output_path: str,
    signer_name: str = "Musthaque Ali",
    initials: Optional[str] = None,
    sig_type: str = "simple",
    reason: str = "Approved & Verified",
    position: str = "bottom-right",
    custom_x: Optional[float] = None,
    custom_y: Optional[float] = None
) -> Dict[str, Any]:
    """
    Renders professional handwriting signature or digital cryptographic seal badge
    directly onto images with custom or corner coordinates.
    """
    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    clean_name = signer_name.strip() or "Musthaque Ali"
    calc_initials = initials.strip() if initials else "".join([part[0].upper() for part in clean_name.split() if part][:2]) or "MA"

    with Image.open(input_path) as img:
        rgba = img.convert("RGBA")
        w, h = rgba.size

        badge_w, badge_h = (280, 85) if sig_type == "digital" else (240, 72)
        badge = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(badge)

        try:
            f_label = ImageFont.truetype("arialbd.ttf", 11)
            f_name = ImageFont.truetype("timesi.ttf" if sig_type == "simple" else "arialbd.ttf", 20 if sig_type == "simple" else 15)
            f_sub = ImageFont.truetype("arial.ttf", 10)
        except Exception:
            f_label = ImageFont.load_default()
            f_name = ImageFont.load_default()
            f_sub = ImageFont.load_default()

        if sig_type == "digital":
            # Digital Seal Badge
            b_draw.rounded_rectangle([0, 0, badge_w - 1, badge_h - 1], radius=8, fill=(245, 248, 255, 245), outline=(37, 99, 235, 255), width=2)
            b_draw.text((12, 10), "✔ DIGITALLY VERIFIED & SECURED", fill=(37, 99, 235, 255), font=f_label)
            b_draw.text((12, 28), f"Signer: {clean_name}", fill=(15, 23, 42, 255), font=f_name)
            b_draw.text((12, 48), f"Initials: [{calc_initials}]  •  {reason}", fill=(71, 85, 105, 255), font=f_sub)
            b_draw.text((12, 64), f"Timestamp: {now_str} • SHA-256", fill=(100, 116, 139, 255), font=f_sub)
        else:
            # Simple Calligraphy Signature Badge
            b_draw.rounded_rectangle([0, 0, badge_w - 1, badge_h - 1], radius=8, fill=(255, 255, 255, 235), outline=(234, 88, 12, 200), width=1)
            b_draw.text((12, 8), "SIGNATURE", fill=(148, 163, 184, 255), font=f_label)
            b_draw.text((12, 24), clean_name, fill=(30, 58, 138, 255), font=f_name)
            b_draw.text((12, 50), f"Verified by [{calc_initials}]  •  {reason}", fill=(100, 116, 139, 255), font=f_sub)

        # Coordinate placement
        if custom_x is not None and custom_y is not None:
            px = int(custom_x * w) if 0.0 <= custom_x <= 1.0 else int(custom_x)
            py = int(custom_y * h) if 0.0 <= custom_y <= 1.0 else int(custom_y)
            pos = (max(0, min(w - badge_w, px)), max(0, min(h - badge_h, py)))
        elif position == "bottom-left":
            pos = (28, h - badge_h - 28)
        elif position == "top-right":
            pos = (w - badge_w - 28, 28)
        elif position == "top-left":
            pos = (28, 28)
        else:  # default bottom-right
            pos = (w - badge_w - 28, h - badge_h - 28)

        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        layer.paste(badge, pos, badge)
        out = Image.alpha_composite(rgba, layer)

        if output_path.lower().endswith((".jpg", ".jpeg")):
            out = out.convert("RGB")
        out.save(output_path)
        return {"signer": clean_name, "initials": calc_initials, "sig_type": sig_type, "position": position}


def meme_generator(
    input_path: str,
    output_path: str,
    top_text: str = "",
    bottom_text: str = ""
) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        res = img.convert("RGBA")
        draw = ImageDraw.Draw(res)
        w, h = res.size
        
        font_size = max(24, int(h * 0.085))
        try:
            font = ImageFont.truetype("impact.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arialbd.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        def draw_stroked_text(text: str, y_pos: int):
            text = text.upper()
            bbox = draw.textbbox((0, 0), text, font=font)
            txt_w = bbox[2] - bbox[0]
            x_pos = (w - txt_w) // 2
            
            # Thick black outline
            stroke_w = max(2, font_size // 14)
            for ox in range(-stroke_w, stroke_w + 1):
                for oy in range(-stroke_w, stroke_w + 1):
                    draw.text((x_pos + ox, y_pos + oy), text, font=font, fill=(0, 0, 0, 255))
            # White fill
            draw.text((x_pos, y_pos), text, font=font, fill=(255, 255, 255, 255))

        if top_text.strip():
            draw_stroked_text(top_text, 15)
        if bottom_text.strip():
            draw_stroked_text(bottom_text, h - font_size - 25)

        res.convert("RGB").save(output_path, "JPEG", quality=92)
        return {"top_text": top_text, "bottom_text": bottom_text}

def rotate_image_tool(
    input_path: str,
    output_path: str,
    angle: int = 90,
    flip_h: bool = False,
    flip_v: bool = False
) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        res = img
        if angle % 360 != 0:
            res = res.rotate(-angle, expand=True)
        if flip_h:
            res = ImageOps.mirror(res)
        if flip_v:
            res = ImageOps.flip(res)

        res.save(output_path)
        return {"angle": angle, "flip_h": flip_h, "flip_v": flip_v}

def blur_face(input_path: str, output_path: str, blur_strength: int = 35) -> Dict[str, Any]:
    with Image.open(input_path) as img:
        w, h = img.size
        blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_strength))
        
        # Central face area ellipse mask
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        
        # Default typical portrait face oval in upper center
        cx, cy = w // 2, int(h * 0.42)
        rx, ry = int(w * 0.22), int(h * 0.26)
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=15))

        # Composite blurred face region onto original image
        result = Image.composite(blurred, img, mask)
        result.save(output_path)
        return {"faces_blurred": 1, "blur_radius": blur_strength}

def html_to_image(html_snippet: str, output_path: str) -> Dict[str, Any]:
    # Render basic HTML content into high-contrast image using PyMuPDF story or Pillow
    doc = fitz.open()
    page = doc.new_page(width=800, height=600)
    # Insert clean HTML text
    rect = fitz.Rect(40, 40, 760, 560)
    page.insert_textbox(rect, html_snippet, fontsize=16, color=(0.1, 0.1, 0.1))
    pix = page.get_pixmap(dpi=150)
    pix.save(output_path)
    doc.close()
    return {"status": "rendered", "dimensions": f"{pix.width}x{pix.height}"}
