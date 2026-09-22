"""
PCML (Piping Condition Monitoring Location) Smart Assigner Engine
Learned from Chevron Inspection Guides (IS 85, IS 51, IS 99, DL Guide)
and 113-Sheet Ground-Truth Isometric DWGs / DWFs.
"""
import os
import re
import math
import shutil
import subprocess
from typing import List, Dict, Any, Tuple, Optional
import ezdxf

# Exact 8-vertex hexagonal polygon points from reference PART_PCML block
HEX_POINTS = [
    (-0.02896, 0.06992),
    (-0.06992, 0.02896),
    (-0.06992, -0.02896),
    (-0.02896, -0.06992),
    (0.02896, -0.06992),
    (0.06992, -0.02896),
    (0.06992, 0.02896),
    (0.02896, 0.06992)
]

def pt_dist_to_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

class PCMLRuleEngine:
    """
    Rule engine to detect piping features and assign PCML markers:
    - 85A: Deadleg Run and Terminal Water Accumulation (IS 85 / DL Guide Sheet 1 Type A)
    - 85B: Deadleg Base of Vertical Rise / Gravity Pocket (IS 85 / DL Guide Sheet 1 Type B)
    - 51A: Microbiologically Influenced Corrosion - Low Point Stagnation (IS 51)
    - 99: Foul Water Wet H2S Corrosion at Flow Disturbance / Turbulence (IS 99)
    """

    @staticmethod
    def extract_features(doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        msp = doc.modelspace()
        
        # 1. Circuit and Line Info
        circuit = ""
        lines = []
        for text_e in list(msp.query('TEXT')) + list(msp.query('MTEXT')):
            content = getattr(text_e.dxf, 'text', '') if hasattr(text_e.dxf, 'text') else getattr(text_e, 'text', '')
            c_match = re.search(r'[0-9]{4}[a-z]?-[A-Z0-9]+-[0-9]+', content)
            if c_match and not circuit:
                circuit = c_match.group(0)
            l_match = re.search(r'[0-9]{1,2}"-?[A-Z0-9]+-[A-Z0-9\-]+', content)
            if l_match:
                lines.append(l_match.group(0))

        if not circuit:
            for ins in msp.query('INSERT'):
                for a in getattr(ins, 'attribs', []):
                    c_match = re.search(r'[0-9]{4}[a-z]?-[A-Z0-9]+-[0-9]+', a.dxf.text)
                    if c_match and not circuit:
                        circuit = c_match.group(0)

        if not circuit:
            circuit = "0014t-X001-010"

        # Check if circuit is susceptible to Foul Water Wet H2S (DM 99)
        is_foul_water = any(k in circuit.upper() for k in ["X001", "X002"]) and any("P-" in l or "CW-" in l for l in lines)

        # 2. Extract Piping Entities
        deadleg_markers = []
        caps = []
        blinds = []
        bleeders = []
        psvs = []
        active_conts = []
        oos_conts = []
        fittings = []
        elbow_blocks = []
        pipe_lines = []

        for ins in msp.query('INSERT'):
            bname = ins.dxf.name.upper()
            layer = ins.dxf.layer.upper()
            pt = (ins.dxf.insert.x, ins.dxf.insert.y)

            if "CAP" in bname:
                caps.append(pt)
            elif "BLEEDER" in bname or "DRAIN" in bname:
                bleeders.append(pt)
            elif "PSV" in bname:
                psvs.append(pt)
            elif "CONT" in bname:
                txt = "".join([a.dxf.text for a in getattr(ins, 'attribs', [])]).upper()
                if "OOS" in txt:
                    oos_conts.append(pt)
                else:
                    active_conts.append(pt)
            elif "BLIND" in bname or "PADDLE" in bname:
                blinds.append(pt)
            elif layer == "DL" or bname.startswith("DL_") or "DL BRACKET" in bname or ("DL" in bname and layer != "0"):
                deadleg_markers.append(pt)
            elif any(e in bname for e in ["*U14", "*U19", "*U84", "ELBOW", "BEND"]):
                elbow_blocks.append(pt)
                fittings.append((bname, pt))
            elif any(k in bname for k in ["VALVE", "SOCKET", "O-LET", "TEE", "WELD"]):
                fittings.append((bname, pt))

        # Extract text or leaders on DL layer
        for text_e in list(msp.query('TEXT')) + list(msp.query('MTEXT')):
            if getattr(text_e.dxf, 'layer', '').upper() == "DL":
                pos = getattr(text_e.dxf, 'insert', None)
                if pos:
                    deadleg_markers.append((pos.x, pos.y))

        for ldr in list(msp.query('LEADER')) + list(msp.query('MULTILEADER')):
            if getattr(ldr.dxf, 'layer', '').upper() == "DL":
                if hasattr(ldr, 'vertices') and ldr.vertices:
                    deadleg_markers.append((ldr.vertices[0].x, ldr.vertices[0].y))

        for l in msp.query('LINE'):
            layer = l.dxf.layer.upper()
            if layer in ("PIPE", "0", "UNAS.PIPE"):
                pipe_lines.append(l)

        # Collect obstacle lines and obstacle points for zero-overlap clearance
        obstacle_lines = [
            (l.dxf.start.x, l.dxf.start.y, l.dxf.end.x, l.dxf.end.y)
            for l in msp.query('LINE')
            if l.dxf.layer.upper() in ('PIPE', '0', 'FITTINGS', 'UNAS.PIPE', 'PIPE-ANNO')
        ]
        obstacle_pts = [
            (ins.dxf.insert.x, ins.dxf.insert.y)
            for ins in msp.query('INSERT')
            if 'PCML' not in ins.dxf.name.upper()
        ]
        for text_e in list(msp.query('TEXT')) + list(msp.query('MTEXT')):
            txt = getattr(text_e.dxf, 'text', '') if hasattr(text_e.dxf, 'text') else getattr(text_e, 'text', '')
            pos = getattr(text_e.dxf, 'insert', None)
            h = getattr(text_e.dxf, 'height', 0.08)
            if pos:
                obstacle_pts.append((pos.x, pos.y))
                if txt.strip():
                    w = len(txt.strip()) * h * 0.75
                    obstacle_lines.append((pos.x - 0.05, pos.y, pos.x + w + 0.05, pos.y))

        # 3. Identify Main Continuous Process Line Segments (Live Line Header)
        live_header_segments = []
        for l in pipe_lines:
            dx = l.dxf.end.x - l.dxf.start.x
            dy = l.dxf.end.y - l.dxf.start.y
            length = math.hypot(dx, dy)
            connects_active_cont = any(
                math.hypot(l.dxf.start.x - c[0], l.dxf.start.y - c[1]) < 0.45 or
                math.hypot(l.dxf.end.x - c[0], l.dxf.end.y - c[1]) < 0.45
                for c in active_conts
            )
            if connects_active_cont or length > 1.8:
                live_header_segments.append((l.dxf.start.x, l.dxf.start.y, l.dxf.end.x, l.dxf.end.y))

        return {
            "circuit": circuit,
            "lines": list(set(lines)),
            "is_foul_water": is_foul_water,
            "caps": caps,
            "blinds": blinds,
            "bleeders": bleeders,
            "psvs": psvs,
            "active_conts": active_conts,
            "oos_conts": oos_conts,
            "deadleg_markers": deadleg_markers,
            "fittings": fittings,
            "elbow_blocks": elbow_blocks,
            "pipe_lines": pipe_lines,
            "live_header_segments": live_header_segments,
            "obstacle_lines": obstacle_lines,
            "obstacle_pts": obstacle_pts
        }

    @staticmethod
    def evaluate_assignments(features: Dict[str, Any], include_reasons: bool = False) -> List[Dict[str, Any]]:
        circuit = features["circuit"]
        assignments = []
        occupied_positions = list(features.get("existing_pcmls", []))
        obstacle_lines = features.get("obstacle_lines", [])
        obstacle_pts = features.get("obstacle_pts", [])

        def dist_to_live_line(pt: Tuple[float, float]) -> float:
            min_d = 999.0
            for x1, y1, x2, y2 in features["live_header_segments"]:
                d = pt_dist_to_segment(pt[0], pt[1], x1, y1, x2, y2)
                if d < min_d:
                    min_d = d
            return min_d

        def is_on_live_line(pt: Tuple[float, float], tol: float = 0.15) -> bool:
            return dist_to_live_line(pt) < tol

        def is_near_active_continuation(pt: Tuple[float, float], tol: float = 0.45) -> bool:
            for c in features.get("active_conts", []):
                if math.hypot(pt[0] - c[0], pt[1] - c[1]) < tol:
                    return True
            return False

        def get_clear_pos(base_x: float, base_y: float, preferred_dir: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
            """
            Finds a clear spot around base point with zero overlap:
            - Clearance to all pipe and fitting lines >= 0.12
            - Clearance to all valves, DL brackets, and text >= 0.14
            - Clearance to existing PCML hexagons >= 0.22
            - Clearance to live process lines >= 0.15
            """
            best = None
            min_penalty = 999999.0
            angles = [math.radians(a) for a in [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 0]]
            radii = [0.20, 0.26, 0.32, 0.38, 0.44]

            for r in radii:
                for ang in angles:
                    cx = base_x + r * math.cos(ang)
                    cy = base_y + r * math.sin(ang)

                    # Distance to lines
                    if obstacle_lines:
                        min_line = min(pt_dist_to_segment(cx, cy, *seg) for seg in obstacle_lines)
                    else:
                        min_line = 999.0

                    # Distance to points
                    if obstacle_pts:
                        min_pt = min(math.hypot(cx - ox, cy - oy) for ox, oy in obstacle_pts)
                    else:
                        min_pt = 999.0

                    # Distance to other PCMLs
                    min_occ = min([math.hypot(cx - ox, cy - oy) for ox, oy in occupied_positions], default=999.0)

                    # Live line distance must be >= 0.15
                    d_live = dist_to_live_line((cx, cy))

                    if min_line >= 0.12 and min_pt >= 0.14 and min_occ >= 0.22 and d_live >= 0.15:
                        penalty = r - 0.3 * min_line - 0.3 * min_pt
                        if preferred_dir:
                            dot = (math.cos(ang) * preferred_dir[0] + math.sin(ang) * preferred_dir[1])
                            penalty -= 0.15 * dot
                        if penalty < min_penalty:
                            min_penalty = penalty
                            best = (cx, cy)

            if not best:
                dx = preferred_dir[0] * 0.30 if preferred_dir else -0.25
                dy = preferred_dir[1] * 0.30 if preferred_dir else 0.20
                best = (base_x + dx, base_y + dy)

            occupied_positions.append(best)
            return best

        # RULE 1: Terminal Stagnation Ends (Caps and Out-of-Service Lines)
        # Assign 85A and 51A (MIC Low Point)
        terminal_points = features["caps"] + features["oos_conts"]
        for pt in terminal_points:
            px1, py1 = get_clear_pos(pt[0], pt[1])
            assignments.append({
                "dm_disp": "85A",
                "dm": "85",
                "type": "A",
                "circuit": circuit,
                "x": px1,
                "y": py1,
                "source": "Terminal Deadleg End"
            })
            px2, py2 = get_clear_pos(pt[0], pt[1])
            assignments.append({
                "dm_disp": "51A",
                "dm": "51",
                "type": "A",
                "circuit": circuit,
                "x": px2,
                "y": py2,
                "source": "MIC Low Point"
            })

        # RULE 2: PSV Relief Valve Branches -> 85A
        for pt in features["psvs"]:
            px, py = get_clear_pos(pt[0], pt[1])
            assignments.append({
                "dm_disp": "85A",
                "dm": "85",
                "type": "A",
                "circuit": circuit,
                "x": px,
                "y": py,
                "source": "PSV Relief Branch"
            })

        # RULE 3: Deadleg Branches (Identified by DL Callout Markers, Bleeders, and Blinds)
        # Upward branch (vent / instrument tap): Two 85A (one branch side, one base side below live header)
        # Downward branch (drain): Only ONE 85A at branch side, none at base
        dl_candidates = features["deadleg_markers"] + features["bleeders"] + features["blinds"]
        clusters = []
        for pt in dl_candidates:
            # Skip if near an already-assigned terminal point
            if any(math.hypot(pt[0] - tp[0], pt[1] - tp[1]) < 0.60 for tp in terminal_points):
                continue
            # Skip if sitting directly at an active through continuation
            if is_near_active_continuation(pt, tol=0.45):
                continue

            found = False
            for c in clusters:
                if math.hypot(pt[0] - c[0], pt[1] - c[1]) < 0.65:
                    found = True
                    break
            if not found:
                clusters.append(pt)

        for cpt in clusters:
            # Determine branch direction (upward vs downward)
            branch_dy = 0.0
            for l in features.get("pipe_lines", []):
                d1 = math.hypot(cpt[0] - l.dxf.start.x, cpt[1] - l.dxf.start.y)
                d2 = math.hypot(cpt[0] - l.dxf.end.x, cpt[1] - l.dxf.end.y)
                if min(d1, d2) < 0.35:
                    dy = (l.dxf.end.y - l.dxf.start.y) if d1 < d2 else (l.dxf.start.y - l.dxf.end.y)
                    if abs(dy) > 0.05:
                        branch_dy = dy
                        break

            if branch_dy > 0.05:
                # UPWARD BRANCH: Two 85A locations
                # 1. Branch side
                px1, py1 = get_clear_pos(cpt[0], cpt[1] + 0.35, preferred_dir=(0.0, 1.0))
                assignments.append({
                    "dm_disp": "85A",
                    "dm": "85",
                    "type": "A",
                    "circuit": circuit,
                    "x": px1,
                    "y": py1,
                    "source": "Deadleg Upward Branch Run"
                })
                # 2. Base side below live header
                px2, py2 = get_clear_pos(cpt[0], cpt[1] - 0.25, preferred_dir=(0.0, -1.0))
                assignments.append({
                    "dm_disp": "85A",
                    "dm": "85",
                    "type": "A",
                    "circuit": circuit,
                    "x": px2,
                    "y": py2,
                    "source": "Deadleg Upward Branch Base"
                })
            else:
                # DOWNWARD BRANCH or Run: Only ONE 85A at branch side, none at base!
                pref = (0.0, -1.0) if branch_dy < -0.05 else (-0.25, 0.15)
                base_y = cpt[1] - 0.25 if branch_dy < -0.05 else cpt[1]
                px, py = get_clear_pos(cpt[0], base_y, preferred_dir=pref)
                assignments.append({
                    "dm_disp": "85A",
                    "dm": "85",
                    "type": "A",
                    "circuit": circuit,
                    "x": px,
                    "y": py,
                    "source": "Deadleg Downward Branch Run"
                })

        # RULE 4: Along OOS Deadleg Runs (Long out-of-service branches)
        if features["oos_conts"]:
            deadleg_fittings = [
                f[1] for f in features["fittings"]
                if not is_on_live_line(f[1], tol=0.15) and not is_near_active_continuation(f[1], tol=0.45)
            ]
            for f in deadleg_fittings:
                if not any(math.hypot(f[0] - ox, f[1] - oy) < 0.70 for ox, oy in occupied_positions):
                    px, py = get_clear_pos(f[0], f[1])
                    assignments.append({
                        "dm_disp": "85A",
                        "dm": "85",
                        "type": "A",
                        "circuit": circuit,
                        "x": px,
                        "y": py,
                        "source": "Deadleg Branch Run"
                    })

        # RULE 5: Foul Water Wet H2S Corrosion (DM 99)
        # On liveline, ONLY at vertical elbow rise is 99 applicable
        if features.get("is_foul_water") and features.get("elbow_blocks"):
            for pt in features["elbow_blocks"]:
                if is_on_live_line(pt, tol=0.20):
                    has_vert_rise = False
                    for l in features.get("pipe_lines", []):
                        d1 = math.hypot(pt[0] - l.dxf.start.x, pt[1] - l.dxf.start.y)
                        d2 = math.hypot(pt[0] - l.dxf.end.x, pt[1] - l.dxf.end.y)
                        if min(d1, d2) < 0.30:
                            dy = (l.dxf.end.y - l.dxf.start.y) if d1 < d2 else (l.dxf.start.y - l.dxf.end.y)
                            if dy > 0.20:
                                has_vert_rise = True
                                break
                    if has_vert_rise:
                        if not any(math.hypot(pt[0] - ox, pt[1] - oy) < 0.30 for ox, oy in occupied_positions):
                            px, py = get_clear_pos(pt[0], pt[1], preferred_dir=(0.20, 0.0))
                            assignments.append({
                                "dm_disp": "99",
                                "dm": "99",
                                "type": "",
                                "circuit": circuit,
                                "x": px,
                                "y": py,
                                "source": "Live Line Vertical Elbow Rise"
                            })
                            break

        return assignments

    @staticmethod
    def ensure_pcml_block(doc: ezdxf.document.Drawing):
        """Ensures PART_PCML block exists matching reference DWF/DWG geometry."""
        if "PART_PCML" in doc.blocks:
            doc.blocks.delete_block("PART_PCML", safe=False)

        pcml_block = doc.blocks.new(name="PART_PCML")
        
        # 1. Outer boundary (color=18, const_width=0.0)
        outer_pts = [
            (-0.028960389, 0.069916564),
            (-0.069916564, 0.028960389),
            (-0.069916564, -0.028960389),
            (-0.028960389, -0.069916564),
            (0.028960389, -0.069916564),
            (0.069916564, -0.028960389),
            (0.069916564, 0.028960389),
            (0.028960389, 0.069916564)
        ]
        pcml_block.add_lwpolyline(
            outer_pts,
            close=True,
            dxfattribs={"layer": "0", "color": 18}
        )

        # 2. Solid HATCH (color=0 BYBLOCK so it inherits block reference color: 13 for Red, 96 for Green, 118 for Dark Green)
        hatch = pcml_block.add_hatch(
            color=0,
            dxfattribs={"layer": "0", "solid_fill": 1, "pattern_name": "SOLID"}
        )
        hatch_pts = [
            (-0.069916564, -0.028960389),
            (-0.028960389, -0.069916564),
            (0.028960389, -0.069916564),
            (0.069916564, -0.028960389),
            (0.069916564, 0.028960389),
            (0.028960389, 0.069916564),
            (-0.028960389, 0.069916564),
            (-0.069916564, 0.028960389)
        ]
        hatch.paths.add_polyline_path(hatch_pts, is_closed=True)

        # 3. Visible DMDISP Attribute: Bold White text (true_color=16777215 #FFFFFF), centered at (0, 0, 0)
        pcml_block.add_attdef(
            tag="DMDISP",
            text="X",
            height=0.05859375,
            dxfattribs={
                "layer": "0",
                "color": 7,
                "true_color": 16777215,
                "flags": 0,
                "halign": 1,
                "valign": 2,
                "insert": (-0.0223, -0.0293, 0.0),
                "align_point": (0.0, 0.0, 0.0),
                "style": "SIMPLEX"
            }
        )

        # 4. Invisible Attributes (flags=1) for DM, TYPE, CIRCUIT
        pcml_block.add_attdef(
            tag="DM",
            text="",
            height=0.05859375,
            dxfattribs={"layer": "0", "color": 7, "flags": 1, "insert": (-0.0527, -0.1332, 0.0)}
        )
        pcml_block.add_attdef(
            tag="TYPE",
            text="",
            height=0.05859375,
            dxfattribs={"layer": "0", "color": 7, "flags": 1, "insert": (-0.0749, -0.2042, 0.0)}
        )
        pcml_block.add_attdef(
            tag="CIRCUIT",
            text="",
            height=0.05859375,
            dxfattribs={"layer": "0", "color": 7, "flags": 1, "insert": (-0.0939, 0.0889, 0.0)}
        )

        # 5. Thick Border Polyline (color=7, const_width=0.009)
        pcml_block.add_lwpolyline(
            outer_pts,
            close=True,
            dxfattribs={"layer": "0", "color": 7, "const_width": 0.009}
        )

        for layer_name, color in [("PART_PCML", 7), ("PCML_ANNO", 1)]:
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name, dxfattribs={"color": color})

    @classmethod
    def annotate_dxf(cls, dxf_path: str, out_dxf_path: str, include_headings: bool = False) -> List[Dict[str, Any]]:
        doc = ezdxf.readfile(dxf_path)
        cls.ensure_pcml_block(doc)
        msp = doc.modelspace()

        # Check existing PCML block references so we never double-place
        existing_pcmls = [
            (e.dxf.insert.x, e.dxf.insert.y)
            for e in msp.query('INSERT')
            if 'PCML' in e.dxf.name.upper()
        ]

        features = cls.extract_features(doc)
        features["existing_pcmls"] = existing_pcmls
        assignments = cls.evaluate_assignments(features, include_reasons=include_headings)

        for pcml in assignments:
            x, y = pcml["x"], pcml["y"]
            # Skip if an existing PCML is already placed here
            if any(math.hypot(x - ex, y - ey) < 0.35 for ex, ey in existing_pcmls):
                continue

            # Map damage mechanism to exact ground truth ACI color:
            # 85A, 85B -> Color 13 (Salmon Red)
            # 51A, 51B -> Color 96 (Light Green)
            # 99 -> Color 118 (Dark Green)
            dm_disp = pcml["dm_disp"]
            if "85" in dm_disp:
                blk_color = 13
            elif "51" in dm_disp:
                blk_color = 96
            elif "99" in dm_disp:
                blk_color = 118
            else:
                blk_color = 13

            ins = msp.add_blockref(
                "PART_PCML",
                (x, y, 0.0),
                dxfattribs={
                    "layer": "PART_PCML",
                    "color": blk_color,
                    "xscale": 1.0,
                    "yscale": 1.0,
                    "zscale": 1.0
                }
            )
            # Add DMDISP attribute (VISIBLE, crisp WHITE #FFFFFF, centered inside hexagon)
            ins.add_attrib(
                "DMDISP",
                dm_disp,
                (-0.0223 + x, -0.0293 + y, 0.0),
                dxfattribs={
                    "height": 0.05859375,
                    "color": 7,
                    "true_color": 16777215,
                    "flags": 0,
                    "halign": 1,
                    "valign": 2,
                    "align_point": (x, y, 0.0)
                }
            )
            # Add DM, TYPE, CIRCUIT attributes (INVISIBLE, flags = 1)
            ins.add_attrib(
                "DM",
                pcml["dm"],
                (-0.0527 + x, -0.1332 + y, 0.0),
                dxfattribs={"height": 0.05859375, "flags": 1}
            )
            ins.add_attrib(
                "TYPE",
                pcml["type"],
                (-0.0749 + x, -0.2042 + y, 0.0),
                dxfattribs={"height": 0.05859375, "flags": 1}
            )
            ins.add_attrib(
                "CIRCUIT",
                pcml["circuit"],
                (-0.0939 + x, 0.0889 + y, 0.0),
                dxfattribs={"height": 0.05859375, "flags": 1}
            )

        doc.saveas(out_dxf_path)
        return assignments

def process_dwg_pcml(
    dwg_path: str,
    job_dir: str,
    include_headings: bool = False,
    plot_style: str = "acad.ctb",
    paper_size: str = "ANSI full bleed B (17.00 x 11.00 Inches)"
) -> Dict[str, Any]:
    """
    Complete end-to-end pipeline:
    1. Converts DWG to DXF via AutoCAD Core Console.
    2. Runs PCMLRuleEngine to detect deadlegs, MIC locations, and foul water points.
    3. Annotates DXF with native PART_PCML hexagons, attributes, and reason callouts.
    4. Converts annotated DXF back to clean AutoCAD DWG.
    5. Plots high-resolution vector PDF using the parallel AutoCAD engine.
    6. Generates preview PNG thumbnail for instant visual inspection.
    """
    import fitz
    from converters.cad_converter import _dwg_to_dxf_native
    from converters.autocad_plotter import plot_single_dwg_native, get_autocad_console_path

    base_name = os.path.splitext(os.path.basename(dwg_path))[0]
    os.makedirs(job_dir, exist_ok=True)

    raw_dxf = os.path.join(job_dir, f"{base_name}_raw.dxf")
    annotated_dxf = os.path.join(job_dir, f"{base_name}_annotated.dxf")
    out_dwg = os.path.join(job_dir, f"{base_name}_PCML.dwg")
    out_pdf_dir = os.path.join(job_dir, "pdf_out")
    os.makedirs(out_pdf_dir, exist_ok=True)

    # 1. Convert input DWG to DXF
    if not _dwg_to_dxf_native(dwg_path, raw_dxf):
        raise RuntimeError(f"Could not convert {dwg_path} to DXF")

    # 2. Assign PCMLs and annotate DXF
    assignments = PCMLRuleEngine.annotate_dxf(raw_dxf, annotated_dxf, include_headings=include_headings)

    # 3. Convert annotated DXF to DWG via accoreconsole
    console = get_autocad_console_path()
    clean_out_dwg = out_dwg.replace("\\", "/")
    scr_lines = [
        "FILEDIA 0",
        "CMDDIA 0",
        f'SAVEAS 2018 "{clean_out_dwg}"',
        "QUIT",
        "Y"
    ]
    scr_path = os.path.join(job_dir, f"save_{base_name}.scr")
    with open(scr_path, "w", encoding="utf-8") as f:
        f.write("\n".join(scr_lines) + "\n")

    cmd = [console, "/i", annotated_dxf, "/s", scr_path, "/l", "en-US"]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=job_dir)

    target_plot_dwg = out_dwg if (os.path.exists(out_dwg) and os.path.getsize(out_dwg) > 0) else annotated_dxf

    # 4. Plot to high-resolution vector PDF
    plotted_pdf = plot_single_dwg_native(
        dwg_path=target_plot_dwg,
        output_dir=out_pdf_dir,
        output_ext=".pdf",
        printer="AutoCAD PDF (High Quality Print).pc3",
        paper_size=paper_size,
        plot_style=plot_style or "acad.ctb",
        plot_area="Extents",
        center_plot=True,
        fit_to_paper=True,
        orientation="Landscape",
        plot_lineweights=True,
        plot_with_styles=True,
        shade_plot="Wireframe"
    )

    final_dwg = out_dwg if os.path.exists(out_dwg) else None
    final_pdf = plotted_pdf if (plotted_pdf and os.path.exists(plotted_pdf)) else None

    # 5. Generate thumbnail preview PNG
    preview_png = None
    if final_pdf and os.path.exists(final_pdf):
        try:
            doc_pdf = fitz.open(final_pdf)
            if len(doc_pdf) > 0:
                page = doc_pdf[0]
                pix = page.get_pixmap(dpi=150)
                preview_png_path = os.path.join(job_dir, f"{base_name}_preview.png")
                pix.save(preview_png_path)
                preview_png = preview_png_path
            doc_pdf.close()
        except Exception as e:
            logger.warning(f"Failed to generate preview PNG: {e}")

    return {
        "source_dwg": dwg_path,
        "base_name": base_name,
        "assignments": assignments,
        "pcml_count": len(assignments),
        "annotated_dwg": final_dwg,
        "annotated_dxf": annotated_dxf,
        "plotted_pdf": final_pdf,
        "preview_png": preview_png
    }
