"""
DamageMech AI - API 571 Corrosion Threat Screening Engine
Author: Google Deepmind Antigravity Pair Programmer
Purpose: Comprehensive expert system codifying API 571 damage mechanisms,
         evaluating process streams, temperature, pressure, metallurgy,
         and physical isometric DWG components.
"""

from typing import Dict, List, Any

# Complete API 571 Damage Mechanisms Master Catalog
API_571_MECHANISMS = {
    "3.27": {
        "id": "3.27",
        "name": "Erosion / Erosion-Corrosion",
        "category": "Internal Thinning",
        "standard": "API 571 Section 3.27",
        "description": "Acceleration of corrosion/thinning caused by high fluid velocity, turbulence, or impingement of suspended solids or liquid droplets.",
        "failure_mode": "Localized wall thinning, scallop marks, horseshoe depressions, sudden rupture.",
        "recommended_ndt": "Grid UT (Ultrasonic Thickness), Automated PAUT, Profile Radiography (RT).",
        "sort_dm": "85A",
        "applicable_components": ["Elbow", "Tee", "Reducer", "Control Valve Bypass", "Downstream Orifice"],
        "critical_location": "Extrados (outer curvature) of elbows, crotch of tees, high-velocity expansion/reduction zones."
    },
    "3.22": {
        "id": "3.22",
        "name": "Corrosion Under Insulation (CUI)",
        "category": "External Thinning / Environmental",
        "standard": "API 571 Section 3.22",
        "description": "Corrosion of piping exterior beneath wet thermal insulation or weatherproofing jacket due to water ingress and trapped chlorides/salts.",
        "failure_mode": "Severe localized pitting, uniform external wall loss, catastrophic loss of containment.",
        "recommended_ndt": "Pulsed Eddy Current (PEC), Profile RT, Guided Wave UT (GWT), Insulation stripping and Visual (VT).",
        "sort_dm": "22A",
        "applicable_components": ["Insulated Pipe Spool", "Pipe Support", "Elbow", "Tee", "Flange Cutout"],
        "critical_location": "Support saddles, trunnions, 6 o'clock water pooling lines, horizontal-to-vertical elbow throats, jacket seams."
    },
    "3.44": {
        "id": "3.44",
        "name": "Deadleg & Stagnant Invert Corrosion",
        "category": "Internal Under-Deposit / Thinning",
        "standard": "API 571 Section 3.44",
        "description": "Corrosion occurring in low-flow or stagnant piping where water droplets, acidic aqueous phases, or sediments settle out.",
        "failure_mode": "Under-deposit pitting, bottom-of-line groove thinning, pinhole perforation.",
        "recommended_ndt": "6 o'clock Spot UT, High-Density Scanning UT, Profile RT, Video Borescope.",
        "sort_dm": "51A",
        "applicable_components": ["Deadleg", "Bleeder", "Drain", "Bypass Loop", "Horizontal Pipe Run"],
        "critical_location": "6 o'clock bottom invert of line, lowest drain sump, blind flange cavity."
    },
    "3.45": {
        "id": "3.45",
        "name": "Microbiologically Induced Corrosion (MIC)",
        "category": "Internal Localized Pitting",
        "standard": "API 571 Section 3.45",
        "description": "Corrosion accelerated by microbiological activity (sulfate-reducing bacteria SRB, acid-producing bacteria APB) under bio-slimes.",
        "failure_mode": "Deep cup-shaped pitting with shiny undercut interiors, localized cavernous metal loss.",
        "recommended_ndt": "High-Resolution Pit Depth UT, Profile Radiography, Biological sessile swab culture.",
        "sort_dm": "45A",
        "applicable_components": ["Deadleg", "Drain", "Tee", "Treated Water Line"],
        "critical_location": "Low points, stagnant pockets, weld root crevice zones, bottom deposits."
    },
    "3.9": {
        "id": "3.9",
        "name": "Amine Stress Corrosion Cracking (Amine SCC)",
        "category": "Environmental Cracking",
        "standard": "API 571 Section 3.9",
        "description": "Alkaline stress corrosion cracking of carbon steel in aqueous amine solutions (MEA, DEA, MDEA) in non-PWHT piping.",
        "failure_mode": "Intergranular surface-breaking cracks parallel to welds, sudden brittle fracture.",
        "recommended_ndt": "Wet Fluorescent Magnetic Particle (WFMT), Phased Array UT (PAUT), Shear Wave Angle Beam.",
        "sort_dm": "09A",
        "applicable_components": ["Weld", "Heat Affected Zone (HAZ)", "Branch Connection", "Tee"],
        "critical_location": "Non-PWHT butt welds, attachment fillet welds (support trunnions), weld toe HAZ."
    },
    "3.14": {
        "id": "3.14",
        "name": "Caustic Embrittlement / Caustic SCC",
        "category": "Environmental Cracking",
        "standard": "API 571 Section 3.14",
        "description": "Cracking of steel subjected to concentrated sodium/potassium hydroxide at elevated temperatures and residual tensile stress.",
        "failure_mode": "Spider-web branched intergranular cracks, brittle blowout.",
        "recommended_ndt": "WFMT, Angle Beam Shear Wave UT, Eddy Current Array (ECA).",
        "sort_dm": "14A",
        "applicable_components": ["Weld", "Injection Quill", "Tee", "Elbow"],
        "critical_location": "Weld HAZ, caustic injection point downstream crotches, non-PWHT residual stress points."
    },
    "3.57": {
        "id": "3.57",
        "name": "Wet H2S Damage (HIC / SOHIC / SSC)",
        "category": "Environmental / Hydrogen Damage",
        "standard": "API 571 Section 3.57",
        "description": "Hydrogen-induced cracking (HIC), blistering, and stress-oriented HIC (SOHIC) in sour services containing free water and H2S.",
        "failure_mode": "Sub-surface stepwise cracking, hydrogen blisters, brittle weld cracking.",
        "recommended_ndt": "Automated PAUT / TOFD (Time-of-Flight Diffraction), WFMT on internal weld roots, Profile RT.",
        "sort_dm": "57A",
        "applicable_components": ["Weld", "Pipe Spool", "Deadleg"],
        "critical_location": "Circumferential weld seam, weld toe HAZ, bottom 6 o'clock water pooling line."
    },
    "3.17": {
        "id": "3.17",
        "name": "Chloride Stress Corrosion Cracking (Cl-SCC)",
        "category": "Environmental Cracking",
        "standard": "API 571 Section 3.17",
        "description": "Surface-initiated cracking of austenitic stainless steels (304SS, 316SS) exposed to aqueous chlorides above 140 deg F (60 deg C).",
        "failure_mode": "Heavily branched transgranular cracking through pipe wall, rapid leak or rupture.",
        "recommended_ndt": "Liquid Penetrant Testing (PT), Eddy Current Array (ECA), High-Frequency PAUT.",
        "sort_dm": "17A",
        "applicable_components": ["Stainless Steel Spool", "Weld", "Flange Crevice", "Under Insulation"],
        "critical_location": "Weld HAZ, stagnant crevices, external pipe surface beneath wet chloride-containing insulation."
    },
    "3.61": {
        "id": "3.61",
        "name": "High-Temperature Sulfidation",
        "category": "High Temperature Thinning",
        "standard": "API 571 Section 3.61",
        "description": "Reaction of sulfur-bearing hydrocarbon streams with carbon steel and low-alloy steels at temperatures above 450 deg F.",
        "failure_mode": "Relatively uniform to turbulent accelerated wall thinning with pyrophoric iron sulfide scale.",
        "recommended_ndt": "High-Temp Spot UT, Profile RT, Continuous UT sensor tracking.",
        "sort_dm": "61A",
        "applicable_components": ["Pipe Spool", "Elbow", "Furnace Outlet", "Tee"],
        "critical_location": "High-temperature crude furnace transfer piping, elbow outer sweeps, turbulent run sections."
    },
    "3.43": {
        "id": "3.43",
        "name": "Mechanical Vibration Fatigue Cracking",
        "category": "Mechanical Damage",
        "standard": "API 571 Section 3.43",
        "description": "Cyclic alternating stress induced by pump/compressor pulsations, acoustic resonance, or flow flutter causing crack initiation.",
        "failure_mode": "Transgranular fatigue cleavage cracks at stress concentrations, high-energy snap rupture.",
        "recommended_ndt": "Dye Penetrant (PT), Magnetic Particle (MT), Small-bore vibration monitoring and bracing inspection.",
        "sort_dm": "43A",
        "applicable_components": ["Small Bore Branch (NPS <= 2 in)", "Bleeder", "Thermowell", "Drain"],
        "critical_location": "Small bore pipe-to-header fillet weld toe, first unsupported elbow/socket weld."
    }
}


def screen_damage_mechanisms(
    service: str,
    temp_f: float,
    press_psi: float,
    metallurgy: str,
    insulation: str = "NO",
    pwht: str = "NO"
) -> List[Dict[str, Any]]:
    service_norm = (service or "").strip().lower()
    mat_norm = (metallurgy or "").strip().upper()
    ins_norm = (insulation or "").strip().upper() in ["YES", "Y", "IH", "IC", "INSULATED"]
    pwht_norm = (pwht or "").strip().upper() in ["YES", "Y", "PWHT"]

    results = []

    def add_threat(sec_id: str, susceptibility: str, driver: str, where_desc: str):
        mech = API_571_MECHANISMS[sec_id]
        results.append({
            "section": mech["standard"],
            "id": mech["id"],
            "name": mech["name"],
            "category": mech["category"],
            "susceptibility": susceptibility,
            "sort_dm": mech["sort_dm"],
            "key_driver": driver,
            "failure_mode": mech["failure_mode"],
            "recommended_ndt": mech["recommended_ndt"],
            "where_to_inspect": where_desc or mech["critical_location"],
            "applicable_components": mech["applicable_components"]
        })

    # Rule 1: Erosion / Erosion-Corrosion (3.27)
    if any(s in service_norm for s in ["crude", "sour", "slurry", "water", "steam", "condensate", "gas"]):
        susc = "HIGH" if any(s in service_norm for s in ["slurry", "sour", "steam"]) else "MEDIUM"
        add_threat(
            "3.27",
            susc,
            f"Dynamic fluid flow in {service} service; turbulence and impingement velocity at directional turns.",
            "Fitting Extrados (Outer Curvature of Elbows), Branch Connection Crotches, and Reducer Necks."
        )

    # Rule 2: Deadleg Stagnant Invert Corrosion (3.44)
    if any(s in service_norm for s in ["crude", "sour", "water", "treated", "amine", "condensate", "hydrocarbon"]):
        susc = "HIGH" if "sour" in service_norm or "water" in service_norm else "MEDIUM"
        add_threat(
            "3.44",
            susc,
            "Stagnant aqueous fluid / water dropout in dead ends, bleeders, and low points.",
            "6 o'clock bottom invert of horizontal runs, drain pots, and bleeder deadleg sumps."
        )

    # Rule 3: Corrosion Under Insulation - CUI (3.22)
    if ins_norm:
        if any(cs in mat_norm for cs in ["CS", "CARBON", "A106"]) or not mat_norm:
            if 25 <= temp_f <= 375:
                susc = "HIGH" if (150 <= temp_f <= 260) else "MEDIUM"
                add_threat(
                    "3.22",
                    susc,
                    f"Operating temperature ({temp_f} deg F) is inside API 571 CUI critical range (25 - 350 deg F).",
                    "Under insulation at pipe support beam contact points, vertical-to-horizontal elbow seams, and flange cutouts."
                )
        elif any(ss in mat_norm for ss in ["304", "316", "AUSTENITIC", "SS"]):
            if 140 <= temp_f <= 375:
                add_threat(
                    "3.22",
                    "HIGH",
                    f"Austenitic Stainless Steel insulated at {temp_f} deg F susceptible to External Chloride CUI/ESCC.",
                    "Pipe exterior beneath wet insulation, particularly around support saddles and sealing joints."
                )

    # Rule 4: Amine SCC (3.9)
    if "amine" in service_norm:
        if "CS" in mat_norm or "CARBON" in mat_norm or not mat_norm:
            susc = "LOW" if pwht_norm else ("HIGH" if temp_f >= 140 else "MEDIUM")
            pwht_note = "PWHT performed (mitigated)" if pwht_norm else "Non-PWHT piping (high residual stress)"
            add_threat(
                "3.9",
                susc,
                f"Aqueous amine stream with {pwht_note} at {temp_f} deg F.",
                "Circumferential pipe butt welds, pipe attachment fillet welds, and weld Heat Affected Zones (HAZ)."
            )

    # Rule 5: Caustic Embrittlement (3.14)
    if "caustic" in service_norm or "naoh" in service_norm or "koh" in service_norm:
        susc = "LOW" if pwht_norm else "HIGH"
        add_threat(
            "3.14",
            susc,
            f"Alkaline caustic service with residual weld stresses (PWHT: {pwht}).",
            "Weld seams, HAZ, and piping within 10 feet downstream of caustic injection quills."
        )

    # Rule 6: Wet H2S Damage / HIC / SSC (3.57)
    if "sour" in service_norm or "h2s" in service_norm or "acid gas" in service_norm:
        if "CS" in mat_norm or "CARBON" in mat_norm or not mat_norm:
            susc = "HIGH" if temp_f <= 200 else "MEDIUM"
            add_threat(
                "3.57",
                susc,
                f"Sour water/H2S with liquid phase below 200 deg F inducing atomic hydrogen diffusion.",
                "Circumferential pipe welds (SSC), plate mid-thickness laminations (HIC), and 6 o'clock water pooling line."
            )

    # Rule 7: High-Temperature Sulfidation (3.61)
    if any(s in service_norm for s in ["crude", "gas oil", "vacuum", "resid", "sulfur"]):
        if temp_f >= 450:
            susc = "HIGH" if "CS" in mat_norm or "CARBON" in mat_norm or not mat_norm else "MEDIUM"
            add_threat(
                "3.61",
                susc,
                f"Sulfur-bearing hydrocarbon above 450 deg F threshold ({temp_f} deg F) causing McConomy sulfidation.",
                "High-temperature furnace transfer piping, elbow outer sweeps, and turbulent run sections."
            )

    # Rule 8: Chloride SCC (3.17)
    if any(ss in mat_norm for ss in ["304", "316", "SS"]):
        if temp_f >= 140:
            add_threat(
                "3.17",
                "HIGH",
                f"Austenitic stainless steel operating at {temp_f} deg F (>140 deg F threshold) with aqueous chlorides.",
                "Circumferential weld HAZ, deadleg crevices, and external surface under wet insulation."
            )

    # Rule 9: Microbiologically Induced Corrosion - MIC (3.45)
    if any(s in service_norm for s in ["treated water", "cooling water", "firewater", "untreated water"]):
        if temp_f <= 140:
            add_threat(
                "3.45",
                "HIGH",
                f"Aqueous water service at ambient/moderate temperature ({temp_f} deg F) favoring bacterial colonies.",
                "Deadleg sumps, lowest horizontal inverts, and stagnant pipe branch loops."
            )

    # Rule 10: Mechanical Vibration Fatigue (3.43)
    add_threat(
        "3.43",
        "MEDIUM",
        "Piping system pulsations and cyclic flow fluctuations acting on cantilever small-bore branches.",
        "Small Bore Piping connections (NPS <= 2 in), bleeder valve socket welds, and drain nipple attachments."
    )

    return results


def map_dwg_component_threats(
    components: List[Dict[str, Any]],
    process_threats: List[Dict[str, Any]],
    line_meta: Dict[str, Any]
) -> List[Dict[str, Any]]:
    mapped_locations = []
    comp_counter = 1

    threat_lookup = {t["id"]: t for t in process_threats}

    for comp in components:
        c_type = comp.get("type", "UNKNOWN").upper()
        name = comp.get("name", "")
        desc = comp.get("desc", f"{c_type} Fitting")
        x = comp.get("x", 0.0)
        y = comp.get("y", 0.0)
        nps = comp.get("nps", line_meta.get("nps", '20"'))

        cid = f"COMP-{comp_counter:03d}"
        comp_counter += 1

        matched_threats = []

        # 1. Elbows
        if "ELBOW" in c_type or "ELBOW" in name:
            if "3.27" in threat_lookup:
                t = threat_lookup["3.27"]
                matched_threats.append({
                    "dm_id": "3.27",
                    "dm_name": t["name"],
                    "sort_dm": t["sort_dm"],
                    "susceptibility": t["susceptibility"],
                    "failure_mode": t["failure_mode"],
                    "ndt": "Grid UT (Radial 4-point on Extrados) / PAUT",
                    "exact_location": "Elbow Extrados (Outer Bend Curvature)",
                    "cml_code": f"CML-ELB-{comp_counter:02d}"
                })
            if line_meta.get("insulation") == "YES" and "3.22" in threat_lookup:
                t = threat_lookup["3.22"]
                matched_threats.append({
                    "dm_id": "3.22",
                    "dm_name": t["name"],
                    "sort_dm": t["sort_dm"],
                    "susceptibility": t["susceptibility"],
                    "failure_mode": t["failure_mode"],
                    "ndt": "Pulsed Eddy Current (PEC) / Profile RT",
                    "exact_location": "Elbow Throat Seam & Bottom Invert",
                    "cml_code": f"CML-CUI-{comp_counter:02d}"
                })

        # 2. Welds
        elif "WELD" in c_type or "WELD" in name:
            for crack_id in ["3.9", "3.14", "3.57", "3.17"]:
                if crack_id in threat_lookup:
                    t = threat_lookup[crack_id]
                    matched_threats.append({
                        "dm_id": crack_id,
                        "dm_name": t["name"],
                        "sort_dm": t["sort_dm"],
                        "susceptibility": t["susceptibility"],
                        "failure_mode": t["failure_mode"],
                        "ndt": t["recommended_ndt"],
                        "exact_location": "Circumferential Butt Weld Seam & HAZ (360 deg)",
                        "cml_code": f"CML-WLD-{comp_counter:02d}"
                    })
            if not matched_threats:
                matched_threats.append({
                    "dm_id": "3.27",
                    "dm_name": "Localized Weld Erosion / Step Corrosion",
                    "sort_dm": "85A",
                    "susceptibility": "MEDIUM",
                    "failure_mode": "Internal root groove thinning",
                    "ndt": "Angle Beam PAUT / Profile RT",
                    "exact_location": "Internal Weld Root & Downstream Toe",
                    "cml_code": f"CML-WLD-{comp_counter:02d}"
                })

        # 3. Deadlegs, Bleeders, Drains
        elif any(k in c_type or k in name for k in ["BLEEDER", "DL_", "DRAIN", "DEADLEG"]):
            if "3.44" in threat_lookup:
                t = threat_lookup["3.44"]
                matched_threats.append({
                    "dm_id": "3.44",
                    "dm_name": t["name"],
                    "sort_dm": t["sort_dm"],
                    "susceptibility": "HIGH",
                    "failure_mode": "Stagnant under-deposit bottom corrosion & pinhole leak",
                    "ndt": "6 o'clock Spot UT + Profile RT",
                    "exact_location": "6 o'clock Invert of Stagnant Sump & Blind Cavity",
                    "cml_code": f"CML-DL-{comp_counter:02d}"
                })
            if "3.43" in threat_lookup:
                t = threat_lookup["3.43"]
                matched_threats.append({
                    "dm_id": "3.43",
                    "dm_name": t["name"],
                    "sort_dm": t["sort_dm"],
                    "susceptibility": "HIGH",
                    "failure_mode": "Vibration fatigue at branch fillet weld",
                    "ndt": "Liquid Penetrant (PT) / Visual Vibration Survey",
                    "exact_location": "Branch-to-Header Welded Tee Crotch & Socket Root",
                    "cml_code": f"CML-VIB-{comp_counter:02d}"
                })

        # 4. Pipe Supports
        elif "SUPPORT" in c_type or "SUPPORT" in name:
            if line_meta.get("insulation") == "YES" and "3.22" in threat_lookup:
                t = threat_lookup["3.22"]
                matched_threats.append({
                    "dm_id": "3.22",
                    "dm_name": t["name"],
                    "sort_dm": t["sort_dm"],
                    "susceptibility": "HIGH",
                    "failure_mode": "CUI under damaged weatherproofing jacket",
                    "ndt": "Pulsed Eddy Current (PEC) / Guided Wave UT",
                    "exact_location": "Pipe-to-Support I-Beam Contact Interface",
                    "cml_code": f"CML-SUP-{comp_counter:02d}"
                })
            else:
                matched_threats.append({
                    "dm_id": "Atmospheric",
                    "dm_name": "Touchpoint Crevice Corrosion",
                    "sort_dm": "22A",
                    "susceptibility": "MEDIUM",
                    "failure_mode": "Atmospheric water-trapping crevice corrosion",
                    "ndt": "EMAT / Profile RT / Lift-off Visual",
                    "exact_location": "Pipe resting surface on I-Beam flange (6 o'clock)",
                    "cml_code": f"CML-SUP-{comp_counter:02d}"
                })

        # 5. Valves
        elif "VALVE" in c_type or "VALVE" in name:
            if "3.27" in threat_lookup:
                t = threat_lookup["3.27"]
                matched_threats.append({
                    "dm_id": "3.27",
                    "dm_name": t["name"],
                    "sort_dm": t["sort_dm"],
                    "susceptibility": "MEDIUM",
                    "failure_mode": "Flow turbulence impingement and cavity wear",
                    "ndt": "Point UT on Body Belly & Downstream Flange",
                    "exact_location": "Valve Internal Throat & Downstream Spool Neck",
                    "cml_code": f"CML-VLV-{comp_counter:02d}"
                })

        # 6. Straight Pipe Spools or Generic
        else:
            if "3.44" in threat_lookup:
                t = threat_lookup["3.44"]
                matched_threats.append({
                    "dm_id": "3.44",
                    "dm_name": t["name"],
                    "sort_dm": t["sort_dm"],
                    "susceptibility": t["susceptibility"],
                    "failure_mode": t["failure_mode"],
                    "ndt": "6 o'clock Spot UT",
                    "exact_location": "Pipe Bottom Invert (6 o'clock position)",
                    "cml_code": f"CML-SPL-{comp_counter:02d}"
                })

        mapped_locations.append({
            "component_id": cid,
            "component_name": name,
            "component_type": c_type,
            "desc": desc,
            "nps": nps,
            "coord_x": x,
            "coord_y": y,
            "threats": matched_threats
        })

    return mapped_locations
