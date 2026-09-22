"""
AutoPCML Local Server
Lightweight Python server that provides real-time AutoCAD DWG conversion and PCML extraction.
Connects directly to AutoCAD 2026 accoreconsole and ezdxf.
"""

import os
import sys
import json
import glob
import subprocess
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import openpyxl
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext, layout
from ezdxf.addons.drawing.svg import SVGBackend

PORT = 8080
ACCORE_PATH = r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe"
DWG_DIR = r"c:\Users\musthaque.mayalankot\OneDrive - Pinnacle\Desktop\DWGs"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def convert_dwg(dwg_path: str, temp_dir: str):
    """Converts DWG to DXF using AutoCAD console, then parses entities and creates SVG."""
    base = os.path.splitext(os.path.basename(dwg_path))[0]
    dxf_path = os.path.join(temp_dir, f"{base}.dxf")
    svg_path = os.path.join(temp_dir, f"{base}.svg")
    scr_path = os.path.join(temp_dir, f"{base}_scr.scr")

    if not os.path.exists(dxf_path):
        with open(scr_path, "w") as f:
            f.write(f'DXFOUT "{dxf_path}" 16\nQUIT Y\n')
        cmd = [ACCORE_PATH, "/i", dwg_path, "/s", scr_path]
        subprocess.run(cmd, capture_output=True, text=True, timeout=35)

    if not os.path.exists(dxf_path):
        return None

    # Parse DXF
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    metadata = {
        "drawingId": base,
        "plant": "0014t",
        "system": "X001",
        "circuit": "010",
        "sheetNum": "04",
        "fullCircuit": "0014t-X001-010",
        "lineTag": '20"-P-0001-15A',
        "pcmlBlocks": [],
        "valves": []
    }

    for e in msp:
        if e.dxftype() == "INSERT":
            bname = e.dxf.name.upper()
            if "BORDER" in bname:
                for a in e.attribs:
                    tag = a.dxf.tag.upper()
                    val = a.dxf.text.strip()
                    if tag == "PLANT_NUMBER" and val: metadata["plant"] = val
                    elif tag == "SYSTEM_NUMBER" and val: metadata["system"] = val
                    elif tag == "CIRCUIT_NUMBER" and val: metadata["circuit"] = val
                    elif tag == "SHEET_NUMBER" and val: metadata["sheetNum"] = val
                    elif tag == "LINE_#1" and val and val != "-": metadata["lineTag"] = val
            elif "PCML" in bname:
                blk = {
                    "name": e.dxf.name,
                    "x": round(e.dxf.insert.x, 2),
                    "y": round(e.dxf.insert.y, 2),
                    "dm": "85",
                    "dmdisp": "85A",
                    "type": "A"
                }
                for a in e.attribs:
                    tag = a.dxf.tag.upper()
                    val = a.dxf.text.strip()
                    if tag == "DM": blk["dm"] = val
                    elif tag == "DMDISP": blk["dmdisp"] = val
                    elif tag == "TYPE": blk["type"] = val
                metadata["pcmlBlocks"].append(blk)
            elif "VALVE" in bname:
                metadata["valves"].append({"name": e.dxf.name, "x": round(e.dxf.insert.x, 2), "y": round(e.dxf.insert.y, 2)})

    metadata["fullCircuit"] = f"{metadata['plant']}-{metadata['system']}-{metadata['circuit']}"
    return metadata

class AutoPCMLHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/upload_dwg":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Extract uploaded file
            temp_dir = os.path.join(BASE_DIR, "scratch_dwg_temp")
            os.makedirs(temp_dir, exist_ok=True)

            dwg_save_path = os.path.join(temp_dir, "uploaded_temp.dwg")
            with open(dwg_save_path, "wb") as f:
                f.write(body)

            data = convert_dwg(dwg_save_path, temp_dir)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": data}).encode("utf-8"))
            return

        elif self.path == "/api/batch_compile":
            # Run batch compiler
            from autopcml_dwg_compiler import build_pcml_excel, convert_dwg_to_dxf, parse_dwg_dxf
            temp_dir = os.path.join(BASE_DIR, "scratch_dwg_temp")
            os.makedirs(temp_dir, exist_ok=True)
            dwgs = glob.glob(os.path.join(DWG_DIR, "*.dwg"))[:10]
            parsed = []
            for d in dwgs:
                dxf = convert_dwg_to_dxf(d, temp_dir)
                if dxf:
                    parsed.append(parse_dwg_dxf(dxf))
            out_excel = os.path.join(BASE_DIR, "PCML_Database_Batch_All_DWGs.xlsx")
            build_pcml_excel(parsed, out_excel)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "count": len(parsed), "excel": "PCML_Database_Batch_All_DWGs.xlsx"}).encode("utf-8"))
            return

        self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def run_server():
    server = HTTPServer(("127.0.0.1", PORT), AutoPCMLHandler)
    print(f"[SERVER STARTED] AutoPCML Studio Server running at: http://127.0.0.1:{PORT}/autopcml_studio.html")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
