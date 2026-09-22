"""
AutoPCML Engine (Python CLI & Backend Module)
Autonomous Piping Isometric & P&ID Extraction to MS Access PCML Database
Author: Reliability Data Analyst / Pinnacle Integrity Engineering
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    openpyxl = None

SAMPLE_ISOMETRICS_DB = {
    "ISO-4-HC-10101-01": {
        "drawing_id": "ISO-4-HC-10101-01",
        "plant": "Chevron Refinery",
        "unit": "Crude Unit 4",
        "circuit": "4-HC-CIR-001",
        "sheet_num": 1,
        "line_tag": '4"-HC-10101-1CS1P-H',
        "nps": '4"',
        "schedule": "Sch 40",
        "material": "CS A106-B",
        "spec": "1CS1P",
        "pipe_class": "CLASS 2",
        "design_press_psig": 150,
        "design_temp_f": 350,
        "nominal_thick": 0.237,
        "min_req_thick": 0.110,
        "components": [
            {
                "comp_id": "COMP-001",
                "type": "ELBOW_90_LR",
                "desc": "90° LR Elbow CS A234-WPB",
                "nps": '4"',
                "sch": "Sch 40",
                "material": "CS A106-B",
                "rating": "Standard",
                "cmls": [
                    {"cml_id": "CML-01", "loc": "Fitting Extrados", "x": 345, "y": 360, "conf": 0.98},
                    {"cml_id": "CML-02", "loc": "Fitting Intrados", "x": 300, "y": 395, "conf": 0.94}
                ]
            },
            {
                "comp_id": "COMP-002",
                "type": "PIPE_SPOOL",
                "desc": "Pipe Spool 18'-0\"",
                "nps": '4"',
                "sch": "Sch 40",
                "material": "CS A106-B",
                "rating": "Standard",
                "cmls": []
            },
            {
                "comp_id": "COMP-003",
                "type": "TEE_STRAIGHT",
                "desc": "4\"x4\" Straight Tee CS",
                "nps": '4"',
                "sch": "Sch 40",
                "material": "CS A106-B",
                "rating": "Standard",
                "cmls": [
                    {"cml_id": "CML-03", "loc": "Tee Crotch", "x": 320, "y": 165, "conf": 0.96}
                ]
            },
            {
                "comp_id": "COMP-004",
                "type": "REDUCER_CONC",
                "desc": "4\"x3\" Conc Reducer Sch 40",
                "nps": '4"',
                "sch": "Sch 40",
                "material": "CS A106-B",
                "rating": "Standard",
                "cmls": [
                    {"cml_id": "CML-04", "loc": "Reducer Transition", "x": 560, "y": 165, "conf": 0.91}
                ]
            },
            {
                "comp_id": "COMP-005",
                "type": "PIPE_SPOOL",
                "desc": "Pipe Spool 8'-9\"",
                "nps": '3"',
                "sch": "Sch 40",
                "material": "CS A106-B",
                "rating": "Standard",
                "cmls": [
                    {"cml_id": "CML-05", "loc": "Pipe Bottom (6 o'clock)", "x": 640, "y": 165, "conf": 0.95}
                ]
            },
            {
                "comp_id": "COMP-006",
                "type": "FLANGE_WN",
                "desc": "3\" 150# WN Flange B16.5",
                "nps": '3"',
                "sch": "Sch 40",
                "material": "CS A105",
                "rating": "150# RF",
                "cmls": []
            }
        ]
    }
}

class AutoPCMLBatchCompiler:
    def __init__(self, output_path: str = "PCML_Database_Export.xlsx"):
        self.output_path = output_path

    def compile_isometrics(self, iso_keys: List[str] = None):
        if not openpyxl:
            print("Error: openpyxl is required. Run: pip install openpyxl")
            return False

        if not iso_keys:
            iso_keys = list(SAMPLE_ISOMETRICS_DB.keys())

        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="001489", end_color="001489", fill_type="solid")
        cell_font = Font(name="Arial", size=9)
        border_thin = Border(
            left=Side(style='thin', color='D4D4D4'),
            right=Side(style='thin', color='D4D4D4'),
            top=Side(style='thin', color='D4D4D4'),
            bottom=Side(style='thin', color='D4D4D4')
        )

        def add_sheet_with_data(sheet_name: str, headers: List[str], data_rows: List[List[Any]]):
            ws = wb.create_sheet(title=sheet_name)
            ws.views.sheetView[0].showGridLines = True
            
            # Write headers
            for col_idx, h in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Write data
            for r_idx, row in enumerate(data_rows, 2):
                for c_idx, val in enumerate(row, 1):
                    cell = ws.cell(row=r_idx, column=c_idx, value=val)
                    cell.font = cell_font
                    cell.border = border_thin
            
            # Auto-fit columns
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # 1. tblCircuitSheetList
        headers_sheet_list = ["Original ISO", "Functional Location", "Circuit", "Circuit Sheet", "Sheet Number", "Notes"]
        rows_sheet_list = []
        for key in iso_keys:
            iso = SAMPLE_ISOMETRICS_DB[key]
            rows_sheet_list.append([
                iso["drawing_id"], iso["circuit"], iso["circuit"], iso["drawing_id"], iso["sheet_num"], f"Extracted via AutoPCML AI from {iso['drawing_id']}"
            ])
        add_sheet_with_data("tblCircuitSheetList", headers_sheet_list, rows_sheet_list)

        # 2. tblCircClass
        headers_circ_class = ["Circuit", "PipeClass"]
        rows_circ_class = []
        for key in iso_keys:
            iso = SAMPLE_ISOMETRICS_DB[key]
            rows_circ_class.append([iso["circuit"], iso["pipe_class"]])
        add_sheet_with_data("tblCircClass", headers_circ_class, rows_circ_class)

        # 3. tblCircDM
        headers_circ_dm = ["DMKey", "SystemNum", "CircuitNumber", "DMType", "DM", "FailureMod", "Source", "SortDM"]
        rows_circ_dm = []
        dm_key = 1
        for key in iso_keys:
            iso = SAMPLE_ISOMETRICS_DB[key]
            rows_circ_dm.append([dm_key, "100", iso["circuit"], "Internal", "Thinning / General Corrosion", "Loss of Containment", "AutoPCML Engine", "01"])
            dm_key += 1
            rows_circ_dm.append([dm_key, "100", iso["circuit"], "Internal", "Corrosion Under Insulation (CUI)", "External Wall Loss", "AutoPCML Engine", "51"])
            dm_key += 1
        add_sheet_with_data("tblCircDM", headers_circ_dm, rows_circ_dm)

        # 4. tblComponents & 5. tblCMLs
        headers_components = ["ComponentID", "Circuit", "LineNumber", "ComponentType", "Description", "NPS", "Schedule", "Material", "Rating"]
        rows_components = []
        headers_cmls = ["CML_ID", "ComponentID", "Circuit", "LineNumber", "LocationDesc", "NPS", "Schedule", "Material", "NominalThick", "MinReqThick", "X_Coord", "Y_Coord", "AI_Confidence", "Status"]
        rows_cmls = []

        for key in iso_keys:
            iso = SAMPLE_ISOMETRICS_DB[key]
            for comp in iso["components"]:
                rows_components.append([
                    comp["comp_id"], iso["circuit"], iso["line_tag"], comp["type"], comp["desc"], comp["nps"], comp["sch"], comp["material"], comp["rating"]
                ])
                for cml in comp["cmls"]:
                    rows_cmls.append([
                        cml["cml_id"], comp["comp_id"], iso["circuit"], iso["line_tag"], cml["loc"], comp["nps"], comp["sch"], comp["material"], iso["nominal_thick"], iso["min_req_thick"], cml["x"], cml["y"], f"{int(cml['conf'] * 100)}%", "Verified"
                    ])

        add_sheet_with_data("tblComponents", headers_components, rows_components)
        add_sheet_with_data("tblCMLs", headers_cmls, rows_cmls)

        wb.save(self.output_path)
        print(f"[SUCCESS] Compiled PCML Access Database to: {os.path.abspath(self.output_path)}")
        print(f" - Sheets generated: {len(wb.sheetnames)} ({', '.join(wb.sheetnames)})")
        print(f" - Components logged: {len(rows_components)}")
        print(f" - CML inspection points: {len(rows_cmls)}")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoPCML Engine - Isometric to MS Access Compiler")
    parser.add_argument("--out", type=str, default="PCML_Database_Tables.xlsx", help="Output Excel path")
    parser.add_argument("--drawing", type=str, default=None, help="Specific drawing ID to compile (e.g. ISO-4-HC-10101-01)")
    args = parser.parse_args()

    compiler = AutoPCMLBatchCompiler(output_path=args.out)
    drawings = [args.drawing] if args.drawing else None
    compiler.compile_isometrics(iso_keys=drawings)

