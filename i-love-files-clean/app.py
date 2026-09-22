"""
'I LOVE FILES' - Universal File Converter & Resizer
FastAPI Web Server
"""
import os
import uuid
import time
import json
import shutil
import logging
import zipfile
import urllib.parse
import asyncio
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import fitz # PyMuPDF

import database
import auth
from auth import get_current_user_optional, get_client_ip
import billing

import format_registry
from converters.cad_converter import convert_cad
from converters.media_converter import convert_media
from converters.doc_converter import convert_document
from converters.image_converter import convert_image
from converters.resizer import resize_pdf, resize_image, resize_video
from converters.smf_extractor import extract_smf_drawing
from converters.merger import merge_documents
from converters.plt_converter import convert_hpgl
from converters.autocad_plotter import batch_plot_dwg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ILoveFiles")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(title="I LOVE FILES", description="Universal Converter & Resizer")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if os.environ.get("COOKIE_SECURE", "false").lower() in ("true", "1", "yes"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth.router)
app.include_router(billing.router)

def enforce_quota(request: Request, file_size_bytes: Optional[int] = None):
    user = get_current_user_optional(request)
    ip = get_client_ip(request)
    quota = database.check_and_increment_quota(user, ip)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=quota["message"]
        )
    if file_size_bytes and file_size_bytes > quota["max_file_size"]:
        max_mb = quota["max_file_size"] // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the {max_mb} MB limit for your {quota['tier'].upper()} plan. Upgrade to Pro for up to 500 MB!"
        )
    return user, ip, quota

@app.get("/api/health")
def get_health():
    return {
        "status": "operational",
        "supported_formats_count": len(format_registry.FORMAT_CATALOG),
        "timestamp": time.time()
    }

@app.get("/api/cad/engine-status")
def get_cad_engine_status():
    from converters.autocad_plotter import get_autocad_console_path, get_autocad_plot_styles_dir, is_autocad_available
    console = get_autocad_console_path()
    avail = is_autocad_available()
    return {
        "is_autocad_available": avail,
        "accoreconsole_path": console,
        "plot_styles_dir": get_autocad_plot_styles_dir(),
        "engine_type": "Autodesk Native Console" if avail else "Aspose CAD Fallback"
    }

@app.get("/api/cad/last-plot-log")
def get_cad_last_plot_log():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.log")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            return {"log": "".join(lines[-150:])}
        except Exception as e:
            return {"error": str(e)}
    return {"log": "No server.log file found yet."}

@app.get("/api/cad/inspect-system")
def inspect_system():
    results = {}
    for base in [r"C:\Program Files\Autodesk", r"C:\Program Files (x86)\Autodesk"]:
        if os.path.isdir(base):
            results[base] = []
            for d in sorted(os.listdir(base)):
                full_d = os.path.join(base, d)
                if os.path.isdir(full_d):
                    exe = os.path.join(full_d, "accoreconsole.exe")
                    results[base].append({"folder": d, "has_accoreconsole": os.path.exists(exe)})
    return results

@app.get("/api/formats")
def get_formats():
    return {"catalog": format_registry.FORMAT_CATALOG}

@app.get("/api/use-case")
def get_format_use_case(source: str, target: str):
    return {"source": source, "target": target, "use_case": format_registry.get_use_case(source, target)}

@app.post("/api/inspect")
async def inspect_file(file: UploadFile = File(...)):
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    
    src_key, src_data = format_registry.get_format_info(ext)
    targets = src_data["targets"] if src_data else ["pdf", "zip"]
    category = src_data["category"] if src_data else "General"
    description = src_data["description"] if src_data else "Data file"
    
    page_count = 1
    if ext == "pdf":
        try:
            content = await file.read()
            pdf_doc = fitz.open(stream=content, filetype="pdf")
            page_count = len(pdf_doc)
            pdf_doc.close()
            await file.seek(0)
        except Exception as e:
            logger.warning(f"Inspect page count warning: {e}")

    target_info = []
    for tgt in targets:
        target_info.append({
            "format": tgt,
            "use_case": format_registry.get_use_case(ext, tgt)
        })
        
    return {
        "filename": filename,
        "extension": ext,
        "category": category,
        "description": description,
        "page_count": page_count,
        "suggested_targets": target_info
    }

@app.post("/api/convert")
async def handle_convert(
    request: Request,
    file: UploadFile = File(...),
    target_format: str = Form(...),
    options: Optional[str] = Form(None)
):
    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    original_filename = file.filename
    base_name, in_ext = os.path.splitext(original_filename)
    in_ext = in_ext.lower().lstrip(".")
    target_format = target_format.lower().lstrip(".")

    input_path = os.path.join(task_dir, original_filename)
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    original_size = os.path.getsize(input_path)
    user, ip, quota = enforce_quota(request, original_size)

    output_filename = f"{base_name}_converted.{target_format}" if in_ext == target_format else f"{base_name}.{target_format}"
    output_path = os.path.join(task_dir, output_filename)

    opts = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            pass

    page_option = opts.get("page_option", "all")
    success = False
    final_output_path = output_path

    try:
        # 1. CAD (DWG, DXF, DWF, DWFX, or PDF -> CAD)
        if in_ext in ("dwg", "dxf", "dwf", "dwfx") or (in_ext == "pdf" and target_format in ("dwg", "dxf")):
            cad_paper_size = opts.get("paper_size", "ANSI full bleed B (17.00 x 11.00 Inches)")
            cad_orientation = opts.get("orientation", "Landscape")
            cad_plot_style = opts.get("plot_style", "acad.ctb")
            cad_plot_with_styles = opts.get("plot_with_styles", True)
            cad_plot_lineweights = opts.get("plot_lineweights", True)
            cad_plot_area = opts.get("plot_area", "Extents")
            cad_shade_plot = opts.get("shade_plot", "Wireframe")
            cad_custom_ctb_path = opts.get("custom_ctb_path")
            success = convert_cad(
                input_path, output_path, target_format,
                paper_size=cad_paper_size,
                orientation=cad_orientation,
                plot_style=cad_plot_style,
                plot_with_styles=cad_plot_with_styles,
                plot_lineweights=cad_plot_lineweights,
                plot_area=cad_plot_area,
                shade_plot=cad_shade_plot,
                custom_ctb_path=cad_custom_ctb_path
            )

        # 2. HP-GL/2 Plots (.000, .plt, .hp, .hpgl, .prn)
        elif in_ext in ("plt", "000", "hpgl", "hp", "prn"):
            success = convert_hpgl(input_path, output_path, target_format)

        # 3. SAP SMF Drawing Extractor
        elif in_ext == "smf":
            success = extract_smf_drawing(input_path, output_path, target_format)

        # 4. Video (or GIF to Video)
        elif in_ext in ("mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "3gp", "3g2", "ts", "mts", "m2ts", "mpg", "mpeg", "vob", "ogv") or (in_ext == "gif" and target_format in ("mp4", "webm", "mov", "mkv", "avi")):
            resolution = opts.get("resolution")
            bitrate = opts.get("bitrate")
            success = convert_media(input_path, output_path, target_format, resolution, bitrate)

        # 5. Audio
        elif in_ext in ("mp3", "wav", "flac", "ogg", "m4a", "aac", "opus", "wma", "aiff", "ac3", "amr", "m4r", "mp2", "caf", "au"):
            bitrate = opts.get("bitrate")
            success = convert_media(input_path, output_path, target_format, bitrate=bitrate)

        # 6. Documents & Specialized (PDF, DOCX, DOC, PPTX, XLSX, HTML, CSV, JSON, XML, MD, TXT, DCM, DICOM, EPUB, MOBI, FB2, HEIC, HEIF, ODT, ODS, ODP, RTF, PAGES, NUMBERS, KEYNOTE, PUB, YAML)
        elif in_ext in ("pdf", "docx", "doc", "dotx", "dot", "pptx", "ppt", "xlsx", "xls", "csv", "txt", "md", "markdown", "html", "htm", "json", "xml", "dcm", "dicom", "epub", "mobi", "fb2", "heic", "heif", "odt", "ods", "odp", "rtf", "pages", "numbers", "keynote", "pub", "yaml", "yml"):
            success, final_output_path = convert_document(input_path, output_path, target_format, page_option=page_option)

        # 7. Images
        elif in_ext in ("png", "jpg", "jpeg", "webp", "bmp", "ico", "tiff", "tif", "svg", "gif", "psd", "eps", "ai"):
            quality = opts.get("quality", 90)
            success = convert_image(input_path, output_path, target_format, quality=quality)

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {in_ext}")

    except Exception as e:
        logger.error(f"Conversion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    if not success or not os.path.exists(final_output_path):
        raise HTTPException(status_code=500, detail="Conversion completed without output file.")

    converted_size = os.path.getsize(final_output_path)
    output_filename = os.path.basename(final_output_path)
    duration_ms = int((time.time() - start_time) * 1000)
    savings = max(0, (original_size - converted_size) / original_size * 100) if original_size > 0 else 0
    use_case = format_registry.get_use_case(in_ext, target_format)

    database.log_conversion(
        operation=f"{in_ext}->{target_format}",
        source_filename=original_filename,
        target_format=target_format,
        file_size_bytes=original_size,
        duration_ms=duration_ms,
        user_id=user["id"] if user else None,
        ip_address=ip
    )

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{urllib.parse.quote(output_filename)}",
        "original_filename": original_filename,
        "output_filename": output_filename,
        "source_format": in_ext.upper(),
        "target_format": target_format.upper(),
        "original_size": original_size,
        "converted_size": converted_size,
        "savings_percent": round(savings, 1),
        "duration_ms": duration_ms,
        "use_case": use_case,
        "quota": {
            "tier": quota["tier"],
            "used_today": quota["used_today"],
            "limit": quota["limit"],
            "remaining": quota["remaining"]
        }
    }

@app.post("/api/convert-batch")
async def handle_convert_batch(
    files: list[UploadFile] = File(...),
    target_format: str = Form(...),
    options: Optional[str] = Form(None)
):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    target_format = target_format.lower().lstrip(".")
    converted_files = []
    total_original_bytes = 0

    opts = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            pass

    for idx, file in enumerate(files):
        filename = file.filename or f"file_{idx}"
        base_name, in_ext = os.path.splitext(filename)
        in_ext = in_ext.lower().lstrip(".")

        input_path = os.path.join(task_dir, filename)
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        total_original_bytes += os.path.getsize(input_path)

        output_filename = f"{base_name}_converted.{target_format}" if in_ext == target_format else f"{base_name}.{target_format}"
        output_path = os.path.join(task_dir, output_filename)

        success = False
        final_output_path = output_path

        try:
            if in_ext in ("dwg", "dxf", "dwf", "dwfx") or (in_ext == "pdf" and target_format in ("dwg", "dxf")):
                cad_paper_size = opts.get("paper_size", "ANSI full bleed B (17.00 x 11.00 Inches)")
                cad_orientation = opts.get("orientation", "Landscape")
                cad_plot_style = opts.get("plot_style", "acad.ctb")
                cad_plot_with_styles = opts.get("plot_with_styles", True)
                cad_plot_lineweights = opts.get("plot_lineweights", True)
                cad_plot_area = opts.get("plot_area", "Extents")
                cad_shade_plot = opts.get("shade_plot", "Wireframe")
                cad_custom_ctb_path = opts.get("custom_ctb_path")
                success = convert_cad(
                    input_path, output_path, target_format,
                    paper_size=cad_paper_size,
                    orientation=cad_orientation,
                    plot_style=cad_plot_style,
                    plot_with_styles=cad_plot_with_styles,
                    plot_lineweights=cad_plot_lineweights,
                    plot_area=cad_plot_area,
                    shade_plot=cad_shade_plot,
                    custom_ctb_path=cad_custom_ctb_path
                )
            elif in_ext in ("plt", "000", "hpgl", "hp", "prn"):
                success = convert_hpgl(input_path, output_path, target_format)
            elif in_ext == "smf":
                success = extract_smf_drawing(input_path, output_path, target_format)
            elif in_ext in ("mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "3gp", "3g2", "ts", "mts", "m2ts", "mpg", "mpeg", "vob", "ogv") or (in_ext == "gif" and target_format in ("mp4", "webm", "mov", "mkv", "avi")):
                success = convert_media(input_path, output_path, target_format)
            elif in_ext in ("mp3", "wav", "flac", "ogg", "m4a", "aac", "opus", "wma", "aiff", "ac3", "amr", "m4r", "mp2", "caf", "au"):
                success = convert_media(input_path, output_path, target_format)
            elif in_ext in ("pdf", "docx", "doc", "dotx", "dot", "pptx", "ppt", "xlsx", "xls", "csv", "txt", "md", "markdown", "html", "htm", "json", "xml"):
                success, final_output_path = convert_document(input_path, output_path, target_format)
            elif in_ext in ("png", "jpg", "jpeg", "webp", "bmp", "ico", "tiff", "tif", "svg"):
                success = convert_image(input_path, output_path, target_format)

            if success and os.path.exists(final_output_path):
                converted_files.append(final_output_path)
        except Exception as e:
            logger.warning(f"Batch item failed ({filename}): {e}")

    if not converted_files:
        raise HTTPException(status_code=500, detail="None of the uploaded files could be converted to the target format.")

    zip_filename = f"batch_converted_{target_format}.zip"
    zip_path = os.path.join(task_dir, zip_filename)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in converted_files:
            zf.write(p, arcname=os.path.basename(p))

    duration_ms = int((time.time() - start_time) * 1000)
    total_converted_bytes = os.path.getsize(zip_path)

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{zip_filename}",
        "output_filename": zip_filename,
        "file_count": len(converted_files),
        "total_files": len(files),
        "original_bytes": total_original_bytes,
        "converted_bytes": total_converted_bytes,
        "duration_ms": duration_ms
    }

# ==============================================================================
# PCML SMART ASSIGNER ENDPOINTS (Chevron Compliance & AutoCAD Publishing)
# ==============================================================================

@app.post("/api/pcml/assign")
async def handle_pcml_assign(
    files: list[UploadFile] = File(...),
    include_headings: bool = Form(False),
    plot_style: str = Form("acad.ctb"),
    paper_size: str = Form("ANSI full bleed B (17.00 x 11.00 Inches)")
):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No DWG/DXF drawings uploaded.")

    from converters.pcml_engine import process_dwg_pcml

    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    results = []
    all_output_files = []
    dm_counts = {}
    total_assigned = 0

    for idx, file in enumerate(files):
        filename = file.filename or f"drawing_{idx}.dwg"
        base_name, in_ext = os.path.splitext(filename)
        in_ext = in_ext.lower().lstrip(".")
        if in_ext not in ("dwg", "dxf"):
            continue

        input_path = os.path.join(task_dir, filename)
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            sub_dir = os.path.join(task_dir, f"proc_{idx}")
            res = process_dwg_pcml(
                dwg_path=input_path,
                job_dir=sub_dir,
                include_headings=include_headings,
                plot_style=plot_style,
                paper_size=paper_size
            )

            dwg_rel = None
            pdf_rel = None
            preview_rel = None

            if res.get("annotated_dwg") and os.path.exists(res["annotated_dwg"]):
                dwg_name = f"{base_name}_PCML.dwg"
                dwg_dest = os.path.join(task_dir, dwg_name)
                shutil.copy2(res["annotated_dwg"], dwg_dest)
                dwg_rel = f"/api/download/{task_id}/{urllib.parse.quote(dwg_name)}"
                all_output_files.append(dwg_dest)

            if res.get("plotted_pdf") and os.path.exists(res["plotted_pdf"]):
                pdf_name = f"{base_name}_PCML.pdf"
                pdf_dest = os.path.join(task_dir, pdf_name)
                shutil.copy2(res["plotted_pdf"], pdf_dest)
                pdf_rel = f"/api/download/{task_id}/{urllib.parse.quote(pdf_name)}"
                all_output_files.append(pdf_dest)

            if res.get("preview_png") and os.path.exists(res["preview_png"]):
                prev_name = f"{base_name}_preview.png"
                prev_dest = os.path.join(task_dir, prev_name)
                shutil.copy2(res["preview_png"], prev_dest)
                preview_rel = f"/api/download/{task_id}/{urllib.parse.quote(prev_name)}"

            for a in res.get("assignments", []):
                code = a.get("dm_disp", "OTHER")
                dm_counts[code] = dm_counts.get(code, 0) + 1
                total_assigned += 1

            results.append({
                "filename": filename,
                "base_name": base_name,
                "pcml_count": res.get("pcml_count", 0),
                "assignments": res.get("assignments", []),
                "dwg_url": dwg_rel,
                "pdf_url": pdf_rel,
                "preview_url": preview_rel
            })
        except Exception as e:
            logger.error(f"Error processing PCML for {filename}: {e}", exc_info=True)
            results.append({
                "filename": filename,
                "base_name": base_name,
                "error": str(e),
                "pcml_count": 0,
                "assignments": []
            })

    zip_url = None
    if all_output_files:
        zip_filename = f"PCML_Blueprint_Package_{task_id[:8]}.zip"
        zip_path = os.path.join(task_dir, zip_filename)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fpath in all_output_files:
                zf.write(fpath, arcname=os.path.basename(fpath))
        zip_url = f"/api/download/{task_id}/{zip_filename}"

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "task_id": task_id,
        "results": results,
        "total_drawings": len(files),
        "successful_drawings": len([r for r in results if not r.get("error")]),
        "total_pcml_count": total_assigned,
        "summary_counts": dm_counts,
        "batch_zip_url": zip_url,
        "duration_ms": duration_ms
    }

@app.get("/api/pcml/rules")
def get_pcml_rules():
    return {
        "rules": [
            {
                "code": "85A",
                "name": "Deadleg Run & End Terminations",
                "strategy": "Chevron IS 85 / Inspection Guide: Deadlegs",
                "description": "Placed on deadleg branches near the live line and at deadleg terminations (upstream of caps/blind flanges/closed block valves) where stagnant liquid, acidic condensation, and water settle.",
                "color": "#e11d48",
                "symbol": "Hexagon PART_PCML"
            },
            {
                "code": "85B",
                "name": "Vertical Deadleg Low Base",
                "strategy": "Chevron IS 85 / Inspection Guide: Deadlegs",
                "description": "Placed at the base of vertical rises, gravity pockets, and low-point drain risers where gravity causes stagnant liquid stratification and localized pitting.",
                "color": "#ea580c",
                "symbol": "Hexagon PART_PCML"
            },
            {
                "code": "51A",
                "name": "MIC - Low-Point Biofilm Stagnation",
                "strategy": "Chevron IS 51 / Inspection Guide: Microbiologically Influenced Corrosion",
                "description": "Placed at low-point drain terminals and deadleg ends where stagnant water provides an anaerobic environment for sulfate-reducing bacteria (SRB) and biofilm formation.",
                "color": "#0284c7",
                "symbol": "Hexagon PART_PCML"
            },
            {
                "code": "51B",
                "name": "MIC - Secondary Vertical Rise Settling",
                "strategy": "Chevron IS 51 / Inspection Guide: Microbiologically Influenced Corrosion",
                "description": "Placed at secondary branches and vertical rise bases subject to intermittent stagnant pooling.",
                "color": "#0d9488",
                "symbol": "Hexagon PART_PCML"
            },
            {
                "code": "99",
                "name": "Foul Water Wet H2S Corrosion",
                "strategy": "Chevron IS 99 / Inspection Guide: Foul Water Wet H2S Systems",
                "description": "Placed on sour/foul water streams at flow disturbance points (elbows, reducers) where turbulent impingement strips iron sulfide protective scales.",
                "color": "#7c3aed",
                "symbol": "Hexagon PART_PCML"
            }
        ]
    }

@app.post("/api/resize")
async def handle_resize(
    file: UploadFile = File(...),
    tool_type: str = Form(...),
    options: Optional[str] = Form(None)
):
    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    original_filename = file.filename
    base_name, in_ext = os.path.splitext(original_filename)
    input_path = os.path.join(task_dir, original_filename)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    opts = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            pass

    tool_type = tool_type.lower().strip()
    stats = {}

    # Target max file size (in KB or MB) if specified
    target_max_bytes = None
    target_val = opts.get("target_size_val")
    target_unit = (opts.get("target_size_unit") or "kb").lower()
    if target_val:
        try:
            t_val = float(target_val)
            if t_val > 0:
                if target_unit == "mb":
                    target_max_bytes = int(t_val * 1024 * 1024)
                else:
                    target_max_bytes = int(t_val * 1024)
        except Exception:
            pass
    elif opts.get("target_max_bytes"):
        try:
            target_max_bytes = int(opts.get("target_max_bytes"))
        except Exception:
            pass

    try:
        if tool_type == "pdf":
            output_filename = f"{base_name}_resized.pdf"
            output_path = os.path.join(task_dir, output_filename)
            target_size = opts.get("target_size", "a4")
            compress_mode = opts.get("compress_mode", "medium")
            stats = resize_pdf(input_path, output_path, target_size, compress_mode, target_max_bytes=target_max_bytes)

        elif tool_type == "image":
            out_ext = opts.get("output_format") or in_ext.lstrip(".")
            output_filename = f"{base_name}_resized.{out_ext}"
            output_path = os.path.join(task_dir, output_filename)
            width = opts.get("width")
            height = opts.get("height")
            scale_percent = opts.get("scale_percent")
            keep_aspect = opts.get("keep_aspect", True)
            quality = opts.get("quality", 85)
            stats = resize_image(input_path, output_path, width, height, scale_percent, keep_aspect, quality, out_ext, target_max_bytes=target_max_bytes)

        elif tool_type == "video":
            output_filename = f"{base_name}_resized.mp4"
            output_path = os.path.join(task_dir, output_filename)
            resolution = opts.get("resolution", "720p")
            crf = opts.get("crf", 28)
            stats = resize_video(input_path, output_path, resolution, crf)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool type: {tool_type}")

    except Exception as e:
        logger.error(f"Resize error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resize operation failed: {str(e)}")

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{output_filename}",
        "original_filename": original_filename,
        "output_filename": output_filename,
        "tool_type": tool_type,
        "duration_ms": duration_ms,
        "stats": stats
    }

@app.post("/api/merge")
async def handle_merge(
    files: list[UploadFile] = File(...)
):
    if not files or len(files) < 2:
        raise HTTPException(status_code=400, detail="Please provide at least 2 files to merge.")

    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    saved_file_paths = []
    total_original_bytes = 0

    try:
        for idx, file in enumerate(files):
            orig_name = file.filename or f"file_{idx}"
            file_path = os.path.join(task_dir, f"{idx:03d}_{orig_name}")
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            total_original_bytes += os.path.getsize(file_path)
            saved_file_paths.append(file_path)

        output_filename = "merged_document.pdf"
        output_path = os.path.join(task_dir, output_filename)

        stats = merge_documents(saved_file_paths, output_path)

    except Exception as e:
        logger.error(f"Merge error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")

    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Merge completed without creating output file.")

    merged_size = os.path.getsize(output_path)
    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{output_filename}",
        "output_filename": output_filename,
        "file_count": len(files),
        "pages": stats.get("pages", 0),
        "original_bytes": total_original_bytes,
        "merged_bytes": merged_size,
        "duration_ms": duration_ms
    }

@app.post("/api/cad/batch-plot")
async def handle_autocad_batch_plot(
    request: Request,
    files: list[UploadFile] = File(...),
    ctb_file: Optional[UploadFile] = File(None),
    printer: str = Form("AutoCAD PDF (High Quality Print).pc3"),
    paper_size: str = Form("ANSI full bleed B (17.00 x 11.00 Inches)"),
    plot_style: str = Form("acad.ctb"),
    plot_area: str = Form("Extents"),
    center_plot: bool = Form(True),
    fit_to_paper: bool = Form(True),
    orientation: str = Form("Landscape"),
    plot_lineweights: bool = Form(True),
    plot_with_styles: bool = Form(True),
    shade_plot: str = Form("Wireframe"),
    merge_output: bool = Form(True)
):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Please upload at least one CAD drawing (.dwg or .dxf).")

    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    saved_dwg_paths = []
    total_dwg_bytes = 0
    for idx, file in enumerate(files):
        orig_name = file.filename or f"drawing_{idx}.dwg"
        clean_name = os.path.basename(orig_name)
        file_path = os.path.join(task_dir, clean_name)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        total_dwg_bytes += os.path.getsize(file_path)
        saved_dwg_paths.append(file_path)

    user, ip, quota = enforce_quota(request, total_dwg_bytes)

    # Batch limit check for guest/free
    if len(saved_dwg_paths) > 2 and quota["tier"] == "guest":
        raise HTTPException(
            status_code=403,
            detail="Batch plotting more than 2 drawings at once requires a Free Account or Pro Plan. Please sign in or upgrade."
        )

    custom_ctb_path = None
    if ctb_file and ctb_file.filename:
        ctb_name = os.path.basename(ctb_file.filename)
        custom_ctb_path = os.path.join(task_dir, ctb_name)
        with open(custom_ctb_path, "wb") as f:
            shutil.copyfileobj(ctb_file.file, f)
        plot_style = ctb_name

    try:
        plot_result = await asyncio.to_thread(
            batch_plot_dwg,
            dwg_paths=saved_dwg_paths,
            job_dir=task_dir,
            printer=printer,
            paper_size=paper_size,
            plot_style=plot_style,
            plot_area=plot_area,
            center_plot=center_plot,
            fit_to_paper=fit_to_paper,
            orientation=orientation,
            plot_lineweights=plot_lineweights,
            plot_with_styles=plot_with_styles,
            shade_plot=shade_plot,
            custom_ctb_path=custom_ctb_path,
            merge_output=merge_output
        )
    except Exception as e:
        logger.error(f"AutoCAD batch plot error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AutoCAD Batch Plot failed: {str(e)}")

    output_filename = plot_result["output_filename"]
    preview_url = None
    if plot_result.get("preview_thumbnail"):
        preview_url = f"/api/download/{task_id}/{plot_result['preview_thumbnail']}"

    database.log_conversion(
        operation="AutoCAD_Batch_Plot",
        source_filename=f"{len(saved_dwg_paths)} DWG/DXF files",
        target_format=os.path.splitext(output_filename)[1].lstrip("."),
        file_size_bytes=plot_result["file_size"],
        duration_ms=plot_result["duration_ms"],
        user_id=user["id"] if user else None,
        ip_address=ip
    )

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{urllib.parse.quote(output_filename)}",
        "output_filename": output_filename,
        "sheets_plotted": plot_result["sheets_plotted"],
        "total_files": plot_result["total_files"],
        "duration_ms": plot_result["duration_ms"],
        "file_size": plot_result["file_size"],
        "printer": printer,
        "paper_size": paper_size,
        "plot_style": plot_style,
        "preview_url": preview_url,
        "preview_data_url": plot_result.get("preview_data_url"),
        "is_unified_booklet": plot_result.get("is_unified_booklet", False),
        "quota": {
            "tier": quota["tier"],
            "used_today": quota["used_today"],
            "limit": quota["limit"],
            "remaining": quota["remaining"]
        }
    }

# =====================================================================
# PDF OPERATIONS STUDIO & CONVERTAPI MATRIX ENDPOINTS
# =====================================================================

@app.get("/api/converters/matrix")
def get_conversion_matrix():
    from format_registry import get_full_conversion_matrix
    return {"matrix": get_full_conversion_matrix()}

@app.post("/api/pdf/{operation}")
async def handle_pdf_operation(
    operation: str,
    request: Request,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None)
):
    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    filename = file.filename or "document.pdf"
    base_name = os.path.splitext(filename)[0]
    input_path = os.path.join(task_dir, filename)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    original_size = os.path.getsize(input_path)
    user, ip, quota = enforce_quota(request, original_size)

    opts = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            pass

    try:
        raw_form = await request.form()
        for k, v in raw_form.items():
            if k not in opts and k not in ("file", "options"):
                opts[k] = v
    except Exception:
        pass

    from converters import pdf_tools

    try:
        if operation == "split":
            ranges = opts.get("ranges", "1")
            burst = opts.get("burst", False)
            res = pdf_tools.split_pdf(input_path, task_dir, page_ranges=ranges, burst=burst)
            final_output = res["output_path"]
            out_filename = res["filename"]
            meta = {"pages": res["page_count"], "mode": res["mode"]}

        elif operation == "rotate":
            angle = int(opts.get("angle", 90))
            ranges = opts.get("ranges")
            out_filename = f"{base_name}_rotated.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.rotate_pdf(input_path, final_output, angle=angle, page_ranges=ranges)
            meta = {"rotated": res["rotated_pages"], "angle": angle}

        elif operation == "delete-pages":
            pages_to_del = opts.get("pages", "")
            out_filename = f"{base_name}_trimmed.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.delete_pages(input_path, final_output, pages_to_delete=pages_to_del)
            meta = {"deleted": res["deleted_count"], "remaining": res["remaining_pages"]}

        elif operation == "protect":
            user_pw = opts.get("password", "")
            owner_pw = opts.get("owner_password")
            out_filename = f"{base_name}_protected.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.protect_pdf(input_path, final_output, user_password=user_pw, owner_password=owner_pw)
            meta = {"encryption": res["encryption"], "pages": res["pages"]}

        elif operation == "unlock":
            pw = opts.get("password", "")
            out_filename = f"{base_name}_unlocked.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.unlock_pdf(input_path, final_output, password=pw)
            meta = {"pages": res["pages"], "decrypted": True}

        elif operation == "redact":
            keywords = opts.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            out_filename = f"{base_name}_redacted.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.redact_pdf(input_path, final_output, keywords=keywords)
            meta = {"redactions": res["redactions_applied"], "pages": res["pages"]}

        elif operation == "flatten":
            out_filename = f"{base_name}_flattened.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.flatten_pdf(input_path, final_output)
            meta = {"flattened_fields": res["flattened_fields"], "pages": res["pages"]}

        elif operation == "repair":
            out_filename = f"{base_name}_repaired.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.repair_pdf(input_path, final_output)
            meta = {"pages": res["repaired_pages"], "status": res["status"]}

        elif operation == "extract-images":
            res = pdf_tools.extract_images_from_pdf(input_path, task_dir)
            final_output = res["output_path"]
            out_filename = res["filename"]
            meta = {"images_extracted": res["images_extracted"]}

        elif operation == "to-word":
            out_filename = f"{base_name}.docx"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.pdf_to_word(input_path, final_output)
            meta = {"format": "DOCX"}

        elif operation == "to-excel":
            out_filename = f"{base_name}.xlsx"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.pdf_to_excel(input_path, final_output)
            meta = {"tables": res["tables_extracted"], "pages": res["pages_processed"]}

        elif operation == "to-pptx":
            out_filename = f"{base_name}.pptx"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.pdf_to_powerpoint(input_path, final_output)
            meta = {"slides": res["slides"]}

        elif operation == "to-images":
            fmt = opts.get("format", "png")
            res = pdf_tools.pdf_to_images(input_path, task_dir, fmt=fmt)
            final_output = res["output_path"]
            out_filename = res["filename"]
            meta = {"pages": res["pages"]}

        elif operation == "pdfa":
            level = opts.get("level", "PDF/A-1b")
            out_filename = f"{base_name}_pdfa.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.pdf_to_pdfa(input_path, final_output, level=level)
            meta = {"standard": level, "pages": res["pages"]}

        elif operation == "print-ready":
            dpi = int(opts.get("dpi", 300))
            out_filename = f"{base_name}_print_ready.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.print_ready_pdf(input_path, final_output, dpi=dpi)
            meta = {"dpi": dpi, "pages": res["pages"]}

        elif operation in ("page-numbers", "number-pages"):
            pos = opts.get("position", "bottom-center")
            fmt = opts.get("format", "Page {page} of {total}")
            out_filename = f"{base_name}_numbered.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.add_page_numbers(input_path, final_output, position=pos, format_str=fmt)
            meta = res

        elif operation == "watermark":
            text = opts.get("text", "CONFIDENTIAL")
            angle = float(opts.get("angle", 45.0))
            opacity = float(opts.get("opacity", 0.25))
            out_filename = f"{base_name}_watermarked.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.add_watermark(input_path, final_output, text=text, opacity=opacity, angle=angle)
            meta = res

        elif operation == "crop":
            margin = float(opts.get("margin", 0.05))
            out_filename = f"{base_name}_cropped.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.crop_pdf(input_path, final_output, margin_pct=margin)
            meta = res

        elif operation == "sign":
            signer = opts.get("signer", "Musthaque Ali")
            reason = opts.get("reason", "Approved & Verified")
            page_n = int(opts.get("page", 1))
            s_type = opts.get("sig_type", "simple")
            inits = opts.get("initials")
            pos = opts.get("position", "bottom-right")
            out_filename = f"{base_name}_signed.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.sign_pdf(input_path, final_output, signer_name=signer, reason=reason, page_num=page_n, sig_type=s_type, initials=inits, position=pos)
            meta = res

        elif operation in ("organize", "extract-pages"):
            ranges = opts.get("ranges", "1")
            res = pdf_tools.split_pdf(input_path, task_dir, page_ranges=ranges)
            final_output = res["output_path"]
            out_filename = res["filename"]
            meta = res

        elif operation in ("scan-to-pdf", "scan"):
            out_filename = f"{base_name}_scan.pdf"
            final_output = os.path.join(task_dir, out_filename)
            res = pdf_tools.scan_to_pdf(input_path, final_output)
            meta = res

        elif operation == "ocr":
            from converters import ai_service
            ocr_res = ai_service.ocr_document_ai(input_path)
            out_filename = f"{base_name}_ocr.txt"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                f.write(ocr_res["extracted_text"])
            meta = {"characters": ocr_res["characters"], "method": ocr_res["method"]}


        else:
            raise HTTPException(status_code=400, detail=f"Unsupported PDF operation: {operation}")

    except Exception as e:
        logger.error(f"PDF operation error [{operation}]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Operation '{operation}' failed: {str(e)}")

    duration_ms = int((time.time() - start_time) * 1000)
    file_size = os.path.getsize(final_output) if os.path.exists(final_output) else 0

    database.log_conversion(
        operation=f"PDF_{operation}",
        source_filename=filename,
        target_format="pdf",
        file_size_bytes=file_size,
        duration_ms=duration_ms,
        user_id=user["id"] if user else None,
        ip_address=ip
    )

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{urllib.parse.quote(out_filename)}",
        "output_filename": out_filename,
        "operation": operation,
        "duration_ms": duration_ms,
        "file_size": file_size,
        "meta": meta,
        "quota": {
            "tier": quota["tier"],
            "used_today": quota["used_today"],
            "limit": quota["limit"],
            "remaining": quota["remaining"]
        }
    }


@app.post("/api/ai/chat")
async def handle_ai_chat(request: Request):
    start_time = time.time()
    form = await request.form()
    messages_raw = form.get("messages", "[]")
    system_instruction = form.get("system_instruction")

    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    input_path = None
    original_size = 1000
    file_upload = form.get("file")
    if file_upload and hasattr(file_upload, "filename") and file_upload.filename:
        input_path = os.path.join(task_dir, file_upload.filename)
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file_upload.file, f)
        original_size = os.path.getsize(input_path)

    user = get_current_user_optional(request)
    ip = get_client_ip(request)
    # Generous allowance for interactive AI Chat conversations
    quota = {"tier": (user.get("tier") if user else "guest"), "allowed": True, "limit": 100, "used_today": 1, "remaining": 99}

    try:
        msgs = json.loads(messages_raw)
    except Exception:
        msgs = [{"role": "user", "content": str(messages_raw)}]

    from converters import ai_service
    try:
        result = ai_service.chat_completion(
            messages=msgs,
            file_path=input_path,
            system_instruction=system_instruction
        )
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI Chat failed: {str(e)}")

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "reply": result["reply"],
        "artifact": result.get("artifact"),
        "model_used": result.get("model_used"),
        "has_file": result.get("has_file", False),
        "duration_ms": duration_ms,
        "quota": {
            "tier": quota.get("tier", "guest"),
            "used_today": quota.get("used_today", 0),
            "limit": quota.get("limit", 3),
            "remaining": quota.get("remaining", 0)
        }
    }


@app.post("/api/ai/{operation}")
async def handle_ai_operation(
    operation: str,
    request: Request,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None)
):
    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    filename = file.filename or "document.pdf"
    base_name = os.path.splitext(filename)[0]
    input_path = os.path.join(task_dir, filename)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    original_size = os.path.getsize(input_path)
    user, ip, quota = enforce_quota(request, original_size)

    opts = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            pass

    from converters import ai_service

    try:
        if operation == "summarize":
            mode = opts.get("mode", "executive")
            res = ai_service.summarize_document(input_path, mode=mode)
            out_filename = f"{base_name}_summary.md"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                f.write(f"# Document Summary: {filename}\n\n" + res["summary_markdown"])
            meta = {"mode": mode, "markdown": res["summary_markdown"], "model": res.get("model_used")}

        elif operation == "translate":
            target_lang = opts.get("language", "Spanish")
            res = ai_service.translate_document(input_path, target_language=target_lang)
            out_filename = f"{base_name}_translated_{target_lang.lower()}.md"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                f.write(f"# Translated ({target_lang}): {filename}\n\n" + res["translated_text"])
            meta = {"target_language": target_lang, "content": res["translated_text"]}

        elif operation in ("pdf-to-markdown", "markdown"):
            res = ai_service.pdf_to_markdown_ai(input_path)
            out_filename = f"{base_name}.md"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                f.write(res["markdown_content"])
            meta = {"content": res["markdown_content"]}

        elif operation == "ocr":
            res = ai_service.ocr_document_ai(input_path)
            out_filename = f"{base_name}_ocr.txt"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                f.write(res["extracted_text"])
            meta = {"characters": res["characters"], "content": res["extracted_text"]}

        elif operation == "image-watermark-assist":
            with open(input_path, "rb") as im_f:
                res = ai_service.ai_watermark_assist(im_f.read())
            out_filename = f"{base_name}_watermark_ai.json"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            meta = res

        elif operation == "image-sign-assist":
            with open(input_path, "rb") as im_f:
                res = ai_service.ai_sign_assist(im_f.read())
            out_filename = f"{base_name}_sign_ai.json"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            meta = res

        elif operation == "image-meme-assist":
            with open(input_path, "rb") as im_f:
                res = ai_service.ai_meme_assist(im_f.read())
            out_filename = f"{base_name}_meme_ai.json"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            meta = res

        elif operation == "image-photo-enhance":
            with open(input_path, "rb") as im_f:
                res = ai_service.ai_photo_enhance(im_f.read())
            out_filename = f"{base_name}_photo_enhance.json"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            meta = res

        elif operation == "image-caption":
            with open(input_path, "rb") as im_f:
                res = ai_service.ai_image_caption(im_f.read())
            out_filename = f"{base_name}_caption.json"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            meta = res

        elif operation == "image-ocr":
            with open(input_path, "rb") as im_f:
                res = ai_service.ai_image_ocr(im_f.read())
            out_filename = f"{base_name}_extracted.md"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                f.write(res["extracted_markdown"])
            meta = {"markdown": res["extracted_markdown"], "model": res.get("model_used")}

        elif operation == "cad-titleblock-inspect":
            res = ai_service.ai_cad_titleblock_inspect(input_path)
            out_filename = f"{base_name}_cad_metadata.json"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            meta = res

        elif operation == "contract-audit":
            res = ai_service.ai_contract_risk_audit(input_path)
            out_filename = f"{base_name}_contract_risk_audit.json"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            meta = res

        elif operation == "extract-financial-table":
            res = ai_service.ai_extract_financial_table(input_path)
            out_filename = f"{base_name}_financial_table.md"
            final_output = os.path.join(task_dir, out_filename)
            with open(final_output, "w", encoding="utf-8") as f:
                f.write(res["extracted_table"])
            meta = {"table": res["extracted_table"]}

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported AI operation: {operation}")

    except Exception as e:
        logger.error(f"AI operation error [{operation}]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI Operation '{operation}' failed: {str(e)}")

    duration_ms = int((time.time() - start_time) * 1000)
    file_size = os.path.getsize(final_output) if os.path.exists(final_output) else 0

    database.log_conversion(
        operation=f"AI_{operation}",
        source_filename=filename,
        target_format="md",
        file_size_bytes=file_size,
        duration_ms=duration_ms,
        user_id=user["id"] if user else None,
        ip_address=ip
    )

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{urllib.parse.quote(out_filename)}",
        "output_filename": out_filename,
        "operation": operation,
        "duration_ms": duration_ms,
        "file_size": file_size,
        "meta": meta,
        "quota": {
            "tier": quota.get("tier", "guest"),
            "used_today": quota.get("used_today", 0),
            "limit": quota.get("limit", 3),
            "remaining": quota.get("remaining", 0)
        }
    }


@app.post("/api/image/{operation}")
async def handle_image_operation(
    operation: str,
    request: Request,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None)
):
    start_time = time.time()
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    filename = file.filename or "image.jpg"
    base_name = os.path.splitext(filename)[0]
    input_path = os.path.join(task_dir, filename)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    original_size = os.path.getsize(input_path)
    user, ip, quota = enforce_quota(request, original_size)

    opts = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            pass

    from converters import image_tools

    try:
        if operation == "compress":
            quality = int(opts.get("quality", 75))
            target_fmt = opts.get("target_format", "keep")
            out_ext = "webp" if target_fmt == "webp" else "png" if target_fmt == "png" else "jpg"
            out_filename = f"{base_name}_compressed.{out_ext}"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.compress_image(input_path, final_output, quality=quality, target_format=target_fmt)

        elif operation == "resize":
            w = int(opts.get("width", 0)) or None
            h = int(opts.get("height", 0)) or None
            s_pct = int(opts.get("scale_pct", 0)) or None
            resample_m = opts.get("resample", "lanczos")
            out_filename = f"{base_name}_resized.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.resize_image(input_path, final_output, width=w, height=h, scale_pct=s_pct, resample=resample_m)

        elif operation == "crop":
            ar = opts.get("aspect_ratio")
            left = int(opts.get("left", 0))
            top = int(opts.get("top", 0))
            width = int(opts["width"]) if opts.get("width") else None
            height = int(opts["height"]) if opts.get("height") else None
            out_filename = f"{base_name}_cropped.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.crop_image(input_path, final_output, left=left, top=top, width=width, height=height, aspect_ratio=ar)

        elif operation == "photo-editor":
            brightness = float(opts.get("brightness", 1.0))
            contrast = float(opts.get("contrast", 1.0))
            saturation = float(opts.get("saturation", 1.0))
            sharpness = float(opts.get("sharpness", 1.0))
            p_filter = opts.get("filter")
            out_filename = f"{base_name}_edited.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.photo_editor(input_path, final_output, brightness=brightness, contrast=contrast, saturation=saturation, sharpness=sharpness, preset_filter=p_filter)

        elif operation == "upscale":
            scale = int(opts.get("scale", 2))
            out_filename = f"{base_name}_{scale}x_upscaled.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.upscale_image(input_path, final_output, scale=scale)

        elif operation == "remove-background":
            out_filename = f"{base_name}_nobg.png"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.remove_background(input_path, final_output)

        elif operation == "watermark":
            w_text = opts.get("text", "CONFIDENTIAL")
            opacity = float(opts.get("opacity", 0.5))
            f_size = int(opts.get("font_size", 40))
            pos = opts.get("position", "center")
            angle = float(opts.get("angle", 0.0))
            color_hex = opts.get("color", "#ffffff")
            tile = bool(opts.get("tile", False))
            c_x = float(opts["custom_x"]) if opts.get("custom_x") is not None else None
            c_y = float(opts["custom_y"]) if opts.get("custom_y") is not None else None
            out_filename = f"{base_name}_watermarked.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.watermark_image(
                input_path, final_output,
                text=w_text, opacity=opacity, font_size=f_size,
                position=pos, angle=angle, color_hex=color_hex, tile=tile,
                custom_x=c_x, custom_y=c_y
            )

        elif operation == "sign":
            signer = opts.get("signer", "Musthaque Ali")
            inits = opts.get("initials")
            s_type = opts.get("sig_type", "simple")
            reason = opts.get("reason", "Approved & Verified")
            pos = opts.get("position", "bottom-right")
            c_x = float(opts["custom_x"]) if opts.get("custom_x") is not None else None
            c_y = float(opts["custom_y"]) if opts.get("custom_y") is not None else None
            out_filename = f"{base_name}_signed.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.sign_image(
                input_path, final_output,
                signer_name=signer, initials=inits, sig_type=s_type,
                reason=reason, position=pos, custom_x=c_x, custom_y=c_y
            )

        elif operation == "meme-generator":
            top = opts.get("top_text", "")
            bot = opts.get("bottom_text", "")
            out_filename = f"{base_name}_meme.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.meme_generator(input_path, final_output, top_text=top, bottom_text=bot)

        elif operation == "rotate":
            angle = int(opts.get("angle", 90))
            flip_h = bool(opts.get("flip_h", False))
            flip_v = bool(opts.get("flip_v", False))
            out_filename = f"{base_name}_rotated.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.rotate_image_tool(input_path, final_output, angle=angle, flip_h=flip_h, flip_v=flip_v)

        elif operation == "blur-face":
            strength = int(opts.get("blur_strength", 35))
            out_filename = f"{base_name}_faceblur.jpg"
            final_output = os.path.join(task_dir, out_filename)
            meta = image_tools.blur_face(input_path, final_output, blur_strength=strength)

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported Image operation: {operation}")

    except Exception as e:
        logger.error(f"Image operation error [{operation}]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image Operation '{operation}' failed: {str(e)}")

    duration_ms = int((time.time() - start_time) * 1000)
    file_size = os.path.getsize(final_output) if os.path.exists(final_output) else 0

    database.log_conversion(
        operation=f"IMG_{operation}",
        source_filename=filename,
        target_format="jpg",
        file_size_bytes=file_size,
        duration_ms=duration_ms,
        user_id=user["id"] if user else None,
        ip_address=ip
    )

    return {
        "task_id": task_id,
        "download_url": f"/api/download/{task_id}/{urllib.parse.quote(out_filename)}",
        "output_filename": out_filename,
        "operation": operation,
        "duration_ms": duration_ms,
        "file_size": file_size,
        "meta": meta,
        "quota": {
            "tier": quota.get("tier", "guest"),
            "used_today": quota.get("used_today", 0),
            "limit": quota.get("limit", 3),
            "remaining": quota.get("remaining", 0)
        }
    }

@app.get("/api/download/{task_id}/{filename}")
def download_file(task_id: str, filename: str):
    import mimetypes
    file_path = os.path.join(TEMP_DIR, task_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    guessed_type, _ = mimetypes.guess_type(filename)
    media_type = guessed_type or "application/octet-stream"
    headers = {
        "Cache-Control": "public, max-age=86400, stale-while-revalidate=604800",
        "Access-Control-Allow-Origin": "*"
    }
    return FileResponse(file_path, filename=filename, media_type=media_type, headers=headers)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
def serve_home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.api_route("/robots.txt", methods=["GET", "HEAD"])
def serve_robots():
    return FileResponse(os.path.join(STATIC_DIR, "robots.txt"), media_type="text/plain")

@app.api_route("/sitemap.xml", methods=["GET", "HEAD"])
def serve_sitemap():
    return FileResponse(os.path.join(STATIC_DIR, "sitemap.xml"), media_type="application/xml")

@app.api_route("/googlef55b91c8df10fa26.html", methods=["GET", "HEAD"])
def serve_google_verification():
    return FileResponse(os.path.join(STATIC_DIR, "googlef55b91c8df10fa26.html"), media_type="text/html")
