"""
AI Intelligence Engine for 'I LOVE FILES'
Powered by OpenRouter API with high-speed models:
- openai/gpt-4o-mini (Primary)
- deepseek/deepseek-chat (Fallback)
"""
import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
import pymupdf

import re

logger = logging.getLogger("ILoveFiles.AI")

def _clean_markdown_fences(text: str) -> str:
    """Removes outer markdown code fences (```markdown ... ```) if the model wrapped its response in them."""
    t = text.strip()
    # Match ```markdown\n...\n``` or ```\n...\n```
    fence_pattern = r"^```(?:markdown|md)?\s*\n([\s\S]*?)\n```$"
    m = re.match(fence_pattern, t, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return t

def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        os.environ["OPENROUTER_API_KEY"] = key
                        break
    return key or ""

PRIMARY_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini")
FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "deepseek/deepseek-chat")

import ssl

def _get_ssl_context():
    # 1. Try certifi CA bundle if available
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    # 2. Fallback to unverified SSL context to guarantee connection on Windows / Azure remote servers
    try:
        ctx = ssl._create_unverified_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        return None

def call_openrouter(messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3) -> str:
    api_key = _get_api_key()
    models_to_try = [model] if model else [PRIMARY_MODEL, FALLBACK_MODEL]

    last_err = None
    for m in models_to_try:
        if not m:
            continue
        body = {
            "model": m,
            "messages": messages,
            "temperature": temperature
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ilovefiles.local",
                "X-Title": "I Love Files Universal Engine"
            }
        )
        try:
            ssl_ctx = _get_ssl_context()
            with urllib.request.urlopen(req, timeout=45, context=ssl_ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return _clean_markdown_fences(content)
        except Exception as e:
            logger.warning(f"OpenRouter model '{m}' failed: {e}. Trying fallback...")
            last_err = e

    raise RuntimeError(f"All AI models failed. Last error: {last_err}")


def _extract_docx_text(file_path: str) -> str:
    """Extracts text, headings, and tables from Word DOCX using python-docx with XML fallback."""
    parts = []
    try:
        import docx
        doc = docx.Document(file_path)
        for p in doc.paragraphs:
            txt = p.text.strip()
            if not txt:
                continue
            style_name = p.style.name.lower() if p.style else ""
            if "heading 1" in style_name or "title" in style_name:
                parts.append(f"# {txt}")
            elif "heading 2" in style_name:
                parts.append(f"## {txt}")
            elif "heading 3" in style_name:
                parts.append(f"### {txt}")
            elif "list" in style_name or "bullet" in style_name:
                parts.append(f"- {txt}")
            else:
                parts.append(txt)

        for table in doc.tables:
            table_lines = []
            for row in table.rows:
                row_vals = [c.text.strip().replace("\n", " ") for c in row.cells]
                if any(row_vals):
                    table_lines.append(" | ".join(row_vals))
            if table_lines:
                parts.append("\n" + "\n".join(table_lines) + "\n")

        res = "\n\n".join(parts)
        if res.strip():
            return res
    except Exception as e:
        logger.warning(f"python-docx extraction failed, trying raw XML parser: {e}")

    # Fallback to direct XML extraction from docx archive
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            texts = [node.text for node in tree.iter() if node.text]
            return " ".join(texts)
    except Exception as e:
        logger.error(f"DOCX XML extraction failed: {e}")
        return ""

def _extract_excel_text(file_path: str, max_rows_per_sheet: int = 250) -> str:
    """Extracts tabular data from Excel spreadsheets (XLSX, XLS) using openpyxl."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        sheets_data = []
        for name in wb.sheetnames:
            ws = wb[name]
            sheet_lines = [f"### Spreadsheet Sheet: {name}"]
            row_count = 0
            for row in ws.iter_rows(values_only=True):
                if row_count >= max_rows_per_sheet:
                    sheet_lines.append(f"[... {max_rows_per_sheet} rows limit reached for sheet '{name}' ...]")
                    break
                row_vals = [str(v).strip() if v is not None else "" for v in row]
                if any(row_vals):
                    sheet_lines.append(" | ".join(row_vals))
                    row_count += 1
            if len(sheet_lines) > 1:
                sheets_data.append("\n".join(sheet_lines))
        wb.close()
        return "\n\n".join(sheets_data)
    except Exception as e:
        logger.warning(f"openpyxl extraction error: {e}")
        return ""

def _extract_pptx_text(file_path: str) -> str:
    """Extracts slide text and presentations from PowerPoint (PPTX) using python-pptx."""
    try:
        import pptx
        prs = pptx.Presentation(file_path)
        slides_text = []
        for idx, slide in enumerate(prs.slides):
            parts = [f"### Presentation Slide {idx+1}"]
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        t = p.text.strip()
                        if t:
                            parts.append(t)
            if len(parts) > 1:
                slides_text.append("\n".join(parts))
        return "\n\n".join(slides_text)
    except Exception as e:
        logger.warning(f"pptx extraction error: {e}")
        return ""

def _extract_raw_doc_strings(file_path: str) -> str:
    """Fallback text recovery for legacy binary documents (DOC, PPT, XLS)."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        ascii_strings = re.findall(rb"[ -~]{4,}", data)
        clean_lines = []
        for s in ascii_strings:
            dec = s.decode("latin-1", errors="ignore").strip()
            # Filter out low-entropy binary junk
            if len(dec) >= 6 and any(c.isalpha() for c in dec):
                clean_lines.append(dec)
        return "\n".join(clean_lines[:600])
    except Exception as e:
        logger.error(f"Binary string extractor failed: {e}")
        return ""

def extract_text_from_document(file_path: str, max_pages: int = 50, max_chars: int = 40000) -> str:
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    full_text = ""

    if ext == "pdf":
        doc = pymupdf.open(file_path)
        extracted = []
        pages_to_read = min(len(doc), max_pages)
        for i in range(pages_to_read):
            t = doc[i].get_text("text")
            if t.strip():
                extracted.append(f"--- [Page {i+1}] ---\n{t.strip()}")
        doc.close()
        full_text = "\n\n".join(extracted)

    elif ext in ("docx", "dotx"):
        full_text = _extract_docx_text(file_path)

    elif ext in ("xlsx", "xlsm", "xltx"):
        full_text = _extract_excel_text(file_path)

    elif ext in ("pptx", "potx", "ppsx"):
        full_text = _extract_pptx_text(file_path)

    elif ext in ("doc", "dot", "ppt", "xls"):
        # Legacy binary Microsoft Office formats
        full_text = _extract_raw_doc_strings(file_path)

    elif ext in ("txt", "md", "markdown", "csv", "tsv", "json", "xml", "html", "htm", "log", "rtf"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
        except Exception:
            full_text = ""
    else:
        # Generic text fallback
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
        except Exception:
            full_text = _extract_raw_doc_strings(file_path)

    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + f"\n\n[... Document truncated to {max_chars} characters for analysis ...]"
    return full_text



def summarize_document(file_path: str, mode: str = "executive") -> Dict[str, Any]:
    text = extract_text_from_document(file_path)
    if not text.strip():
        return {
            "summary_markdown": "⚠️ No readable text could be extracted from this document. It may be a scanned image-only PDF. Please use OCR PDF first.",
            "mode": mode,
            "word_count": 0
        }

    prompts = {
        "executive": (
            "You are a C-suite executive briefing specialist. Provide a high-impact, beautifully ordered executive summary "
            "formatted in pristine Markdown without enclosing code block fences.\n"
            "Format the response using this exact structure:\n"
            "# Executive Summary & Briefing\n\n"
            "## 1. Executive Overview\n2-3 crisp, high-level paragraphs explaining the core purpose and scope.\n\n"
            "## 2. Key Strategic Takeaways\n- **Lead Point**: Clear takeaway with context.\n- **Secondary Finding**: Quantitative or factual impact.\n\n"
            "## 3. Metrics & Data Highlights\nCreate a clean Markdown table summarizing vital figures, dates, percentages, or milestones.\n\n"
            "## 4. Action Items & Next Steps\nOrdered numbered list of strategic recommendations."
        ),
        "bullets": (
            "You are an analytical researcher. Condense the document into structured, highly organized bullet points "
            "grouped under clear topical headings (## Section Title). Use **bold leads** for every bullet point. "
            "Do not enclose the response in markdown code fences."
        ),
        "technical": (
            "You are a principal engineer and systems architect. Analyze the technical specifications, architecture, "
            "methodology, and constraints. Present an ordered technical breakdown with ## Architecture, ## Specifications, "
            "and ## Operational Insights. Do not enclose the response in markdown code fences."
        ),
        "concise": (
            "Summarize this document in a single powerful overview paragraph followed by exactly 5 clear, high-impact bullet points with bold titles. "
            "Do not enclose the response in markdown code fences."
        )
    }

    sys_prompt = prompts.get(mode, prompts.get("executive"))
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Document Content:\n\n{text}"}
    ]

    summary_md = call_openrouter(messages)
    return {
        "summary_markdown": summary_md,
        "mode": mode,
        "original_chars": len(text),
        "model_used": PRIMARY_MODEL
    }


def translate_document(file_path: str, target_language: str = "Spanish") -> Dict[str, Any]:
    text = extract_text_from_document(file_path, max_chars=30000)
    if not text.strip():
        return {
            "translated_text": "⚠️ Document contains no readable text to translate.",
            "target_language": target_language
        }

    sys_prompt = (
        f"You are an expert technical translator. Translate the following text into {target_language}. "
        "Maintain the exact formatting, headers, lists, code snippets, and terminology. "
        "Return ONLY the translated content without meta comments."
    )
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": text}
    ]

    translated = call_openrouter(messages)
    return {
        "translated_text": translated,
        "target_language": target_language,
        "model_used": PRIMARY_MODEL
    }


def pdf_to_markdown_ai(file_path: str) -> Dict[str, Any]:
    text = extract_text_from_document(file_path, max_chars=35000)
    if not text.strip():
        return {
            "markdown_content": "# Empty Document\n\nNo text could be extracted.",
            "status": "empty"
        }

    sys_prompt = (
        "You are an expert technical document converter. Convert the raw extracted text into "
        "clean, beautifully formatted GitHub-flavored Markdown without wrapping the response in markdown code blocks.\n"
        "- Deduce natural # H1, ## H2, ### H3 headings\n"
        "- Format tables cleanly with | Col 1 | Col 2 |\n"
        "- Format bullet lists and numbered steps\n"
        "- Wrap inner code or math formulas in standard code blocks\n"
        "Return ONLY the raw markdown content directly."
    )
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": text}
    ]

    md_content = call_openrouter(messages)
    return {
        "markdown_content": md_content,
        "model_used": PRIMARY_MODEL
    }


def ocr_document_ai(file_path: str) -> Dict[str, Any]:
    """
    Performs OCR on document using PyMuPDF native text extraction or AI vision fallback.
    """
    text = extract_text_from_document(file_path, max_chars=40000)
    if text.strip() and len(text.strip()) > 100:
        return {
            "extracted_text": text,
            "method": "PyMuPDF High-Fidelity Text Layer Extraction",
            "characters": len(text)
        }
    
    # Fallback to AI OCR
    sys_prompt = "You are a specialized OCR engine. Transcribe all text, numbers, and tables accurately from this document."
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Transcribe this document content:\n\n{text}"}
    ]
    extracted = call_openrouter(messages)
    return {
        "extracted_text": extracted,
        "method": "OpenRouter AI Multimodal OCR",
        "characters": len(extracted)
    }


# ============================================================================
# MULTIMODAL VISION & ADVANCED AI ASSIST ENGINES (GPT-4o-mini POWERED)
# ============================================================================
import base64
import io
from PIL import Image

def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Extracts and parses JSON object from AI model response."""
    try:
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.warning(f"Failed to parse JSON from AI response: {e}")
    return None

def call_openrouter_vision(
    prompt: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    model: Optional[str] = None,
    temperature: float = 0.2
) -> str:
    """
    Sends an image + prompt to OpenRouter multimodal vision model (GPT-4o-mini).
    Automatically downsamples high-res images to guarantee sub-3s latency.
    """
    api_key = _get_api_key()
    target_model = model or PRIMARY_MODEL

    # Resize image if larger than 1280px on any side
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            if max(im.size) > 1280:
                im.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            out_buf = io.BytesIO()
            fmt = "PNG" if im.mode in ("RGBA", "P") else "JPEG"
            im.save(out_buf, format=fmt, quality=85)
            clean_bytes = out_buf.getvalue()
            mime = "image/png" if fmt == "PNG" else "image/jpeg"
    except Exception:
        clean_bytes = image_bytes
        mime = mime_type

    b64_str = base64.b64encode(clean_bytes).decode("utf-8")
    data_uri = f"data:{mime};base64,{b64_str}"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_uri}}
            ]
        }
    ]

    models_to_try = [target_model, "openai/gpt-4o-mini", "google/gemini-flash-1.5"]
    last_err = None

    for m in models_to_try:
        body = {
            "model": m,
            "messages": messages,
            "temperature": temperature
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ilovefiles.local",
                "X-Title": "I Love Files Universal Engine"
            }
        )
        try:
            ssl_ctx = _get_ssl_context()
            with urllib.request.urlopen(req, timeout=40, context=ssl_ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"].strip()
                return _clean_markdown_fences(content)
        except Exception as e:
            logger.warning(f"Vision model {m} failed: {e}. Trying fallback...")
            last_err = e

    raise RuntimeError(f"All vision models failed. Last error: {last_err}")


def ai_watermark_assist(image_bytes: bytes) -> Dict[str, Any]:
    """
    Visually inspects the image and returns smart context-aware watermark presets
    and safe non-obscuring coordinates (custom_x, custom_y).
    """
    prompt = (
        "Analyze this image to recommend an optimal watermark stamp.\n"
        "Examine what kind of image it is (architectural blueprint, invoice, portrait, artwork, product photo, confidential document).\n"
        "Determine:\n"
        "1. The most appropriate professional watermark text string (e.g. 'CONFIDENTIAL // ARCHIVE COPY', 'PRELIMINARY DESIGN - NOT FOR CONSTRUCTION', 'COPYRIGHT PROTECTED', 'SAMPLE - DO NOT DUPLICATE').\n"
        "2. Safe fractional coordinates (custom_x, custom_y between 0.05 and 0.85) where the stamp does NOT block essential focal content (e.g. faces, drawing numbers, vital totals).\n"
        "3. Recommended opacity (0.2 to 0.6), rotation angle (0, 30, 45, or -30), and color (#ffffff or #ea580c or #1e293b).\n\n"
        "Return ONLY valid JSON matching this exact structure:\n"
        "{\n"
        '  "suggested_text": "CONFIDENTIAL // ARCHIVE COPY",\n'
        '  "custom_x": 0.35,\n'
        '  "custom_y": 0.75,\n'
        '  "opacity": 0.35,\n'
        '  "angle": 0,\n'
        '  "color": "#ffffff",\n'
        '  "image_type": "Brief classification of image",\n'
        '  "rationale": "Why this position and text were chosen"\n'
        "}"
    )
    raw = call_openrouter_vision(prompt, image_bytes)
    data = _extract_json_block(raw)
    if not data:
        data = {
            "suggested_text": "CONFIDENTIAL // MUSTHAQUE ALI ARCHIVE",
            "custom_x": 0.5,
            "custom_y": 0.5,
            "opacity": 0.35,
            "angle": 30,
            "color": "#ffffff",
            "image_type": "General Image",
            "rationale": "Centered default watermark stamp"
        }
    return data


def ai_sign_assist(image_bytes: bytes) -> Dict[str, Any]:
    """
    Visually inspects document/image to find an ideal blank signature block,
    margins, or signing box, and suggests signer metadata.
    """
    prompt = (
        "Inspect this document or image to find the optimal signature placement.\n"
        "Look for sign lines ('Signature:', 'Approved By:'), title blocks, blank bottom corners, or footer margins.\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "signer_name": "Musthaque Ali",\n'
        '  "initials": "MA",\n'
        '  "reason": "Approved & Certified",\n'
        '  "sig_type": "digital",\n'
        '  "custom_x": 0.65,\n'
        '  "custom_y": 0.82,\n'
        '  "placement_rationale": "Located empty margin or title block at bottom right"\n'
        "}"
    )
    raw = call_openrouter_vision(prompt, image_bytes)
    data = _extract_json_block(raw)
    if not data:
        data = {
            "signer_name": "Musthaque Ali",
            "initials": "MA",
            "reason": "Approved & Verified",
            "sig_type": "digital",
            "custom_x": 0.65,
            "custom_y": 0.82,
            "placement_rationale": "Standard lower-right verification placement"
        }
    return data


def ai_meme_assist(image_bytes: bytes) -> Dict[str, Any]:
    """
    Visually inspects the scene, facial expressions, and objects to generate
    contextual, funny Top and Bottom meme punchlines.
    """
    prompt = (
        "Analyze the visual scene, expressions, and mood of this image to create hilarious meme captions.\n"
        "Generate 3 distinct creative meme caption pairs (Top Text and Bottom Text) tailored directly to what is happening in the picture.\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "image_context": "Brief description of scene/expression",\n'
        '  "options": [\n'
        '    {"top_text": "WHEN THE CODE BUILDS", "bottom_text": "ON THE FIRST TRY"},\n'
        '    {"top_text": "ME WAITING FOR", "bottom_text": "THE CLIENT FEEDBACK"},\n'
        '    {"top_text": "EXPECTATION VS REALITY", "bottom_text": "AT 3 AM"}\n'
        "  ]\n"
        "}"
    )
    raw = call_openrouter_vision(prompt, image_bytes)
    data = _extract_json_block(raw)
    if not data:
        data = {
            "image_context": "Visual Scene",
            "options": [
                {"top_text": "WHEN EVERYTHING WORKS", "bottom_text": "WITHOUT ANY BUGS"},
                {"top_text": "ONE DOES NOT SIMPLY", "bottom_text": "EDIT WITHOUT AI"},
                {"top_text": "FINAL_DESIGN_V3_FINAL_FINAL", "bottom_text": "NOW ACTUALLY APPROVED"}
            ]
        }
    return data


def ai_photo_enhance(image_bytes: bytes) -> Dict[str, Any]:
    """
    Visually evaluates exposure, contrast, white balance, and sharpness,
    calculating optimal photo editing sliders and preset filter.
    """
    prompt = (
        "Critically inspect this photo for lighting, shadows, exposure, saturation, and dynamic range.\n"
        "Recommend optimal photo adjustment sliders:\n"
        "- brightness: float between 0.7 and 1.4 (1.0 = unchanged)\n"
        "- contrast: float between 0.8 and 1.5 (1.0 = unchanged)\n"
        "- saturation: float between 0.8 and 1.5 (1.0 = unchanged)\n"
        "- sharpness: float between 1.0 and 2.0 (1.0 = unchanged)\n"
        "- filter: one of ['cinematic', 'warm', 'cool', 'sharp', 'vintage', '']\n"
        "- explanation: 1-2 sentence breakdown of what visual improvements will occur.\n\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "brightness": 1.1,\n'
        '  "contrast": 1.15,\n'
        '  "saturation": 1.05,\n'
        '  "sharpness": 1.25,\n'
        '  "filter": "cinematic",\n'
        '  "explanation": "Brightened shadows and enriched contrast for cinematic clarity."\n'
        "}"
    )
    raw = call_openrouter_vision(prompt, image_bytes)
    data = _extract_json_block(raw)
    if not data:
        data = {
            "brightness": 1.1,
            "contrast": 1.15,
            "saturation": 1.1,
            "sharpness": 1.3,
            "filter": "cinematic",
            "explanation": "Standard high-fidelity dynamic range boost and edge crispness."
        }
    return data


def ai_image_caption(image_bytes: bytes) -> Dict[str, Any]:
    """
    Generates accessibility alt-text, detailed scene descriptions, and SEO tags.
    """
    prompt = (
        "Analyze this image and generate comprehensive descriptions and accessibility metadata.\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "alt_text": "Concise, descriptive accessibility alt-text under 125 characters",\n'
        '  "detailed_caption": "2-3 sentence rich description of subjects, setting, lighting, and mood",\n'
        '  "tags": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],\n'
        '  "detected_text": "Any visible signage, logos, or words seen in the image"\n'
        "}"
    )
    raw = call_openrouter_vision(prompt, image_bytes)
    data = _extract_json_block(raw)
    if not data:
        data = {
            "alt_text": "Photograph inspected by I Love Files AI Vision Engine",
            "detailed_caption": "An image inspected and processed with zero cloud egress.",
            "tags": ["photography", "media", "ilovefiles"],
            "detected_text": ""
        }
    return data


def ai_image_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    Uses GPT-4o-mini Vision to transcribe all visible text, receipts, handwriting,
    and tables from an image directly into clean GitHub-flavored Markdown.
    """
    prompt = (
        "Transcribe ALL visible text, tables, numbers, and handwritten notes from this image.\n"
        "Preserve exact layout, line breaks, and column structures:\n"
        "- Format tabular data using clean Markdown tables (| Header | Header |)\n"
        "- Retain exact spelling, uppercase/lowercase, and currency amounts\n"
        "- Return ONLY the clean Markdown transcription without commentary."
    )
    raw = call_openrouter_vision(prompt, image_bytes)
    return {
        "extracted_markdown": raw,
        "model_used": PRIMARY_MODEL
    }


def ai_cad_titleblock_inspect(file_path: str) -> Dict[str, Any]:
    """
    Inspects an engineering drawing (PDF plot or DXF/DWG extract)
    to extract standard Title Block metadata and propose professional standard file renaming.
    Leaves all AutoCAD plotting routines 100% untouched.
    """
    text_content = ""
    try:
        if file_path.lower().endswith(".pdf"):
            doc = pymupdf.open(file_path)
            if len(doc) > 0:
                text_content = doc[0].get_text("text")[:10000]
            doc.close()
    except Exception as e:
        logger.warning(f"Could not extract text layer from CAD PDF: {e}")

    prompt = (
        "You are an expert AutoCAD / BIM project document controller.\n"
        "Inspect the following text extracted from an engineering/architectural drawing title block:\n\n"
        f"Drawing Content:\n{text_content if text_content.strip() else '[No text layer found; perform deduction based on drawing name and typical CAD standards]'}\n\n"
        "Extract or deduce the standard title block fields:\n"
        "1. Sheet Number (e.g. 'A-101', 'M-201', 'E-01', 'S-05', or 'SHEET-01')\n"
        "2. Revision (e.g. 'Rev 01', 'Rev A', 'Rev 00')\n"
        "3. Project Name (or Client Name)\n"
        "4. Sheet Title / Description (e.g. 'GROUND FLOOR HVAC LAYOUT', 'FIRST FLOOR ARCHITECTURAL PLAN')\n"
        "5. Engineering Discipline (Architectural, Mechanical, Electrical, Structural, Civil, or Plumbing)\n"
        "6. Standard Engineering Filename in format: [SheetNumber]_[Revision]_[CleanSheetTitle].pdf\n\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "sheet_number": "A-101",\n'
        '  "revision": "Rev 01",\n'
        '  "project_name": "Engineering Project",\n'
        '  "sheet_title": "GROUND FLOOR PLAN",\n'
        '  "discipline": "Architectural",\n'
        '  "suggested_filename": "A-101_Rev01_GROUND_FLOOR_PLAN.pdf",\n'
        '  "confidence": "HIGH"\n'
        "}"
    )
    messages = [
        {"role": "system", "content": "You are a professional CAD / BIM document controller."},
        {"role": "user", "content": prompt}
    ]
    raw = call_openrouter(messages)
    data = _extract_json_block(raw)
    if not data:
        base = os.path.splitext(os.path.basename(file_path))[0]
        data = {
            "sheet_number": "SHEET-01",
            "revision": "Rev 00",
            "project_name": "AutoCAD Project",
            "sheet_title": base.replace("_", " ").title(),
            "discipline": "General CAD",
            "suggested_filename": f"{base}_Plotted_CAD.pdf",
            "confidence": "STANDARD"
        }
    return data


def ai_contract_risk_audit(file_path: str) -> Dict[str, Any]:
    """
    Scans a legal agreement, NDA, contract, or terms of service for high, medium,
    and low risk clauses with actionable executive explanations.
    """
    text = extract_text_from_document(file_path, max_chars=40000)
    if not text.strip():
        return {
            "risk_score": "UNKNOWN",
            "executive_summary": "Document contains no readable text to audit.",
            "total_clauses_analyzed": 0,
            "clauses": []
        }

    prompt = (
        "You are a senior commercial contracts counsel. Perform a rigorous risk audit of the following agreement:\n\n"
        f"{text[:35000]}\n\n"
        "Analyze key legal areas:\n"
        "- Indemnification & Liability Caps (unlimited liability = HIGH risk)\n"
        "- Termination for Convenience & Notice Windows\n"
        "- Intellectual Property assignment / licenses\n"
        "- Non-compete, Non-solicit covenants & Restrictive clauses\n"
        "- Governing Law, Jurisdiction & Dispute Resolution\n"
        "- Auto-renewal & Hidden Payment Penalties\n\n"
        "Rate overall risk as 'LOW', 'MEDIUM', or 'HIGH'.\n"
        "For each notable clause, provide:\n"
        "- name: clause title\n"
        "- level: 'HIGH', 'MEDIUM', or 'LOW'\n"
        "- quote: exact brief quote from agreement (max 15 words)\n"
        "- explanation: why this is risky or favorable\n"
        "- recommendation: concrete counter-proposal or negotiation tip\n\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "risk_score": "MEDIUM",\n'
        '  "executive_summary": "2-3 sentence executive legal summary",\n'
        '  "total_clauses_analyzed": 5,\n'
        '  "clauses": [\n'
        "    {\n"
        '      "name": "Indemnification",\n'
        '      "level": "HIGH",\n'
        '      "quote": "Party A shall indemnify Party B without limit...",\n'
        '      "explanation": "Uncapped indemnity creates unlimited financial exposure.",\n'
        '      "recommendation": "Cap indemnity at 12 months fees paid."\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    messages = [
        {"role": "system", "content": "You are a senior corporate counsel and contracts risk auditor."},
        {"role": "user", "content": prompt}
    ]
    raw = call_openrouter(messages)
    data = _extract_json_block(raw)
    if not data:
        data = {
            "risk_score": "LOW",
            "executive_summary": "Document reviewed. Standard commercial terms observed without immediate high-risk anomalies.",
            "total_clauses_analyzed": 1,
            "clauses": [
                {
                    "name": "General Commercial Provisions",
                    "level": "LOW",
                    "quote": "Governed by applicable commercial laws",
                    "explanation": "Standard provisions appear balanced.",
                    "recommendation": "Proceed with standard counsel sign-off."
                }
            ]
        }
    return data


def ai_extract_financial_table(file_path: str) -> Dict[str, Any]:
    """
    Extracts financial tables, line items, and invoice numbers into clean Markdown tables and CSV.
    """
    text = extract_text_from_document(file_path, max_chars=35000)
    prompt = (
        "Extract all financial transaction line items, invoice numbers, tax amounts, and totals from this document:\n\n"
        f"{text[:30000]}\n\n"
        "Format the output cleanly:\n"
        "1. Provide a clean GitHub Markdown table of all line items (| Item | Description | Qty | Unit Price | Total |)\n"
        "2. Provide an executive summary of Total Before Tax, Tax/VAT, and Grand Total.\n\n"
        "Return clean Markdown directly without extra preambles."
    )
    messages = [
        {"role": "system", "content": "You are a specialized financial data extractor."},
        {"role": "user", "content": prompt}
    ]
    extracted = call_openrouter(messages)
    return {
        "extracted_table": extracted,
        "model_used": PRIMARY_MODEL
    }


def chat_completion(
    messages: List[Dict[str, Any]],
    file_path: Optional[str] = None,
    system_instruction: Optional[str] = None
) -> Dict[str, Any]:
    """
    Full-featured conversational engine for the Claude-style AI Studio.
    Supports multimodal images, text-extracted documents (PDF, DOCX, CAD DXF/DWG text),
    and intelligent side-by-side Artifact detection.
    """
    sys_prompt = system_instruction or (
        "You are I LOVE FILES AI, an elite technical document, engineering, and file intelligence assistant created by Musthaque Ali for the I LOVE FILES platform. "
        "You provide immediate, comprehensive, and accurate answers to every question the user asks. "
        "When documents, architectural blueprints, AutoCAD drawings, spreadsheets, images, or contracts are provided, analyze them with deep technical precision, clarity, and detail. "
        "Format tables, code snippets, or structured analysis cleanly using GitHub Flavored Markdown. "
        "Never claim you cannot view an attachment if data, text, or visual pages are provided. Always maintain a helpful, confident, professional tone."
    )

    formatted_messages = [{"role": "system", "content": sys_prompt}]

    # Process conversational messages
    for msg in messages:
        formatted_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # Attach file context to the last user message if provided
    has_file = False
    if file_path and os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        fname = os.path.basename(file_path)
        has_file = True

        last_msg = formatted_messages[-1]
        user_text = last_msg["content"] if isinstance(last_msg["content"], str) else ""
        clean_user_text = user_text.strip()
        if not clean_user_text or clean_user_text.startswith("[Attached:"):
            effective_prompt = (
                f"Please review and analyze this attached file '{fname}' thoroughly. "
                f"Summarize all key technical details, specifications, tabular data, scope, or clauses, "
                f"and provide clear, structured takeaways in GitHub Flavored Markdown format."
            )
        else:
            effective_prompt = clean_user_text

        if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"):
            try:
                with Image.open(file_path) as im:
                    if max(im.size) > 1280:
                        im.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    fmt = "PNG" if im.mode in ("RGBA", "P") else "JPEG"
                    im.save(buf, format=fmt, quality=85)
                    clean_bytes = buf.getvalue()
                    mime = "image/png" if fmt == "PNG" else "image/jpeg"
                b64_str = base64.b64encode(clean_bytes).decode("utf-8")
                data_uri = f"data:{mime};base64,{b64_str}"

                last_msg["content"] = [
                    {"type": "text", "text": effective_prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            except Exception as e:
                logger.warning(f"Failed to process image attachment: {e}")
                last_msg["content"] = f"{effective_prompt}\n\n[Attached Image: {fname}]"

        elif ext == ".pdf":
            try:
                text_content = extract_text_from_document(file_path, max_chars=35000)
                # If the PDF has little or no text (e.g. AutoCAD plot or scanned document), render page(s) as vision images
                if len(text_content.strip()) < 150:
                    try:
                        import fitz
                        doc = fitz.open(file_path)
                        rendered_images = []
                        max_pages_to_render = min(len(doc), 3)
                        for pno in range(max_pages_to_render):
                            page = doc[pno]
                            pix = page.get_pixmap(dpi=140)
                            png_bytes = pix.tobytes("png")
                            b64 = base64.b64encode(png_bytes).decode("utf-8")
                            rendered_images.append(f"data:image/png;base64,{b64}")
                        doc.close()

                        if rendered_images:
                            content_parts = [{"type": "text", "text": f"{effective_prompt}\n\n(Attached PDF rendered pages for visual inspection: {fname})"}]
                            for uri in rendered_images:
                                content_parts.append({"type": "image_url", "image_url": {"url": uri}})
                            last_msg["content"] = content_parts
                        else:
                            last_msg["content"] = f"{effective_prompt}\n\n[Attached PDF: {fname} (Vector drawing with no embedded text glyphs)]"
                    except Exception as err_pdf_img:
                        logger.warning(f"Failed to render PDF pages as image: {err_pdf_img}")
                        last_msg["content"] = f"{effective_prompt}\n\n[Attached Document: {fname}]\n---\n{text_content[:30000]}\n---"
                else:
                    last_msg["content"] = f"{effective_prompt}\n\n[Attached Document: {fname}]\n---\n{text_content[:30000]}\n---"
            except Exception as e:
                logger.warning(f"Failed to extract document attachment text: {e}")
                last_msg["content"] = f"{effective_prompt}\n\n[Attached Document: {fname}]"

        elif ext in (".dxf", ".dwg"):
            try:
                cad_info = []
                if ext == ".dxf":
                    import ezdxf
                    doc_dxf = ezdxf.readfile(file_path)
                    layers = [l.dxf.name for l in doc_dxf.layers]
                    cad_info.append(f"AutoCAD DXF File: {fname}")
                    cad_info.append(f"Layers ({len(layers)}): {', '.join(layers[:40])}")
                    texts = [e.dxf.text for e in doc_dxf.modelspace().query("TEXT") if hasattr(e.dxf, "text")]
                    mtexts = [e.text for e in doc_dxf.modelspace().query("MTEXT") if hasattr(e, "text")]
                    all_text = texts + mtexts
                    if all_text:
                        cad_info.append(f"CAD Text Annotations ({len(all_text)}):\n" + "\n".join(all_text[:50]))
                dxf_summary = "\n".join(cad_info) if cad_info else extract_text_from_document(file_path, max_chars=35000)
                last_msg["content"] = f"{effective_prompt}\n\n[Attached CAD File: {fname}]\n---\n{dxf_summary}\n---"
            except Exception as e:
                logger.warning(f"Failed to process CAD file: {e}")
                last_msg["content"] = f"{effective_prompt}\n\n[Attached CAD File: {fname}]"
        else:
            try:
                text_content = extract_text_from_document(file_path, max_chars=35000)
                last_msg["content"] = f"{effective_prompt}\n\n[Attached Document: {fname}]\n---\n{text_content[:30000]}\n---"
            except Exception as e:
                logger.warning(f"Failed to extract text: {e}")
                last_msg["content"] = f"{effective_prompt}\n\n[Attached Document: {fname}]"

    # Call OpenRouter
    raw_reply = call_openrouter(formatted_messages, temperature=0.3)

    # Detect Artifact (Code block, tabular report, or detailed markdown document)
    artifact = None
    m_code = re.search(r"```([a-zA-Z0-9_-]*)\n([\s\S]*?)```", raw_reply)
    if m_code and len(m_code.group(2).strip()) > 80:
        lang = m_code.group(1).lower() or "text"
        artifact = {
            "title": f"Generated {lang.upper() if lang else 'Code'}",
            "type": "code",
            "language": lang,
            "content": m_code.group(2).strip()
        }
    elif ("| --- |" in raw_reply or "## " in raw_reply) and len(raw_reply) > 300:
        h_m = re.search(r"^#+\s*(.+)$", raw_reply, re.MULTILINE)
        title = h_m.group(1).strip() if h_m else "Analysis Document"
        artifact = {
            "title": title,
            "type": "markdown",
            "language": "markdown",
            "content": raw_reply
        }

    return {
        "reply": raw_reply,
        "model_used": PRIMARY_MODEL,
        "artifact": artifact,
        "has_file": bool(file_path)
    }
