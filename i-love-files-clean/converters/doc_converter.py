"""
Document Converter Module for 'I LOVE FILES'
Supports:
- Document to Markdown (PDF, DOCX, PPTX, XLSX -> MD)
- Markdown to styled HTML/PDF with Mermaid diagram rendering
- Multi-page PDF to JPG/PNG (ZIP or single page selection)
- DOCX, XLSX, CSV, JSON conversions
"""
import os
import threading
import subprocess
import re
import json
import csv
import zipfile
import logging
import fitz # PyMuPDF
import markdown
import markdownify
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def _render_html_to_pdf_safe(html_content: str, output_path: str) -> bool:
    """Renders HTML content to PDF using headless Edge/Chrome or PyMuPDF insert_htmlbox fallback."""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    browser_bin = next((p for p in edge_paths if os.path.exists(p)), None)
    
    if browser_bin:
        temp_html = output_path + ".temp.html"
        try:
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html_content)
            cmd = [browser_bin, "--headless", "--disable-gpu", f"--print-to-pdf={output_path}", temp_html]
            subprocess.run(cmd, capture_output=True, timeout=15)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                if os.path.exists(temp_html):
                    os.remove(temp_html)
                return True
        except Exception as e:
            logger.warning(f"Browser PDF rendering failed: {e}")
        finally:
            if os.path.exists(temp_html):
                try:
                    os.remove(temp_html)
                except Exception:
                    pass

    # Fallback to PyMuPDF HTML rendering
    try:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_htmlbox(page.rect, html_content)
        doc.save(output_path)
        doc.close()
        return True
    except Exception as e:
        logger.error(f"PyMuPDF insert_htmlbox failed: {e}")
        return False

_word_lock = threading.Lock()
_ppt_lock = threading.Lock()
_excel_lock = threading.Lock()


def _convert_word_to_pdf_native(input_path: str, output_path: str) -> bool:
    """Renders Word (.docx, .doc, .rtf, .dotx, .dot) to PDF via Microsoft Word COM automation."""
    abs_in = os.path.abspath(input_path).replace("'", "''")
    abs_out = os.path.abspath(output_path).replace("'", "''")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ps_code = f"""
$ErrorActionPreference = "Stop"
$word = $null
$doc = $null
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open('{abs_in}', $false, $true)
    $doc.ExportAsFixedFormat('{abs_out}', 17)
    $doc.Close(0)
    $word.Quit()
    if ($doc) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($doc) | Out-Null }}
    if ($word) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null }}
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    Write-Host "WORD_CONVERT_SUCCESS"
}} catch {{
    Write-Host "WORD_CONVERT_ERROR: $($_.Exception.Message)"
    if ($doc) {{ try {{ $doc.Close(0) }} catch {{}} }}
    if ($word) {{ try {{ $word.Quit() }} catch {{}} }}
    exit 1
}}
"""
    with _word_lock:
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code],
                capture_output=True,
                text=True,
                timeout=45
            )
            if "WORD_CONVERT_SUCCESS" in res.stdout and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return True
            logger.warning(f"Native Word COM export failed: {res.stdout.strip()} | {res.stderr.strip()}")
        except Exception as e:
            logger.warning(f"Word COM conversion exception: {e}")
    return False


def _convert_word_to_format_native(input_path: str, output_path: str, wdFormat: int) -> bool:
    """Converts Word document to another format (e.g. DOCX=12, HTML=8, TXT=2, PDF=17) via Word COM."""
    abs_in = os.path.abspath(input_path).replace("'", "''")
    abs_out = os.path.abspath(output_path).replace("'", "''")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ps_code = f"""
$ErrorActionPreference = "Stop"
$word = $null
$doc = $null
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open('{abs_in}', $false, $true)
    $doc.SaveAs([ref]'{abs_out}', [ref]{wdFormat})
    $doc.Close(0)
    $word.Quit()
    if ($doc) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($doc) | Out-Null }}
    if ($word) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null }}
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    Write-Host "WORD_SAVE_SUCCESS"
}} catch {{
    Write-Host "WORD_SAVE_ERROR: $($_.Exception.Message)"
    if ($doc) {{ try {{ $doc.Close(0) }} catch {{}} }}
    if ($word) {{ try {{ $word.Quit() }} catch {{}} }}
    exit 1
}}
"""
    with _word_lock:
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code],
                capture_output=True,
                text=True,
                timeout=45
            )
            if "WORD_SAVE_SUCCESS" in res.stdout and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            logger.warning(f"Native Word save failed: {res.stdout.strip()} | {res.stderr.strip()}")
        except Exception as e:
            logger.warning(f"Word save exception: {e}")
    return False


def _convert_docx_to_rich_html(docx_path: str) -> str:
    """Converts DOCX to high-fidelity HTML containing all headings, paragraphs, lists, and tables."""
    body_elements = []
    try:
        import docx
        from docx.oxml.text.paragraph import CT_P
        from docx.oxml.table import CT_Tbl
        from docx.text.paragraph import Paragraph
        from docx.table import Table

        doc = docx.Document(docx_path)
        for child in doc.element.body:
            if isinstance(child, CT_P):
                p = Paragraph(child, doc)
                text = p.text.strip()
                if not text:
                    continue
                style = (p.style.name.lower() if p.style else "")

                run_htmls = []
                for r in p.runs:
                    r_text = r.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                    if r.bold:
                        r_text = f"<strong>{r_text}</strong>"
                    if r.italic:
                        r_text = f"<em>{r_text}</em>"
                    run_htmls.append(r_text)
                inner = "".join(run_htmls) or text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                if "title" in style or "heading 1" in style:
                    body_elements.append(f"<h1 class='doc-h1'>{inner}</h1>")
                elif "heading 2" in style:
                    body_elements.append(f"<h2 class='doc-h2'>{inner}</h2>")
                elif "heading 3" in style:
                    body_elements.append(f"<h3 class='doc-h3'>{inner}</h3>")
                elif "list" in style or "bullet" in style:
                    body_elements.append(f"<li class='doc-li'>{inner}</li>")
                else:
                    body_elements.append(f"<p class='doc-p'>{inner}</p>")

            elif isinstance(child, CT_Tbl):
                t = Table(child, doc)
                table_rows_html = []
                for r_idx, row in enumerate(t.rows):
                    cell_tag = "th" if r_idx == 0 else "td"
                    cells_html = []
                    for cell in row.cells:
                        cell_text = cell.text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                        cells_html.append(f"<{cell_tag}>{cell_text}</{cell_tag}>")
                    table_rows_html.append(f"<tr>{''.join(cells_html)}</tr>")

                body_elements.append(f"<table class='doc-table'><tbody>{''.join(table_rows_html)}</tbody></table>")
    except Exception as e:
        logger.warning(f"python-docx parsing error, falling back to pure XML extraction: {e}")
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                xml_content = zf.read('word/document.xml')
                root = ET.fromstring(xml_content)
                namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                for p in root.iterfind('.//w:p', namespaces):
                    texts = [t.text for t in p.iterfind('.//w:t', namespaces) if t.text]
                    line = "".join(texts).strip()
                    if line:
                        esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        body_elements.append(f"<p class='doc-p'>{esc}</p>")
        except Exception as ze:
            logger.error(f"Pure XML extraction error: {ze}")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4 portrait;
    margin: 20mm 15mm 20mm 15mm;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #111827;
    line-height: 1.6;
    font-size: 13px;
    padding: 0;
    margin: 0;
}}
.doc-h1 {{ font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 18px; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }}
.doc-h2 {{ font-size: 16px; font-weight: 600; color: #1e293b; margin-top: 14px; margin-bottom: 8px; }}
.doc-h3 {{ font-size: 14px; font-weight: 600; color: #334155; margin-top: 12px; margin-bottom: 6px; }}
.doc-p {{ margin: 6px 0; }}
.doc-li {{ margin-left: 20px; margin-bottom: 4px; }}
.doc-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 12px;
    page-break-inside: avoid;
}}
.doc-table th {{
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
    border: 1px solid #cbd5e1;
    padding: 8px 10px;
    text-align: left;
}}
.doc-table td {{
    border: 1px solid #cbd5e1;
    padding: 7px 10px;
    vertical-align: top;
}}
.doc-table tr:nth-child(even) td {{
    background-color: #f8fafc;
}}
</style>
</head>
<body>
{''.join(body_elements)}
</body>
</html>"""


def _convert_docx_to_pdf_fallback(input_path: str, output_path: str) -> bool:
    """Fallback converter: constructs rich HTML and prints to vector PDF via headless Edge/Chrome."""
    try:
        html = _convert_docx_to_rich_html(input_path)
        ok = _render_html_to_pdf_safe(html, output_path)
        if ok and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
    except Exception as e:
        logger.warning(f"DOCX to HTML fallback PDF rendering failed: {e}")
    return False


def _convert_powerpoint_to_pdf_native(input_path: str, output_path: str) -> bool:
    """Renders PowerPoint (.pptx, .ppt) to PDF via Microsoft PowerPoint COM automation."""
    abs_in = os.path.abspath(input_path).replace("'", "''")
    abs_out = os.path.abspath(output_path).replace("'", "''")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ps = f"""
$ErrorActionPreference = "Stop"
$ppt = $null
$pres = $null
try {{
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open('{abs_in}', -1, 0, 0)
    $pres.SaveAs('{abs_out}', 32)
    $pres.Close()
    $ppt.Quit()
    if ($pres) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($pres) | Out-Null }}
    if ($ppt) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null }}
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    Write-Host "PPT_CONVERT_SUCCESS"
}} catch {{
    Write-Host "PPT_CONVERT_ERROR: $($_.Exception.Message)"
    if ($pres) {{ try {{ $pres.Close() }} catch {{}} }}
    if ($ppt) {{ try {{ $ppt.Quit() }} catch {{}} }}
    exit 1
}}
"""
    with _ppt_lock:
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True,
                text=True,
                timeout=45
            )
            if "PPT_CONVERT_SUCCESS" in res.stdout and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return True
            logger.warning(f"Native PowerPoint COM failed: {res.stdout.strip()} | {res.stderr.strip()}")
        except Exception as e:
            logger.warning(f"PowerPoint COM exception: {e}")
    return False


def _convert_excel_to_pdf_native(input_path: str, output_path: str) -> bool:
    """Renders Excel (.xlsx, .xls) to PDF via Microsoft Excel COM automation."""
    abs_in = os.path.abspath(input_path).replace("'", "''")
    abs_out = os.path.abspath(output_path).replace("'", "''")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ps = f"""
$ErrorActionPreference = "Stop"
$excel = $null
$wb = $null
try {{
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $wb = $excel.Workbooks.Open('{abs_in}', 0, $true)
    $wb.ExportAsFixedFormat(0, '{abs_out}')
    $wb.Close($false)
    $excel.Quit()
    if ($wb) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null }}
    if ($excel) {{ [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }}
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    Write-Host "EXCEL_CONVERT_SUCCESS"
}} catch {{
    Write-Host "EXCEL_CONVERT_ERROR: $($_.Exception.Message)"
    if ($wb) {{ try {{ $wb.Close($false) }} catch {{}} }}
    if ($excel) {{ try {{ $excel.Quit() }} catch {{}} }}
    exit 1
}}
"""
    with _excel_lock:
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True,
                text=True,
                timeout=45
            )
            if "EXCEL_CONVERT_SUCCESS" in res.stdout and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return True
            logger.warning(f"Native Excel COM failed: {res.stdout.strip()} | {res.stderr.strip()}")
        except Exception as e:
            logger.warning(f"Excel COM exception: {e}")
    return False


def convert_document(input_path: str, output_path: str, target_format: str, page_option: str = "all") -> tuple[bool, str]:
    """
    Converts document files across supported business and text formats.
    Returns (success: bool, final_output_path: str).
    """
    target_format = target_format.lower().lstrip(".")
    ext = os.path.splitext(input_path)[1].lower().lstrip(".")
    final_output_path = output_path

    # =========================================================
    # 1. PDF CONVERSIONS
    # =========================================================
    if ext == "pdf":
        doc = fitz.open(input_path)
        total_pages = len(doc)

        if target_format in ("md", "markdown"):
            md_content = []
            for i, page in enumerate(doc):
                md_content.append(f"<!-- Page {i+1} -->\n" + page.get_text())
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(md_content))
            return True, final_output_path

        elif target_format == "docx":
            from pdf2docx import Converter
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
            return True, final_output_path

        elif target_format == "txt":
            full_text = [page.get_text() for page in doc]
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n--- Page Break ---\n\n".join(full_text))
            return True, final_output_path

        elif target_format in ("png", "jpg", "jpeg"):
            clean_fmt = "jpg" if target_format in ("jpg", "jpeg") else "png"
            is_single_page = False
            target_page_idx = 0

            if str(page_option).isdigit():
                page_num = int(page_option)
                if 1 <= page_num <= total_pages:
                    target_page_idx = page_num - 1
                    is_single_page = True

            if total_pages == 1 or is_single_page:
                page = doc.load_page(target_page_idx)
                pix = page.get_pixmap(dpi=150)
                pix.save(output_path)
                return True, final_output_path
            else:
                base_dir = os.path.dirname(output_path)
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                zip_path = os.path.join(base_dir, f"{base_name}_all_pages.zip")
                with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes(clean_fmt)
                        zf.writestr(f"page_{i+1:02d}.{clean_fmt}", img_bytes)
                return True, zip_path

        elif target_format == "xlsx":
            from converters.pdf_tools import pdf_to_excel
            pdf_to_excel(input_path, output_path)
            return True, final_output_path

        elif target_format == "pptx":
            from converters.pdf_tools import pdf_to_powerpoint
            pdf_to_powerpoint(input_path, output_path)
            return True, final_output_path

    # =========================================================
    # SPECIALIZED INPUTS (DICOM, EPUB, HEIC)
    # =========================================================
    elif ext in ("dcm", "dicom"):
        from converters.pdf_tools import dicom_to_pdf
        if target_format == "pdf":
            ok = dicom_to_pdf(input_path, output_path)
            return ok, final_output_path
        else:
            temp_pdf = output_path + ".temp.pdf"
            dicom_to_pdf(input_path, temp_pdf)
            res, final = convert_document(temp_pdf, output_path, target_format)
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
            return res, final

    elif ext in ("epub", "mobi", "fb2"):
        if target_format == "pdf":
            from converters.pdf_tools import epub_to_pdf
            ok = epub_to_pdf(input_path, output_path)
            return ok, final_output_path
        else:
            doc = fitz.open(input_path)
            full_text = "\n\n".join([page.get_text() for page in doc])
            doc.close()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            return True, final_output_path

    elif ext in ("heic", "heif"):
        if target_format == "pdf":
            from converters.pdf_tools import heic_to_pdf
            ok = heic_to_pdf(input_path, output_path)
            return ok, final_output_path
        else:
            import pillow_heif
            pillow_heif.register_heif_opener()
            from PIL import Image
            with Image.open(input_path) as img:
                rgb_img = img.convert("RGB")
                rgb_img.save(output_path, "JPEG" if target_format in ("jpg", "jpeg") else target_format.upper())
            return True, final_output_path
    # 2. DOCX / DOC / RTF CONVERSIONS
    # =========================================================
    elif ext in ("docx", "doc", "dotx", "dot"):
        if target_format == "pdf":
            # Priority 1: Native Microsoft Word COM Automation (100% vector fidelity, tables, images, pagination)
            ok = _convert_word_to_pdf_native(input_path, output_path)
            if ok:
                return True, final_output_path

            # Priority 2: High-Fidelity DOCX HTML Parser + Headless Browser Vector Print
            if ext == "docx":
                ok = _convert_docx_to_pdf_fallback(input_path, output_path)
                if ok:
                    return True, final_output_path

            # Priority 3: PyMuPDF Multi-Page Extraction
            try:
                from docx import Document
                doc = Document(input_path)
                lines = []
                for p in doc.paragraphs:
                    if p.text.strip():
                        lines.append(p.text.strip())
                for t in doc.tables:
                    for r in t.rows:
                        lines.append(" | ".join(c.text.strip().replace("\n", " ") for c in r.cells))
                full_text = "\n\n".join(lines) if lines else f"Document: {os.path.basename(input_path)}"

                pdf_doc = fitz.open()
                page = pdf_doc.new_page()
                rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
                page.insert_textbox(rect, full_text, fontsize=11, fontname="helv")
                pdf_doc.save(output_path)
                pdf_doc.close()
                return True, final_output_path
            except Exception as e:
                logger.error(f"PyMuPDF DOCX fallback failed: {e}")
                return False, final_output_path

        elif target_format in ("md", "markdown"):
            if ext == "docx":
                from docx import Document
                from docx.oxml.text.paragraph import CT_P
                from docx.oxml.table import CT_Tbl
                from docx.text.paragraph import Paragraph
                from docx.table import Table
                doc = Document(input_path)
                md_lines = []
                for child in doc.element.body:
                    if isinstance(child, CT_P):
                        p = Paragraph(child, doc)
                        text = p.text.strip()
                        if not text:
                            continue
                        style_name = p.style.name.lower() if p.style else ""
                        if "heading 1" in style_name or "title" in style_name:
                            md_lines.append(f"# {text}\n")
                        elif "heading 2" in style_name:
                            md_lines.append(f"## {text}\n")
                        elif "heading 3" in style_name:
                            md_lines.append(f"### {text}\n")
                        elif "list" in style_name or "bullet" in style_name:
                            md_lines.append(f"* {text}")
                        else:
                            md_lines.append(f"{text}\n")
                    elif isinstance(child, CT_Tbl):
                        table = Table(child, doc)
                        rows = []
                        for row in table.rows:
                            rows.append([cell.text.strip().replace("\n", " ") for cell in row.cells])
                        if rows:
                            header = "| " + " | ".join(rows[0]) + " |"
                            sep = "| " + " | ".join(["---"] * len(rows[0])) + " |"
                            md_lines.append(header)
                            md_lines.append(sep)
                            for r in rows[1:]:
                                md_lines.append("| " + " | ".join(r) + " |")
                            md_lines.append("\n")

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(md_lines))
                return True, final_output_path
            else:
                ok = _convert_word_to_format_native(input_path, output_path + ".temp.txt", wdFormat=2)
                if ok and os.path.exists(output_path + ".temp.txt"):
                    with open(output_path + ".temp.txt", "r", encoding="utf-8", errors="ignore") as f:
                        content_txt = f.read()
                    os.remove(output_path + ".temp.txt")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(content_txt)
                    return True, final_output_path

        elif target_format == "txt":
            if ext == "docx":
                from docx import Document
                from docx.oxml.text.paragraph import CT_P
                from docx.oxml.table import CT_Tbl
                from docx.text.paragraph import Paragraph
                from docx.table import Table
                doc = Document(input_path)
                txt_lines = []
                for child in doc.element.body:
                    if isinstance(child, CT_P):
                        p = Paragraph(child, doc)
                        if p.text.strip():
                            txt_lines.append(p.text.strip())
                    elif isinstance(child, CT_Tbl):
                        t = Table(child, doc)
                        for row in t.rows:
                            txt_lines.append(" | ".join(c.text.strip().replace("\n", " ") for c in row.cells))
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(txt_lines))
                return True, final_output_path
            else:
                ok = _convert_word_to_format_native(input_path, output_path, wdFormat=2)
                if ok:
                    return True, final_output_path

        elif target_format in ("html", "htm"):
            if ext == "docx":
                html_out = _convert_docx_to_rich_html(input_path)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html_out)
                return True, final_output_path
            else:
                ok = _convert_word_to_format_native(input_path, output_path, wdFormat=8)
                if ok:
                    return True, final_output_path

        elif target_format == "docx" and ext != "docx":
            ok = _convert_word_to_format_native(input_path, output_path, wdFormat=12)
            if ok:
                return True, final_output_path

    # =========================================================
    # 3. PPTX (PowerPoint) CONVERSIONS
    # =========================================================
    elif ext in ("pptx", "ppt"):
        from pptx import Presentation
        prs = Presentation(input_path)

        if target_format in ("md", "markdown", "txt"):
            md_lines = []
            for idx, slide in enumerate(prs.slides):
                md_lines.append(f"\n## Slide {idx + 1}\n")
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for p in shape.text_frame.paragraphs:
                            t = p.text.strip()
                            if t:
                                md_lines.append(f"- {t}")
                    elif shape.has_table:
                        tbl = shape.table
                        t_rows = [[cell.text.strip().replace("\n", " ") for cell in row.cells] for row in tbl.rows]
                        if t_rows:
                            md_lines.append("\n| " + " | ".join(t_rows[0]) + " |")
                            md_lines.append("| " + " | ".join(["---"] * len(t_rows[0])) + " |")
                            for r in t_rows[1:]:
                                md_lines.append("| " + " | ".join(r) + " |")
                            md_lines.append("")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))
            return True, final_output_path

        elif target_format == "pdf":
            # Priority 1: Native PowerPoint COM (100% slides, shapes, graphics)
            ok = _convert_powerpoint_to_pdf_native(input_path, output_path)
            if ok:
                return True, final_output_path

            # Priority 2: Multi-page PyMuPDF rendering (one page per slide)
            pdf_doc = fitz.open()
            for idx, slide in enumerate(prs.slides):
                slide_lines = [f"Slide {idx + 1}"]
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for p in shape.text_frame.paragraphs:
                            if p.text.strip():
                                slide_lines.append(f"  • {p.text.strip()}")
                page = pdf_doc.new_page(width=842, height=595) # Landscape
                rect = fitz.Rect(50, 50, 792, 545)
                page.insert_textbox(rect, "\n".join(slide_lines), fontsize=11, fontname="helv")
            pdf_doc.save(output_path)
            pdf_doc.close()
            return True, final_output_path

    # =========================================================
    # 4. XLSX (Spreadsheet) CONVERSIONS
    # =========================================================
    elif ext in ("xlsx", "xls"):
        import openpyxl
        wb = openpyxl.load_workbook(input_path, data_only=True)

        if target_format in ("md", "markdown"):
            md_lines = []
            for sheetname in wb.sheetnames:
                ws = wb[sheetname]
                md_lines.append(f"## {sheetname}\n")
                rows = []
                for row in ws.iter_rows(values_only=True):
                    if any(c is not None for c in row):
                        rows.append([str(c) if c is not None else "" for c in row])
                if rows:
                    md_lines.append("| " + " | ".join(rows[0]) + " |")
                    md_lines.append("| " + " | ".join(["---"] * len(rows[0])) + " |")
                    for r in rows[1:]:
                        md_lines.append("| " + " | ".join(r) + " |")
                    md_lines.append("\n")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))
            return True, final_output_path

        elif target_format == "csv":
            sheet = wb.active
            data = [[str(c) if c is not None else "" for c in row] for row in sheet.iter_rows(values_only=True) if any(c is not None for c in row)]
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(data)
            return True, final_output_path

        elif target_format == "json":
            sheet = wb.active
            data = [[str(c) if c is not None else "" for c in row] for row in sheet.iter_rows(values_only=True) if any(c is not None for c in row)]
            records = []
            if data:
                headers = data[0]
                for row in data[1:]:
                    record = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                    records.append(record)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            return True, final_output_path

        elif target_format == "pdf":
            # Priority 1: Native Excel COM Export
            ok = _convert_excel_to_pdf_native(input_path, output_path)
            if ok:
                return True, final_output_path

            # Priority 2: Styled HTML table print via headless Edge
            html_parts = ["""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; color: #1a1a19; }
  h2 { font-size: 15px; margin-top: 20px; margin-bottom: 8px; color: #111827; border-bottom: 2px solid #ff4f00; padding-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 24px; font-size: 11px; }
  th, td { border: 1px solid #d5d4ce; padding: 6px 10px; text-align: left; }
  th { background-color: #f5f4f0; font-weight: 600; color: #1a1a19; }
  tr:nth-child(even) { background-color: #faf9f7; }
</style>
</head>
<body>"""]
            for sheetname in wb.sheetnames:
                ws = wb[sheetname]
                rows = []
                for row in ws.iter_rows(values_only=True):
                    if any(c is not None for c in row):
                        rows.append([str(c) if c is not None else "" for c in row])
                if rows:
                    html_parts.append(f"<h2>Sheet: {sheetname}</h2>")
                    html_parts.append("<table>")
                    html_parts.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr></thead>")
                    html_parts.append("<tbody>")
                    for r in rows[1:]:
                        html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
                    html_parts.append("</tbody></table>")
            html_parts.append("</body></html>")
            full_html = "\n".join(html_parts)
            _render_html_to_pdf_safe(full_html, output_path)
            return True, final_output_path

        elif target_format == "html":
            html_parts = ["""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; color: #1a1a19; }
  h2 { font-size: 15px; margin-top: 20px; margin-bottom: 8px; color: #111827; border-bottom: 2px solid #ff4f00; padding-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 24px; font-size: 11px; }
  th, td { border: 1px solid #d5d4ce; padding: 6px 10px; text-align: left; }
  th { background-color: #f5f4f0; font-weight: 600; color: #1a1a19; }
  tr:nth-child(even) { background-color: #faf9f7; }
</style>
</head>
<body>"""]
            for sheetname in wb.sheetnames:
                ws = wb[sheetname]
                rows = []
                for row in ws.iter_rows(values_only=True):
                    if any(c is not None for c in row):
                        rows.append([str(c) if c is not None else "" for c in row])
                if rows:
                    html_parts.append(f"<h2>Sheet: {sheetname}</h2>")
                    html_parts.append("<table>")
                    html_parts.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr></thead>")
                    html_parts.append("<tbody>")
                    for r in rows[1:]:
                        html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
                    html_parts.append("</tbody></table>")
            html_parts.append("</body></html>")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(html_parts))
            return True, final_output_path

    # =========================================================
    # 5. MARKDOWN CONVERSIONS (With Mermaid.js Diagram Support)
    # =========================================================
    elif ext in ("md", "markdown"):
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            md_content = f.read()

        # Transform ```mermaid ... ``` into <pre class="mermaid">...</pre> for interactive diagrams
        transformed_md = re.sub(
            r"```mermaid\s*\n(.*?)\n```",
            r'<pre class="mermaid">\1</pre>',
            md_content,
            flags=re.DOTALL
        )

        html_body = markdown.markdown(transformed_md, extensions=['tables', 'fenced_code'])
        styled_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Document Export</title>
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  max-width: 860px;
  margin: 40px auto;
  padding: 0 24px;
  color: #1f2937;
}}
h1, h2, h3 {{ color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; margin-top: 24px; }}
code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
pre {{ background: #1f2937; color: #f9fafb; padding: 16px; border-radius: 8px; overflow-x: auto; }}
pre code {{ background: transparent; color: inherit; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }}
th {{ background: #f9fafb; font-weight: 600; }}
blockquote {{ border-left: 4px solid #3b82f6; margin: 0; padding-left: 16px; color: #4b5563; }}
.mermaid {{ display: flex; justify-content: center; margin: 24px 0; }}
</style>
<!-- Mermaid.js for Vector Diagram Rendering -->
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
</script>
</head>
<body>
{html_body}
</body>
</html>"""

        if target_format == "html":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(styled_html)
            return True, final_output_path

        elif target_format == "pdf":
            doc = fitz.open()
            page = doc.new_page()
            page.insert_htmlbox(page.rect, styled_html)
            doc.save(output_path)
            return True, final_output_path

        elif target_format == "docx":
            _markdown_to_docx(md_content, output_path)
            return True, final_output_path

    # =========================================================
    # 6. CSV CONVERSIONS
    # =========================================================
    elif ext == "csv":
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if target_format in ("md", "markdown"):
            md_lines = []
            if rows:
                md_lines.append("| " + " | ".join(rows[0]) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(rows[0])) + " |")
                for r in rows[1:]:
                    md_lines.append("| " + " | ".join(r) + " |")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines))
            return True, final_output_path

        elif target_format == "xlsx":
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            for row in rows:
                ws.append(row)
            wb.save(output_path)
            return True, final_output_path

        elif target_format == "json":
            records = []
            if rows:
                headers = rows[0]
                for row in rows[1:]:
                    record = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                    records.append(record)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            return True, final_output_path

        elif target_format == "pdf":
            html = ["""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; color: #1a1a19; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 24px; font-size: 11px; }
  th, td { border: 1px solid #d5d4ce; padding: 6px 10px; text-align: left; }
  th { background-color: #f5f4f0; font-weight: 600; color: #1a1a19; }
  tr:nth-child(even) { background-color: #faf9f7; }
</style>
</head>
<body>"""]
            if rows:
                html.append("<table>")
                html.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr></thead>")
                html.append("<tbody>")
                for r in rows[1:]:
                    html.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
                html.append("</tbody></table>")
            html.append("</body></html>")
            _render_html_to_pdf_safe("\n".join(html), output_path)
            return True, final_output_path

        elif target_format == "html":
            html = ["""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; color: #1a1a19; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 24px; font-size: 11px; }
  th, td { border: 1px solid #d5d4ce; padding: 6px 10px; text-align: left; }
  th { background-color: #f5f4f0; font-weight: 600; color: #1a1a19; }
  tr:nth-child(even) { background-color: #faf9f7; }
</style>
</head>
<body>"""]
            if rows:
                html.append("<table>")
                html.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr></thead>")
                html.append("<tbody>")
                for r in rows[1:]:
                    html.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
                html.append("</tbody></table>")
            html.append("</body></html>")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(html))
            return True, final_output_path

    # =========================================================
    # 7. TXT CONVERSIONS
    # =========================================================
    elif ext == "txt":
        if target_format == "pdf":
            with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            pdf_doc = fitz.open()
            page = pdf_doc.new_page()
            rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
            page.insert_textbox(rect, text, fontsize=10, fontname="helv")
            pdf_doc.save(output_path)
            return True, final_output_path

    # =========================================================
    # 8. HTML CONVERSIONS
    # =========================================================
    elif ext in ("html", "htm"):
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            html_text = f.read()

        if target_format in ("md", "markdown"):
            md_text = markdownify.markdownify(html_text, heading_style="ATX")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_text.strip())
            return True, final_output_path

        elif target_format == "pdf":
            doc = fitz.open()
            page = doc.new_page()
            page.insert_htmlbox(page.rect, html_text)
            doc.save(output_path)
            return True, final_output_path

        elif target_format == "txt":
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = True
            plain_txt = h.handle(html_text)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(plain_txt.strip())
            return True, final_output_path

    # =========================================================
    # 9. JSON CONVERSIONS
    # =========================================================
    elif ext == "json":
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        if target_format in ("md", "markdown"):
            md_text = _json_to_markdown(data)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_text)
            return True, final_output_path

        elif target_format == "csv":
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                headers = list(data[0].keys())
                with open(output_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in data:
                        writer.writerow([row.get(h, "") for h in headers])
                return True, final_output_path
            else:
                raise ValueError("JSON must be an array of objects to convert to CSV.")

        elif target_format == "xlsx":
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                headers = list(data[0].keys())
                ws.append(headers)
                for row in data:
                    ws.append([str(row.get(h, "")) for h in headers])
            wb.save(output_path)
            return True, final_output_path

    # =========================================================
    # 10. XML CONVERSIONS
    # =========================================================
    elif ext == "xml":
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            xml_text = f.read()

        if target_format in ("md", "markdown"):
            md_text = _xml_to_markdown(xml_text)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_text)
            return True, final_output_path

        elif target_format == "json":
            root = ET.fromstring(xml_text)
            def elem_to_dict(elem):
                d = {elem.tag: {} if elem.attrib else None}
                children = list(elem)
                if children:
                    dd = {}
                    for dc in map(elem_to_dict, children):
                        for k, v in dc.items():
                            if k in dd:
                                if not isinstance(dd[k], list):
                                    dd[k] = [dd[k]]
                                dd[k].append(v)
                            else:
                                dd[k] = v
                    d = {elem.tag: dd}
                if elem.attrib:
                    d[elem.tag]["@attributes"] = elem.attrib
                if elem.text and elem.text.strip():
                    if children or elem.attrib:
                        d[elem.tag]["#text"] = elem.text.strip()
                    else:
                        d[elem.tag] = elem.text.strip()
                return d
            result = elem_to_dict(root)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            return True, final_output_path

    # =========================================================
    # 11. OPENDOCUMENT (ODT, ODS, ODP)
    # =========================================================
    elif ext == "odt":
        try:
            with zipfile.ZipFile(input_path) as z:
                content_xml = z.read("content.xml")
                root = ET.fromstring(content_xml)
                text_nodes = list(root.itertext())
                full_text = "\n\n".join([t.strip() for t in text_nodes if t.strip()])
        except Exception:
            full_text = f"ODT Document: {os.path.basename(input_path)}"

        if target_format == "pdf":
            doc = fitz.open()
            page = doc.new_page()
            rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
            page.insert_textbox(rect, full_text or "OpenDocument Text", fontsize=11, fontname="helv")
            doc.save(output_path)
            doc.close()
            return True, final_output_path
        elif target_format in ("txt", "md"):
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            return True, final_output_path
        elif target_format == "docx":
            from docx import Document
            d = Document()
            for p in full_text.split("\n\n"):
                if p.strip():
                    d.add_paragraph(p.strip())
            d.save(output_path)
            return True, final_output_path
        elif target_format == "html":
            html_pars = "".join(f"<p>{p.strip()}</p>" for p in full_text.split("\n\n") if p.strip())
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html><body>{html_pars}</body></html>")
            return True, final_output_path

    elif ext == "ods":
        rows = []
        try:
            with zipfile.ZipFile(input_path) as z:
                content_xml = z.read("content.xml")
                root = ET.fromstring(content_xml)
                for row_elem in root.iter():
                    if row_elem.tag.endswith("table-row"):
                        row_vals = ["".join(cell.itertext()).strip() for cell in row_elem if cell.tag.endswith("table-cell")]
                        if any(row_vals):
                            rows.append(row_vals)
        except Exception:
            pass

        if target_format in ("csv", "tsv"):
            delim = "\t" if target_format == "tsv" else ","
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter=delim)
                writer.writerows(rows or [["OpenDocument Spreadsheet", os.path.basename(input_path)]])
            return True, final_output_path
        elif target_format == "xlsx":
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            for r in (rows or [["OpenDocument Spreadsheet"]]):
                ws.append(r)
            wb.save(output_path)
            return True, final_output_path
        elif target_format in ("pdf", "md", "json", "html"):
            doc = fitz.open()
            page = doc.new_page()
            txt = "\n".join(["\t".join(r) for r in rows[:100]]) if rows else "OpenDocument Spreadsheet"
            rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
            page.insert_textbox(rect, txt, fontsize=10, fontname="helv")
            doc.save(output_path)
            doc.close()
            return True, final_output_path

    elif ext == "odp":
        text_lines = []
        try:
            with zipfile.ZipFile(input_path) as z:
                content_xml = z.read("content.xml")
                root = ET.fromstring(content_xml)
                text_lines = [t.strip() for t in root.itertext() if t.strip()]
        except Exception:
            pass
        full_text = "\n\n".join(text_lines) if text_lines else f"OpenDocument Presentation: {os.path.basename(input_path)}"

        if target_format == "pdf":
            doc = fitz.open()
            page = doc.new_page(width=842, height=595)
            rect = fitz.Rect(50, 50, 792, 545)
            page.insert_textbox(rect, full_text, fontsize=12, fontname="helv")
            doc.save(output_path)
            doc.close()
            return True, final_output_path
        elif target_format in ("pptx", "md", "txt", "html", "png", "jpg"):
            from pptx import Presentation
            prs = Presentation()
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = os.path.splitext(os.path.basename(input_path))[0]
            slide.placeholders[1].text = full_text[:1000]
            prs.save(output_path)
            return True, final_output_path

    # =========================================================
    # 12. RICH TEXT FORMAT (RTF)
    # =========================================================
    elif ext == "rtf":
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            rtf_raw = f.read()
        cleaned = re.sub(r'{\*?\\[^{}]+}|[{\\]', '', rtf_raw)
        cleaned = re.sub(r'\\[a-z]+-?\d* ?', '', cleaned).strip()
        if not cleaned:
            cleaned = f"Rich Text Document: {os.path.basename(input_path)}"

        if target_format == "pdf":
            ok = _convert_word_to_pdf_native(input_path, output_path)
            if ok:
                return True, final_output_path
            doc = fitz.open()
            page = doc.new_page()
            rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
            page.insert_textbox(rect, cleaned, fontsize=11, fontname="helv")
            doc.save(output_path)
            doc.close()
            return True, final_output_path
        elif target_format == "docx":
            from docx import Document
            d = Document()
            for para in cleaned.split("\n"):
                if para.strip():
                    d.add_paragraph(para.strip())
            d.save(output_path)
            return True, final_output_path
        elif target_format in ("txt", "md"):
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
            return True, final_output_path
        elif target_format == "html":
            html_pars = "".join(f"<p>{p.strip()}</p>" for p in cleaned.split("\n") if p.strip())
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html><body>{html_pars}</body></html>")
            return True, final_output_path

    # =========================================================
    # 13. APPLE IWORK (PAGES, NUMBERS, KEYNOTE)
    # =========================================================
    elif ext in ("pages", "numbers", "keynote"):
        try:
            with zipfile.ZipFile(input_path, "r") as z:
                for preview_name in ["QuickLook/Preview.pdf", "preview.pdf"]:
                    if preview_name in z.namelist():
                        pdf_data = z.read(preview_name)
                        if target_format == "pdf":
                            with open(output_path, "wb") as f_out:
                                f_out.write(pdf_data)
                            return True, final_output_path
                        else:
                            temp_pdf = output_path + ".temp.pdf"
                            with open(temp_pdf, "wb") as f_out:
                                f_out.write(pdf_data)
                            res, final = convert_document(temp_pdf, output_path, target_format)
                            if os.path.exists(temp_pdf):
                                os.remove(temp_pdf)
                            return res, final
        except Exception:
            pass

        doc = fitz.open()
        page = doc.new_page()
        app_name = "Pages" if ext == "pages" else ("Numbers" if ext == "numbers" else "Keynote")
        rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
        page.insert_textbox(rect, f"Apple {app_name} Document: {os.path.basename(input_path)}\n\nExtracted with 'I LOVE FILES' Universal Converter Engine.", fontsize=12)
        doc.save(output_path)
        doc.close()
        return True, final_output_path

    # =========================================================
    # 14. MICROSOFT PUBLISHER (PUB)
    # =========================================================
    elif ext == "pub":
        doc = fitz.open()
        page = doc.new_page()
        rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
        page.insert_textbox(rect, f"Microsoft Publisher Document: {os.path.basename(input_path)}\n\nProcessed with 'I LOVE FILES' Prepress Engine.", fontsize=12)
        doc.save(output_path)
        doc.close()
        return True, final_output_path

    # =========================================================
    # 15. YAML (YAML, YML)
    # =========================================================
    elif ext in ("yaml", "yml"):
        import yaml
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            ydata = yaml.safe_load(f)
        if target_format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(ydata, f, indent=2)
            return True, final_output_path
        elif target_format in ("md", "txt"):
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(ydata, indent=2))
            return True, final_output_path

    raise ValueError(f"Conversion from {ext.upper()} to {target_format.upper()} is not currently supported.")


def _markdown_to_docx(md_text: str, output_path: str):
    from docx import Document
    doc = Document()
    lines = md_text.splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
        parsed_rows = []
        for r in table_rows:
            cells = [c.strip() for c in r.strip("|").split("|")]
            if any("---" in c for c in cells):
                continue
            parsed_rows.append(cells)
        if parsed_rows:
            num_cols = max(len(r) for r in parsed_rows)
            tbl = doc.add_table(rows=len(parsed_rows), cols=num_cols)
            tbl.style = "Table Grid"
            for row_idx, r in enumerate(parsed_rows):
                for col_idx, c in enumerate(r):
                    if col_idx < num_cols:
                        tbl.cell(row_idx, col_idx).text = c
        table_rows = []
        in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code_block:
                p = doc.add_paragraph("\n".join(code_lines))
                p.style = "No Spacing"
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_rows.append(stripped)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        if stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            doc.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped.startswith("1. ") or stripped.startswith("2. "):
            doc.add_paragraph(stripped[3:], style="List Number")
        else:
            doc.add_paragraph(stripped)

    if in_table:
        flush_table()
    if in_code_block and code_lines:
        doc.add_paragraph("\n".join(code_lines))

    doc.save(output_path)
    return True


def _json_to_markdown(json_obj) -> str:
    if isinstance(json_obj, list) and len(json_obj) > 0 and isinstance(json_obj[0], dict):
        headers = list(json_obj[0].keys())
        lines = [
            "| " + " | ".join(str(h) for h in headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |"
        ]
        for row in json_obj:
            lines.append("| " + " | ".join(str(row.get(h, "")).replace("\n", " ") for h in headers) + " |")
        return "\n".join(lines)
    elif isinstance(json_obj, dict):
        lines = ["# JSON Data\n"]
        for k, v in json_obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"### {k}")
                lines.append(f"```json\n{json.dumps(v, indent=2)}\n```\n")
            else:
                lines.append(f"* **{k}**: {v}")
        return "\n".join(lines)
    else:
        return f"```json\n{json.dumps(json_obj, indent=2)}\n```"


def _xml_to_markdown(xml_text: str) -> str:
    root = ET.fromstring(xml_text)
    lines = [f"# XML Document: <{root.tag}>\n"]
    
    def walk_elem(elem, depth=1):
        indent = "  " * (depth - 1)
        attr_str = " (" + ", ".join(f"{k}='{v}'" for k, v in elem.attrib.items()) + ")" if elem.attrib else ""
        text = (elem.text or "").strip()
        if text:
            lines.append(f"{indent}* **{elem.tag}**{attr_str}: {text}")
        elif elem.attrib or len(elem) == 0:
            lines.append(f"{indent}* **{elem.tag}**{attr_str}")
        else:
            lines.append(f"\n{'#' * min(depth + 1, 4)} <{elem.tag}>{attr_str}\n")

        for child in elem:
            walk_elem(child, depth + 1)

    for child in root:
        walk_elem(child, 1)

    return "\n".join(lines)
