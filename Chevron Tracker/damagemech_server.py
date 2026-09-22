"""
DamageMech Server - Backend API for API 571 Screening & DWG Location Mapping
Runs lightweight Python HTTP server on port 8085.
"""

import os
import sys
import json
import glob
import subprocess
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import damagemech_rules
import damagemech_dwg_engine

PORT = 8085
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DWG_DIR = r"c:\Users\musthaque.mayalankot\OneDrive - Pinnacle\Desktop\DWGs"
TEMP_DIR = os.path.join(BASE_DIR, "scratch_dwg_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

class DamageMechHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/sample_dwgs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            files = []
            if os.path.exists(DWG_DIR):
                for f in glob.glob(os.path.join(DWG_DIR, "*.dwg")):
                    files.append({
                        "name": os.path.basename(f),
                        "path": f,
                        "size": os.path.getsize(f)
                    })
            self.wfile.write(json.dumps(files[:20]).encode("utf-8"))
            return

        if path == "/api/download_excel":
            excel_path = os.path.join(BASE_DIR, "DamageMech_PCML_Database.xlsx")
            if os.path.exists(excel_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                self.send_header("Content-Disposition", 'attachment; filename="DamageMech_Chevron_PCML_Database.xlsx"')
                self.send_header("Content-Length", str(os.path.getsize(excel_path)))
                self.end_headers()
                with open(excel_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Excel database not generated yet.")
                return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if path == "/api/screen_threats":
            try:
                data = json.loads(body.decode("utf-8"))
                threats = damagemech_rules.screen_damage_mechanisms(
                    service=data.get("service", "Crude Oil"),
                    temp_f=float(data.get("temp_f", 300)),
                    press_psi=float(data.get("press_psi", 150)),
                    metallurgy=data.get("metallurgy", "Carbon Steel"),
                    insulation=data.get("insulation", "NO"),
                    pwht=data.get("pwht", "NO")
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"threats": threats}).encode("utf-8"))
            except Exception as e:
                self.send_error(500, str(e))
            return

        if path == "/api/analyze_dwg":
            try:
                data = json.loads(body.decode("utf-8"))
                dwg_name = data.get("dwg_name", "0014t-X001-010-04.dwg")
                dwg_full_path = os.path.join(DWG_DIR, dwg_name) if not os.path.isabs(dwg_name) else dwg_name
                dxf_file = os.path.join(TEMP_DIR, os.path.splitext(os.path.basename(dwg_full_path))[0] + ".dxf")

                # If temp_04.dxf exists in root, use it as fast fallback
                if not os.path.exists(dxf_file) and "04" in dwg_name and os.path.exists(os.path.join(BASE_DIR, "temp_04.dxf")):
                    dxf_file = os.path.join(BASE_DIR, "temp_04.dxf")

                if not os.path.exists(dxf_file) and os.path.exists(dwg_full_path):
                    dxf_file = damagemech_dwg_engine.convert_dwg_to_dxf(dwg_full_path, TEMP_DIR)

                if not dxf_file or not os.path.exists(dxf_file):
                    self.send_error(400, f"Could not convert or find DWG/DXF: {dwg_name}")
                    return

                drawing_data = damagemech_dwg_engine.parse_dwg_drawing(dxf_file)

                # Process overrides if supplied
                service = data.get("service")
                temp = data.get("temp_f")
                if temp is not None:
                    temp = float(temp)
                if data.get("insulation"):
                    drawing_data["insulation"] = data.get("insulation")
                if data.get("pwht"):
                    drawing_data["pwht"] = data.get("pwht")

                results = damagemech_dwg_engine.run_damagemech_mapping(drawing_data, service_override=service, temp_override=temp)

                # Generate excel
                excel_path = os.path.join(BASE_DIR, "DamageMech_PCML_Database.xlsx")
                damagemech_dwg_engine.export_chevron_pcml_excel(results, excel_path)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(results).encode("utf-8"))
            except Exception as e:
                self.send_error(500, str(e))
            return

        self.send_error(404, "Unknown endpoint")

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, DamageMechHandler)
    print(f"[SERVER READY] DamageMech AI Server listening on http://localhost:{PORT}")
    print(f"Open http://localhost:{PORT}/damagemech_app.html in your browser.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
