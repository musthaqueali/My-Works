import os
import sys
import subprocess
import tempfile
import time
import shutil
import glob
import concurrent.futures
from typing import List, Dict, Any, Optional
import pymupdf

def get_autocad_console_path() -> Optional[str]:
    """
    Dynamically finds accoreconsole.exe from:
    1. AUTOCAD_CONSOLE_PATH environment variable
    2. AutoCAD 2026, 2025, 2024 installations
    3. Autodesk DWG TrueView 2026, 2025, 2024 installations
    4. Any Autodesk installation folder containing accoreconsole.exe
    """
    env_path = os.environ.get("AUTOCAD_CONSOLE_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # 1. First priority: Full AutoCAD installations (2027, 2026, 2025, 2024, 2023, 2022)
    acad_candidates = [
        r"C:\Program Files\Autodesk\AutoCAD 2027\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2025\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2024\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe",
    ]
    for c in acad_candidates:
        if os.path.exists(c):
            return c

    # Search dynamically for any full AutoCAD installation
    for root_dir in [r"C:\Program Files\Autodesk", r"C:\Program Files (x86)\Autodesk"]:
        if os.path.isdir(root_dir):
            try:
                for entry in sorted(os.listdir(root_dir), reverse=True):
                    if "autocad" in entry.lower() and "trueview" not in entry.lower():
                        c = os.path.join(root_dir, entry, "accoreconsole.exe")
                        if os.path.exists(c):
                            return c
            except Exception:
                pass

    # 2. Second priority: Autodesk DWG TrueView installations
    trueview_candidates = [
        r"C:\Program Files\Autodesk\DWG TrueView 2027 - English\accoreconsole.exe",
        r"C:\Program Files\Autodesk\DWG TrueView 2026 - English\accoreconsole.exe",
        r"C:\Program Files\Autodesk\DWG TrueView 2025 - English\accoreconsole.exe",
        r"C:\Program Files\Autodesk\DWG TrueView 2024 - English\accoreconsole.exe",
    ]
    for c in trueview_candidates:
        if os.path.exists(c):
            return c

    for root_dir in [r"C:\Program Files\Autodesk", r"C:\Program Files (x86)\Autodesk"]:
        if os.path.isdir(root_dir):
            try:
                for entry in sorted(os.listdir(root_dir), reverse=True):
                    if "trueview" in entry.lower():
                        c = os.path.join(root_dir, entry, "accoreconsole.exe")
                        if os.path.exists(c):
                            return c
            except Exception:
                pass

    return None

def get_autocad_plot_styles_dir() -> Optional[str]:
    """Dynamically locates the Autodesk Plot Styles directory across any user account or version."""
    env_dir = os.environ.get("AUTOCAD_PLOT_STYLES_DIR")
    if env_dir and os.path.exists(env_dir):
        return env_dir
    appdata = os.environ.get("APPDATA")
    if appdata:
        autodesk_dir = os.path.join(appdata, "Autodesk")
        if os.path.isdir(autodesk_dir):
            try:
                for root, dirs, files in os.walk(autodesk_dir):
                    if os.path.basename(root).lower() == "plot styles":
                        return root
            except Exception:
                pass
    return None

AUTOCAD_CONSOLE_PATH = get_autocad_console_path()
AUTOCAD_PLOT_STYLES_DIR = get_autocad_plot_styles_dir()

def is_autocad_available() -> bool:
    return get_autocad_console_path() is not None

def generate_plot_script(
    output_path: str,
    printer: str = "AutoCAD PDF (High Quality Print).pc3",
    paper_size: str = "ANSI full bleed B (17.00 x 11.00 Inches)",
    plot_style: str = "acad.ctb",
    plot_area: str = "Extents",
    center_plot: bool = True,
    fit_to_paper: bool = True,
    orientation: str = "Landscape",
    plot_lineweights: bool = True,
    plot_with_styles: bool = True,
    shade_plot: str = "Wireframe",
    layout_name: str = "Model",
) -> str:
    units = "Millimeters" if ("mm" in paper_size.lower() or "iso" in paper_size.lower()) else "Inches"
    clean_out = output_path.replace("\\", "/")
    
    ctb_name = plot_style if (plot_with_styles and plot_style and plot_style.lower() != "none") else "."
    
    script_lines = [
        "EXPERT 5",
        "PROXYNOTICE 0",
        "PROXYSHOW 1",
        "CMDDIA 0",
        "FILEDIA 0",
        "SAVETIME 0",
        "VTENABLE 0",
        "-LAYER",
        "T",
        "*",
        "ON",
        "*",
        "U",
        "*",
        "",
        "ZOOM",
        "E",
        "-PLOT",
        "Yes",
        layout_name,
        printer,
        paper_size,
        units,
        orientation,
        "No",
        plot_area,
        "Fit" if fit_to_paper else "1:1",
        "Center" if center_plot else "0,0",
        "Yes" if plot_with_styles else "No",
        ctb_name,
        "Yes" if plot_lineweights else "No",
        shade_plot,
        f'"{clean_out}"',
        "No",
        "Yes",
        "QUIT",
        "Y"
    ]
    return "\n".join(script_lines) + "\n"

def get_autocad_plotters_dir() -> Optional[str]:
    """Locates the Autodesk Plotters directory across user profiles and versions."""
    env_dir = os.environ.get("AUTOCAD_PLOTTERS_DIR")
    if env_dir and os.path.exists(env_dir):
        return env_dir
    appdata = os.environ.get("APPDATA")
    if appdata:
        autodesk_dir = os.path.join(appdata, "Autodesk")
        if os.path.isdir(autodesk_dir):
            for root, dirs, files in os.walk(autodesk_dir):
                if os.path.basename(root).lower() == "plotters":
                    return root
    return None

AUTOCAD_PLOTTERS_DIR = get_autocad_plotters_dir()

def plot_single_dwg_native(
    dwg_path: str,
    output_dir: str,
    output_ext: str = ".pdf",
    printer: str = "AutoCAD PDF (High Quality Print).pc3",
    paper_size: str = "ANSI full bleed B (17.00 x 11.00 Inches)",
    plot_style: str = "acad.ctb",
    plot_area: str = "Extents",
    center_plot: bool = True,
    fit_to_paper: bool = True,
    orientation: str = "Landscape",
    plot_lineweights: bool = True,
    plot_with_styles: bool = True,
    shade_plot: str = "Wireframe",
    custom_ctb_path: Optional[str] = None,
    timeout_sec: int = 90
) -> Optional[str]:
    dwg_path = os.path.abspath(dwg_path)
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(dwg_path))[0]
    out_file = os.path.abspath(os.path.join(output_dir, f"{base_name}{output_ext}"))
    
    console_path = get_autocad_console_path()
    if not console_path or not os.path.exists(console_path):
        return None

    # DWG TrueView ships with "DWG To PDF.pc3", not "AutoCAD PDF (High Quality Print).pc3"
    if "trueview" in console_path.lower() and "autocad pdf" in printer.lower():
        printer = "DWG To PDF.pc3"

    plot_styles_dir = AUTOCAD_PLOT_STYLES_DIR or get_autocad_plot_styles_dir()

    active_ctb = plot_style
    if custom_ctb_path and os.path.exists(custom_ctb_path):
        custom_ctb_name = os.path.basename(custom_ctb_path)
        dwg_dir = os.path.dirname(dwg_path)
        dest_ctb = os.path.join(dwg_dir, custom_ctb_name)
        if not os.path.exists(dest_ctb):
            shutil.copyfile(custom_ctb_path, dest_ctb)
        try:
            if plot_styles_dir and os.path.exists(plot_styles_dir):
                sys_ctb = os.path.join(plot_styles_dir, custom_ctb_name)
                if not os.path.exists(sys_ctb):
                    shutil.copyfile(custom_ctb_path, sys_ctb)
        except Exception:
            pass
        active_ctb = custom_ctb_name
    else:
        # Check bundled plot_styles directory
        local_plot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plot_styles")
        if os.path.exists(local_plot_dir) and active_ctb:
            bundled_ctb = os.path.join(local_plot_dir, active_ctb)
            if os.path.exists(bundled_ctb):
                dwg_dir = os.path.dirname(dwg_path)
                dest_ctb = os.path.join(dwg_dir, active_ctb)
                if not os.path.exists(dest_ctb):
                    try: shutil.copyfile(bundled_ctb, dest_ctb)
                    except Exception: pass
                try:
                    if plot_styles_dir and os.path.exists(plot_styles_dir):
                        sys_ctb = os.path.join(plot_styles_dir, active_ctb)
                        if not os.path.exists(sys_ctb):
                            shutil.copyfile(bundled_ctb, sys_ctb)
                except Exception:
                    pass

    # Ensure bundled PC3 files (DWG To PDF.pc3, etc.) are available in dwg_dir and system Plotters
    plotters_dir = AUTOCAD_PLOTTERS_DIR or get_autocad_plotters_dir()
    local_plot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plot_styles")
    if os.path.exists(local_plot_dir):
        for f in os.listdir(local_plot_dir):
            if f.lower().endswith(".pc3"):
                src_pc3 = os.path.join(local_plot_dir, f)
                dst_dwg = os.path.join(os.path.dirname(dwg_path), f)
                if not os.path.exists(dst_dwg):
                    try: shutil.copyfile(src_pc3, dst_dwg)
                    except Exception: pass
                if plotters_dir and os.path.isdir(plotters_dir):
                    dst_sys = os.path.join(plotters_dir, f)
                    if not os.path.exists(dst_sys):
                        try: shutil.copyfile(src_pc3, dst_sys)
                        except Exception: pass
    
    scr_content = generate_plot_script(
        output_path=out_file,
        printer=printer,
        paper_size=paper_size,
        plot_style=active_ctb,
        plot_area=plot_area,
        center_plot=center_plot,
        fit_to_paper=fit_to_paper,
        orientation=orientation,
        plot_lineweights=plot_lineweights,
        plot_with_styles=plot_with_styles,
        shade_plot=shade_plot
    )
    
    scr_file = os.path.join(output_dir, f"plot_{base_name}.scr")
    with open(scr_file, "w", encoding="utf-8") as f:
        f.write(scr_content)
        
    cmd = [
        console_path,
        "/i", dwg_path,
        "/s", scr_file,
        "/l", "en-US",
        "/readonly"
    ]
    
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
            cwd=os.path.dirname(dwg_path)
        )

        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.log")
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] [AutoCAD Native Plot for {base_name}]\n")
                lf.write(f"Cmd: {' '.join(cmd)}\n")
                lf.write(f"Exit code: {proc.returncode}\n")
                lf.write(f"STDOUT:\n{proc.stdout}\n")
                if proc.stderr:
                    lf.write(f"STDERR:\n{proc.stderr}\n")
        except Exception:
            pass

        actual_out = None
        if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            actual_out = out_file
        else:
            pattern = os.path.join(output_dir, f"{base_name}*{output_ext}")
            matches = glob.glob(pattern)
            if matches and os.path.getsize(matches[0]) > 0:
                actual_out = matches[0]

        # Automatic fallback retry if initial plotter/paper combination was rejected
        if not actual_out and output_ext == ".pdf":
            for alt_printer in ["DWG To PDF.pc3", "AutoCAD PDF (High Quality Print).pc3"]:
                if alt_printer.lower() == printer.lower():
                    continue
                for alt_paper in ["ANSI full bleed B (17.00 x 11.00 Inches)", "ANSI B (17.00 x 11.00 Inches)", "Letter"]:
                    scr_alt = generate_plot_script(
                        output_path=out_file,
                        printer=alt_printer,
                        paper_size=alt_paper,
                        plot_style=active_ctb,
                        plot_area=plot_area,
                        center_plot=center_plot,
                        fit_to_paper=fit_to_paper,
                        orientation=orientation,
                        plot_lineweights=plot_lineweights,
                        plot_with_styles=plot_with_styles,
                        shade_plot=shade_plot
                    )
                    with open(scr_file, "w", encoding="utf-8") as f:
                        f.write(scr_alt)
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout_sec, cwd=os.path.dirname(dwg_path))
                    if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                        actual_out = out_file
                        break
                    m = glob.glob(os.path.join(output_dir, f"{base_name}*{output_ext}"))
                    if m and os.path.getsize(m[0]) > 0:
                        actual_out = m[0]
                        break
        if actual_out and output_ext == ".pdf" and os.path.exists(actual_out):
            try:
                from converters.cad_converter import ensure_pdf_contrast_and_lineweights
                ensure_pdf_contrast_and_lineweights(actual_out)
            except Exception:
                pass

        return actual_out
    except Exception as e:
        print(f"[AutoCAD Plotter] Exception: {e}")
        return None

def merge_dwf_files(dwf_paths: List[str], output_path: str, dwg_names: Optional[List[str]] = None) -> Optional[str]:
    """
    Merges multiple single-sheet DWF6 files into one multi-sheet DWF file.
    
    DWF6 files are ZIP-based containers. Each single-sheet DWF contains:
      - manifest.xml (root manifest listing all sections)
      - com.autodesk.dwf.ePlot_<GUID>/ (one section per sheet with W2D, descriptor, fonts, thumbnail)
      - com.autodesk.dwf.ePlotGlobal/ (optional global section with DSD)
    
    To ensure AutoCAD Design Review 2018 renders every sheet without showing blank:
      1. Preserves each sheet's exact internal section and descriptor references
      2. Renames collisions gracefully if necessary, updating descriptor.xml references
      3. Aggregates all ePlot sections into a single master manifest.xml with ordered sheets
      4. Wraps inside standard DWF6 container header
    """
    import zipfile
    import uuid
    import io

    valid_inputs = []
    for p in dwf_paths:
        if os.path.exists(p) and os.path.getsize(p) > 0 and zipfile.is_zipfile(p):
            valid_inputs.append(p)
    
    if not valid_inputs:
        return None

    # If only one DWF, copy it directly
    if len(valid_inputs) == 1:
        shutil.copy2(valid_inputs[0], output_path)
        return output_path

    master_manifest_id = str(uuid.uuid4()).upper()
    sections_xml = []
    all_files = {}  # path_in_zip -> bytes
    used_section_dirs = set()
    global_section_written = False
    sheet_idx = 0

    for src_idx, dwf_path in enumerate(valid_inputs):
        try:
            with zipfile.ZipFile(dwf_path, 'r') as zf:
                entries = zf.namelist()
                
                # Derive sheet title from DWG filename
                if dwg_names and src_idx < len(dwg_names):
                    dwg_base = os.path.splitext(os.path.basename(dwg_names[src_idx]))[0]
                else:
                    dwg_base = os.path.splitext(os.path.basename(dwf_path))[0]

                # Parse manifest.xml from this DWF to get original section metadata
                manifest_xml_data = ""
                if 'manifest.xml' in entries:
                    manifest_xml_data = zf.read('manifest.xml').decode('utf-8', errors='ignore')

                # Identify all ePlot section folders
                section_dirs = []
                for e in entries:
                    if 'com.autodesk.dwf.ePlot_' in e and 'ePlotGlobal' not in e:
                        sdir = e.split('/')[0]
                        if sdir not in section_dirs:
                            section_dirs.append(sdir)

                for old_section_dir in section_dirs:
                    sheet_idx += 1
                    # Ensure section folder is unique in merged archive
                    if old_section_dir in used_section_dirs:
                        new_guid = str(uuid.uuid4()).upper()
                        target_section_dir = f"com.autodesk.dwf.ePlot_{new_guid}"
                    else:
                        target_section_dir = old_section_dir
                    used_section_dirs.add(target_section_dir)

                    need_remap = (target_section_dir != old_section_dir)
                    section_resources = []

                    for entry in entries:
                        if entry.startswith(old_section_dir + '/'):
                            rel_name = entry[len(old_section_dir) + 1:]
                            new_zip_path = f"{target_section_dir}/{rel_name}"
                            content = zf.read(entry)

                            # If directory was renamed, update internal descriptor references
                            if need_remap and rel_name == 'descriptor.xml':
                                desc_str = content.decode('utf-8', errors='ignore')
                                desc_str = desc_str.replace(old_section_dir, target_section_dir)
                                desc_str = desc_str.replace(old_section_dir.replace('/', '\\'), target_section_dir.replace('/', '\\'))
                                content = desc_str.encode('utf-8')

                            all_files[new_zip_path] = content

                            # Build manifest resource elements matching AutoCAD standard
                            if rel_name.endswith('.w2d'):
                                section_resources.append(
                                    f'<dwf:Resource role="2d streaming graphics" mime="application/x-w2d" href="{target_section_dir}\\{rel_name}"/>'
                                )
                            elif rel_name == 'descriptor.xml':
                                section_resources.append(
                                    f'<dwf:Resource role="descriptor" mime="text/xml" href="{target_section_dir}\\{rel_name}"/>'
                                )
                            elif rel_name.endswith('.png'):
                                section_resources.append(
                                    f'<dwf:Resource role="thumbnail" mime="image/png" href="{target_section_dir}\\{rel_name}"/>'
                                )
                            elif rel_name.endswith('.pia'):
                                section_resources.append(
                                    f'<dwf:Resource role="AutoCAD Viewport Data" mime="application/x-dwg-state" href="{target_section_dir}\\{rel_name}"/>'
                                )
                            elif rel_name.endswith('.ef_'):
                                section_resources.append(
                                    f'<dwf:Resource role="font" mime="application/x-font" href="{target_section_dir}\\{rel_name}"/>'
                                )

                    sheet_title = dwg_base
                    toc_xml = "\n        ".join(section_resources)
                    section_xml = (
                        f'    <dwf:Section type="com.autodesk.dwf.ePlot" '
                        f'name="{target_section_dir}" title="{sheet_title}">\n'
                        f'      <dwf:Source provider="AutoCAD" href="{dwg_base}.dwg"/>\n'
                        f'      <dwf:Toc>\n'
                        f'        {toc_xml}\n'
                        f'      </dwf:Toc>\n'
                        f'    </dwf:Section>'
                    )
                    sections_xml.append(section_xml)

                # Copy global section if available (only once)
                if not global_section_written:
                    for entry in entries:
                        if entry.startswith('com.autodesk.dwf.ePlotGlobal/'):
                            all_files[entry] = zf.read(entry)
                            global_section_written = True

        except Exception as e:
            print(f"[DWF Merge] Error processing {dwf_path}: {e}")
            continue

    if not sections_xml:
        return None

    # Global section entry in manifest
    global_toc = ""
    if global_section_written:
        global_resources = []
        for p in all_files:
            if p.startswith('com.autodesk.dwf.ePlotGlobal/'):
                rel = p[len('com.autodesk.dwf.ePlotGlobal/'):]
                if rel == 'descriptor.xml':
                    global_resources.append(f'<dwf:Resource role="descriptor" mime="text/xml" href="com.autodesk.dwf.ePlotGlobal\\{rel}"/>')
                elif rel.endswith('.dsd'):
                    global_resources.append(f'<dwf:Resource role="AutoCAD Drawing Set Data" mime="application/x-dsd" href="com.autodesk.dwf.ePlotGlobal\\{rel}"/>')
        if global_resources:
            gtoc_lines = "\n        ".join(global_resources)
            global_toc = (
                f'    <dwf:Section type="com.autodesk.dwf.ePlotGlobal" name="com.autodesk.dwf.ePlotGlobal" title="com.autodesk.dwf.ePlotGlobal">\n'
                f'      <dwf:Source provider="AutoCAD" href="BatchSet.dwg"/>\n'
                f'      <dwf:Toc>\n'
                f'        {gtoc_lines}\n'
                f'      </dwf:Toc>\n'
                f'    </dwf:Section>\n'
            )

    sections_block = global_toc + "\n".join(sections_xml)
    manifest_xml = (
        f'<dwf:Manifest xmlns:dwf="DWF-Manifest:6.0" version="6.0" objectId="{master_manifest_id}">\n'
        f'  <dwf:Interfaces>\n'
        f'    <dwf:Interface objectId="715941D4-1AC2-4545-8185-BC40E053B551" name="ePlot" href="http://www.autodesk.com/viewers"/>\n'
        f'  </dwf:Interfaces>\n'
        f'  <dwf:Properties>\n'
        f'    <dwf:Property name="DWFProductVendor" value="Autodesk, Inc."/>\n'
        f'    <dwf:Property name="SourceProductName" value="AutoCAD"/>\n'
        f'    <dwf:Property name="SourceProductVendor" value="Autodesk, Inc."/>\n'
        f'  </dwf:Properties>\n'
        f'  <dwf:Sections>\n'
        f'{sections_block}\n'
        f'  </dwf:Sections>\n'
        f'</dwf:Manifest>'
    )

    DWF6_HEADER = b"(DWF V06.00)"
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        zout.writestr('manifest.xml', manifest_xml.encode('utf-8'))
        for path_in_zip, data in all_files.items():
            zout.writestr(path_in_zip, data)

    with open(output_path, 'wb') as f:
        f.write(DWF6_HEADER)
        f.write(zip_buf.getvalue())

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path
    return None


def batch_plot_dwg(
    dwg_paths: List[str],
    job_dir: str,
    printer: str = "AutoCAD PDF (High Quality Print).pc3",
    paper_size: str = "ANSI full bleed B (17.00 x 11.00 Inches)",
    plot_style: str = "acad.ctb",
    plot_area: str = "Extents",
    center_plot: bool = True,
    fit_to_paper: bool = True,
    orientation: str = "Landscape",
    plot_lineweights: bool = True,
    plot_with_styles: bool = True,
    shade_plot: str = "Wireframe",
    custom_ctb_path: Optional[str] = None,
    merge_output: bool = True
) -> Dict[str, Any]:
    start_time = time.time()
    os.makedirs(job_dir, exist_ok=True)
    
    if "dwf" in printer.lower() or "dwfx" in printer.lower():
        output_ext = ".dwf"
    elif "png" in printer.lower():
        output_ext = ".png"
    elif "jpg" in printer.lower() or "jpeg" in printer.lower():
        output_ext = ".jpg"
    else:
        output_ext = ".pdf"

    is_dwf = output_ext == ".dwf"
    is_pdf = output_ext == ".pdf"
    preview_thumbnail_rel = None

    # Preflight setup: copy custom CTB and bundled CTB/PC3 once to avoid parallel file contention
    plot_styles_dir = AUTOCAD_PLOT_STYLES_DIR or get_autocad_plot_styles_dir()
    plotters_dir = AUTOCAD_PLOTTERS_DIR or get_autocad_plotters_dir()
    local_plot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plot_styles")

    if custom_ctb_path and os.path.exists(custom_ctb_path):
        custom_ctb_name = os.path.basename(custom_ctb_path)
        dest_ctb = os.path.join(job_dir, custom_ctb_name)
        if not os.path.exists(dest_ctb):
            try: shutil.copyfile(custom_ctb_path, dest_ctb)
            except Exception: pass
        if plot_styles_dir and os.path.isdir(plot_styles_dir):
            sys_ctb = os.path.join(plot_styles_dir, custom_ctb_name)
            if not os.path.exists(sys_ctb):
                try: shutil.copyfile(custom_ctb_path, sys_ctb)
                except Exception: pass

    if os.path.exists(local_plot_dir):
        for f in os.listdir(local_plot_dir):
            fl = f.lower()
            if fl.endswith(".ctb"):
                dst = os.path.join(job_dir, f)
                if not os.path.exists(dst):
                    try: shutil.copyfile(os.path.join(local_plot_dir, f), dst)
                    except Exception: pass
                if plot_styles_dir and os.path.isdir(plot_styles_dir):
                    dst_sys = os.path.join(plot_styles_dir, f)
                    if not os.path.exists(dst_sys):
                        try: shutil.copyfile(os.path.join(local_plot_dir, f), dst_sys)
                        except Exception: pass
            elif fl.endswith(".pc3"):
                dst = os.path.join(job_dir, f)
                if not os.path.exists(dst):
                    try: shutil.copyfile(os.path.join(local_plot_dir, f), dst)
                    except Exception: pass
                if plotters_dir and os.path.isdir(plotters_dir):
                    dst_sys = os.path.join(plotters_dir, f)
                    if not os.path.exists(dst_sys):
                        try: shutil.copyfile(os.path.join(local_plot_dir, f), dst_sys)
                        except Exception: pass

    # Worker function to plot an individual drawing with fallback
    def _plot_worker(item):
        idx, dwg_path = item
        plotted = None
        if is_autocad_available():
            plotted = plot_single_dwg_native(
                dwg_path=dwg_path,
                output_dir=job_dir,
                output_ext=output_ext,
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
                custom_ctb_path=custom_ctb_path
            )
        if plotted and os.path.exists(plotted):
            return idx, plotted, None

        # Fallback to secondary converter if native plot was not available or failed
        try:
            from converters.cad_converter import convert_cad
            base_name = os.path.splitext(os.path.basename(dwg_path))[0]
            target_fmt = output_ext.lstrip(".")
            fallback_out = os.path.join(job_dir, f"{base_name}{output_ext}")
            ok = convert_cad(
                dwg_path,
                fallback_out,
                target_format=target_fmt,
                paper_size=paper_size,
                orientation=orientation,
                plot_style=plot_style,
                plot_with_styles=plot_with_styles,
                plot_lineweights=plot_lineweights,
                plot_area=plot_area,
                shade_plot=shade_plot,
                custom_ctb_path=custom_ctb_path
            )
            if ok and os.path.exists(fallback_out) and os.path.getsize(fallback_out) > 0:
                return idx, fallback_out, None
            else:
                return idx, None, os.path.basename(dwg_path)
        except Exception as fe:
            print(f"[AutoCAD Batch Plot Fallback] {fe}")
            return idx, None, os.path.basename(dwg_path)

    # Determine optimal worker count based on system CPU cores and drawing quantity
    cpu_cores = os.cpu_count() or 4
    # Run up to 12 parallel workers on multi-core systems, reserving CPU headroom
    max_workers = min(len(dwg_paths), max(1, min(cpu_cores - 2, 12)))
    if max_workers < 1:
        max_workers = 1

    indexed_dwgs = list(enumerate(dwg_paths))
    results = []

    if max_workers > 1 and len(dwg_paths) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_plot_worker, indexed_dwgs))
    else:
        results = [_plot_worker(item) for item in indexed_dwgs]

    # Ensure sheets maintain the exact order they were uploaded
    results.sort(key=lambda r: r[0])

    plotted_files = [r[1] for r in results if r[1]]
    failed_files = [r[2] for r in results if r[2]]

    if not plotted_files:
        raise RuntimeError("No drawings could be plotted.")
        
    # Merge outputs into a unified multi-sheet document
    if is_pdf and merge_output and len(plotted_files) > 1:
        final_filename = "AutoCAD_Batch_Plot_Booklet.pdf"
        final_output_path = os.path.join(job_dir, final_filename)
        
        merged_doc = pymupdf.open()
        for pdf_path in plotted_files:
            try:
                sub_doc = pymupdf.open(pdf_path)
                merged_doc.insert_pdf(sub_doc)
                sub_doc.close()
            except Exception as me:
                print(f"Error appending {pdf_path}: {me}")
                
        merged_doc.save(final_output_path)
        merged_doc.close()

    elif is_dwf and merge_output and len(plotted_files) > 1:
        final_filename = "AutoCAD_Batch_Plot_Drawing_Set.dwf"
        final_output_path = os.path.join(job_dir, final_filename)
        merged_res = merge_dwf_files(plotted_files, final_output_path, dwg_names=dwg_paths)
        if not (merged_res and os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 0):
            # Fallback to single file or archive if merge failed
            final_output_path = plotted_files[0]
            final_filename = os.path.basename(final_output_path)

    elif len(plotted_files) == 1:
        final_output_path = plotted_files[0]
        final_filename = os.path.basename(final_output_path)
    else:
        final_filename = "AutoCAD_Batch_Plot_Archive.zip"
        zip_base = os.path.join(job_dir, "AutoCAD_Batch_Plot_Archive")
        zip_staging_dir = os.path.join(job_dir, "staging")
        os.makedirs(zip_staging_dir, exist_ok=True)
        
        for pf in plotted_files:
            shutil.copy2(pf, os.path.join(zip_staging_dir, os.path.basename(pf)))
            
        shutil.make_archive(zip_base, "zip", zip_staging_dir)
        final_output_path = f"{zip_base}.zip"

    # Always generate or extract preview thumbnail for Sheet 1
    thumb_path = os.path.join(job_dir, "preview_sheet_1.png")
    preview_data_url = None

    # Priority 1: If output is PDF or we have a plotted PDF, render page 0 with PyMuPDF at high DPI (250 DPI)
    if is_pdf and os.path.exists(final_output_path) and final_output_path.endswith(".pdf"):
        try:
            preview_doc = pymupdf.open(final_output_path)
            if len(preview_doc) > 0:
                page = preview_doc[0]
                pix = page.get_pixmap(dpi=250)
                pix.save(thumb_path)
                preview_thumbnail_rel = "preview_sheet_1.png"
                try:
                    import base64
                    img_bytes = pix.tobytes("webp") if hasattr(pix, "tobytes") else pix.tobytes("png")
                    mime = "image/webp" if hasattr(pix, "tobytes") else "image/png"
                    preview_data_url = f"data:{mime};base64,{base64.b64encode(img_bytes).decode('ascii')}"
                except Exception:
                    try:
                        import base64
                        with open(thumb_path, "rb") as im_f:
                            preview_data_url = f"data:image/png;base64,{base64.b64encode(im_f.read()).decode('ascii')}"
                    except Exception:
                        pass
            preview_doc.close()
        except Exception as te:
            print(f"PDF thumbnail generation error: {te}")

    # Priority 1b: If output is PNG or JPG raster, copy sheet 1 directly as thumbnail
    elif output_ext in (".png", ".jpg", ".jpeg") and plotted_files and os.path.exists(plotted_files[0]):
        try:
            shutil.copy2(plotted_files[0], thumb_path)
            preview_thumbnail_rel = "preview_sheet_1.png"
            try:
                import base64
                with open(thumb_path, "rb") as im_f:
                    mime = "image/jpeg" if output_ext in (".jpg", ".jpeg") else "image/png"
                    preview_data_url = f"data:{mime};base64,{base64.b64encode(im_f.read()).decode('ascii')}"
            except Exception:
                pass
        except Exception as te:
            print(f"Raster thumbnail generation error: {te}")

    # Priority 2: If DWF, extract AutoCAD's embedded high-fidelity PNG thumbnail from the DWF
    if not preview_thumbnail_rel and plotted_files and plotted_files[0].lower().endswith(".dwf") and os.path.exists(plotted_files[0]):
        try:
            import zipfile
            with zipfile.ZipFile(plotted_files[0], 'r') as zf:
                png_members = [m for m in zf.namelist() if m.lower().endswith(".png")]
                if png_members:
                    raw_png = zf.read(png_members[0])
                    with open(thumb_path, "wb") as out_f:
                        out_f.write(raw_png)
                    preview_thumbnail_rel = "preview_sheet_1.png"
                    import base64
                    preview_data_url = f"data:image/png;base64,{base64.b64encode(raw_png).decode('ascii')}"
        except Exception as ze:
            print(f"DWF thumbnail extraction error: {ze}")

    # Priority 3: Universal Fallback using CAD converter
    if not preview_thumbnail_rel and dwg_paths and os.path.exists(dwg_paths[0]):
        try:
            from converters.cad_converter import convert_cad
            ok = convert_cad(dwg_paths[0], thumb_path, "png")
            if ok and os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                preview_thumbnail_rel = "preview_sheet_1.png"
                import base64
                with open(thumb_path, "rb") as im_f:
                    preview_data_url = f"data:image/png;base64,{base64.b64encode(im_f.read()).decode('ascii')}"
        except Exception as te:
            print(f"Universal CAD thumbnail error: {te}")

    duration_ms = int((time.time() - start_time) * 1000)
    file_size = os.path.getsize(final_output_path) if os.path.exists(final_output_path) else 0

    return {
        "output_path": final_output_path,
        "output_filename": final_filename,
        "sheets_plotted": len(plotted_files),
        "total_files": len(dwg_paths),
        "failed_files": failed_files,
        "duration_ms": duration_ms,
        "file_size": file_size,
        "preview_thumbnail": preview_thumbnail_rel,
        "preview_data_url": preview_data_url,
        "printer": printer,
        "paper_size": paper_size,
        "plot_style": plot_style,
        "is_unified_booklet": is_pdf and merge_output and len(plotted_files) > 1
    }