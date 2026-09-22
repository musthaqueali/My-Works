/**
 * DamageMech AI - API 571 Corrosion Threat Knowledge Base & Client-Side Engine
 * Master catalog of API 571 mechanisms, screening rules, and location mapping logic.
 */

const API_571_MECHANISMS = {
  "3.27": {
    id: "3.27",
    name: "Erosion / Erosion-Corrosion",
    category: "Internal Thinning",
    standard: "API 571 Section 3.27",
    description: "Acceleration of corrosion/thinning caused by high fluid velocity, turbulence, or impingement of suspended solids or liquid droplets.",
    failure_mode: "Localized wall thinning, scallop marks, horseshoe depressions, sudden rupture.",
    recommended_ndt: "Grid UT (Ultrasonic Thickness), Automated PAUT, Profile Radiography (RT).",
    sort_dm: "85A",
    applicable_components: ["Elbow", "Tee", "Reducer", "Control Valve Bypass", "Downstream Orifice"],
    critical_location: "Extrados (outer curvature) of elbows, crotch of tees, high-velocity expansion/reduction zones."
  },
  "3.22": {
    id: "3.22",
    name: "Corrosion Under Insulation (CUI)",
    category: "External Thinning / Environmental",
    standard: "API 571 Section 3.22",
    description: "Corrosion of piping exterior beneath wet thermal insulation or weatherproofing jacket due to water ingress and trapped chlorides/salts.",
    failure_mode: "Severe localized pitting, uniform external wall loss, catastrophic loss of containment.",
    recommended_ndt: "Pulsed Eddy Current (PEC), Profile RT, Guided Wave UT (GWT), Insulation stripping and Visual (VT).",
    sort_dm: "22A",
    applicable_components: ["Insulated Pipe Spool", "Pipe Support", "Elbow", "Tee", "Flange Cutout"],
    critical_location: "Support saddles, trunnions, 6 o'clock water pooling lines, horizontal-to-vertical elbow throats, jacket seams."
  },
  "3.44": {
    id: "3.44",
    name: "Deadleg & Stagnant Invert Corrosion",
    category: "Internal Under-Deposit / Thinning",
    standard: "API 571 Section 3.44",
    description: "Corrosion occurring in low-flow or stagnant piping where water droplets, acidic aqueous phases, or sediments settle out.",
    failure_mode: "Under-deposit pitting, bottom-of-line groove thinning, pinhole perforation.",
    recommended_ndt: "6 o'clock Spot UT, High-Density Scanning UT, Profile RT, Video Borescope.",
    sort_dm: "51A",
    applicable_components: ["Deadleg", "Bleeder", "Drain", "Bypass Loop", "Horizontal Pipe Run"],
    critical_location: "6 o'clock bottom invert of line, lowest drain sump, blind flange cavity."
  },
  "3.45": {
    id: "3.45",
    name: "Microbiologically Induced Corrosion (MIC)",
    category: "Internal Localized Pitting",
    standard: "API 571 Section 3.45",
    description: "Corrosion accelerated by microbiological activity (sulfate-reducing bacteria SRB, acid-producing bacteria APB) under bio-slimes.",
    failure_mode: "Deep cup-shaped pitting with shiny undercut interiors, localized cavernous metal loss.",
    recommended_ndt: "High-Resolution Pit Depth UT, Profile Radiography, Biological sessile swab culture.",
    sort_dm: "45A",
    applicable_components: ["Deadleg", "Drain", "Tee", "Treated Water Line"],
    critical_location: "Low points, stagnant pockets, weld root crevice zones, bottom deposits."
  },
  "3.9": {
    id: "3.9",
    name: "Amine Stress Corrosion Cracking (Amine SCC)",
    category: "Environmental Cracking",
    standard: "API 571 Section 3.9",
    description: "Alkaline stress corrosion cracking of carbon steel in aqueous amine solutions (MEA, DEA, MDEA) in non-PWHT piping.",
    failure_mode: "Intergranular surface-breaking cracks parallel to welds, sudden brittle fracture.",
    recommended_ndt: "Wet Fluorescent Magnetic Particle (WFMT), Phased Array UT (PAUT), Shear Wave Angle Beam.",
    sort_dm: "09A",
    applicable_components: ["Weld", "Heat Affected Zone (HAZ)", "Branch Connection", "Tee"],
    critical_location: "Non-PWHT butt welds, attachment fillet welds (support trunnions), weld toe HAZ."
  },
  "3.14": {
    id: "3.14",
    name: "Caustic Embrittlement / Caustic SCC",
    category: "Environmental Cracking",
    standard: "API 571 Section 3.14",
    description: "Cracking of steel subjected to concentrated sodium/potassium hydroxide at elevated temperatures and residual tensile stress.",
    failure_mode: "Spider-web branched intergranular cracks, brittle blowout.",
    recommended_ndt: "WFMT, Angle Beam Shear Wave UT, Eddy Current Array (ECA).",
    sort_dm: "14A",
    applicable_components: ["Weld", "Injection Quill", "Tee", "Elbow"],
    critical_location: "Weld HAZ, caustic injection point downstream crotches, non-PWHT residual stress points."
  },
  "3.57": {
    id: "3.57",
    name: "Wet H2S Damage (HIC / SOHIC / SSC)",
    category: "Environmental / Hydrogen Damage",
    standard: "API 571 Section 3.57",
    description: "Hydrogen-induced cracking (HIC), blistering, and stress-oriented HIC (SOHIC) in sour services containing free water and H2S.",
    failure_mode: "Sub-surface stepwise cracking, hydrogen blisters, brittle weld cracking.",
    recommended_ndt: "Automated PAUT / TOFD (Time-of-Flight Diffraction), WFMT on internal weld roots, Profile RT.",
    sort_dm: "57A",
    applicable_components: ["Weld", "Pipe Spool", "Deadleg"],
    critical_location: "Circumferential weld seam, weld toe HAZ, bottom 6 o'clock water pooling line."
  },
  "3.17": {
    id: "3.17",
    name: "Chloride Stress Corrosion Cracking (Cl-SCC)",
    category: "Environmental Cracking",
    standard: "API 571 Section 3.17",
    description: "Surface-initiated cracking of austenitic stainless steels (304SS, 316SS) exposed to aqueous chlorides above 140 deg F (60 deg C).",
    failure_mode: "Heavily branched transgranular cracking through pipe wall, rapid leak or rupture.",
    recommended_ndt: "Liquid Penetrant Testing (PT), Eddy Current Array (ECA), High-Frequency PAUT.",
    sort_dm: "17A",
    applicable_components: ["Stainless Steel Spool", "Weld", "Flange Crevice", "Under Insulation"],
    critical_location: "Weld HAZ, stagnant crevices, external pipe surface beneath wet chloride-containing insulation."
  },
  "3.61": {
    id: "3.61",
    name: "High-Temperature Sulfidation",
    category: "High Temperature Thinning",
    standard: "API 571 Section 3.61",
    description: "Reaction of sulfur-bearing hydrocarbon streams with carbon steel and low-alloy steels at temperatures above 450 deg F.",
    failure_mode: "Relatively uniform to turbulent accelerated wall thinning with pyrophoric iron sulfide scale.",
    recommended_ndt: "High-Temp Spot UT, Profile RT, Continuous UT sensor tracking.",
    sort_dm: "61A",
    applicable_components: ["Pipe Spool", "Elbow", "Furnace Outlet", "Tee"],
    critical_location: "High-temperature crude furnace transfer piping, elbow outer sweeps, turbulent run sections."
  },
  "3.43": {
    id: "3.43",
    name: "Mechanical Vibration Fatigue Cracking",
    category: "Mechanical Damage",
    standard: "API 571 Section 3.43",
    description: "Cyclic alternating stress induced by pump/compressor pulsations, acoustic resonance, or flow flutter causing crack initiation.",
    failure_mode: "Transgranular fatigue cleavage cracks at stress concentrations, high-energy snap rupture.",
    recommended_ndt: "Dye Penetrant (PT), Magnetic Particle (MT), Small-bore vibration monitoring and bracing inspection.",
    sort_dm: "43A",
    applicable_components: ["Small Bore Branch (NPS <= 2 in)", "Bleeder", "Thermowell", "Drain"],
    critical_location: "Small bore pipe-to-header fillet weld toe, first unsupported elbow/socket weld."
  }
};

function screenDamageMechanisms(service, tempF, pressPsi, metallurgy, insulation, pwht) {
  const serviceNorm = (service || "").toLowerCase();
  const matNorm = (metallurgy || "").toUpperCase();
  const insNorm = ["YES", "Y", "IH", "IC", "INSULATED"].includes((insulation || "").toUpperCase());
  const pwhtNorm = ["YES", "Y", "PWHT"].includes((pwht || "").toUpperCase());
  const temp = parseFloat(tempF) || 100;

  const results = [];

  function addThreat(id, susc, driver, whereDesc) {
    const m = API_571_MECHANISMS[id];
    if (!m) return;
    results.push({
      id: m.id,
      section: m.standard,
      name: m.name,
      category: m.category,
      susceptibility: susc,
      sort_dm: m.sort_dm,
      key_driver: driver,
      failure_mode: m.failure_mode,
      recommended_ndt: m.recommended_ndt,
      where_to_inspect: whereDesc || m.critical_location,
      applicable_components: m.applicable_components
    });
  }

  // 1. Erosion / Erosion-Corrosion (3.27)
  if (/crude|sour|slurry|water|steam|condensate|gas|hydrocarbon/.test(serviceNorm)) {
    const susc = /slurry|sour|steam/.test(serviceNorm) ? "HIGH" : "MEDIUM";
    addThreat("3.27", susc, `Dynamic fluid velocity in ${service} service; flow turbulence and impingement.`, "Fitting Extrados (Outer Bend of Elbows), Branch Crotches, and Reducer Necks.");
  }

  // 2. Deadleg Stagnant Invert (3.44)
  if (/crude|sour|water|treated|amine|condensate|hydrocarbon/.test(serviceNorm)) {
    const susc = /sour|water/.test(serviceNorm) ? "HIGH" : "MEDIUM";
    addThreat("3.44", susc, "Stagnant aqueous fluid / water dropout in dead ends, bleeders, and low points.", "6 o'clock bottom invert of horizontal runs, drain pots, and bleeder sumps.");
  }

  // 3. CUI (3.22)
  if (insNorm) {
    if (/CS|CARBON|A106/.test(matNorm) || !matNorm) {
      if (temp >= 25 && temp <= 375) {
        const susc = (temp >= 150 && temp <= 260) ? "HIGH" : "MEDIUM";
        addThreat("3.22", susc, `Operating temperature (${temp}°F) within API 571 CUI danger window (25°F - 350°F).`, "Under insulation at pipe support beam contact points, elbow throat seams, and flange cutouts.");
      }
    } else if (/304|316|AUSTENITIC|SS/.test(matNorm)) {
      if (temp >= 140 && temp <= 375) {
        addThreat("3.22", "HIGH", `Austenitic SS insulated at ${temp}°F susceptible to External Chloride CUI / ESCC.`, "Pipe exterior beneath wet insulation, especially at support saddles and insulation joints.");
      }
    }
  }

  // 4. Amine SCC (3.9)
  if (/amine/.test(serviceNorm)) {
    if (/CS|CARBON/.test(matNorm) || !matNorm) {
      const susc = pwhtNorm ? "LOW" : (temp >= 140 ? "HIGH" : "MEDIUM");
      addThreat("3.9", susc, `Aqueous amine stream with ${pwhtNorm ? 'PWHT (mitigated)' : 'Non-PWHT (high residual stress)'} at ${temp}°F.`, "Circumferential pipe butt welds, pipe attachment fillet welds, and weld HAZ.");
    }
  }

  // 5. Caustic Embrittlement (3.14)
  if (/caustic|naoh|koh/.test(serviceNorm)) {
    const susc = pwhtNorm ? "LOW" : "HIGH";
    addThreat("3.14", susc, `Alkaline caustic service with residual weld stresses (PWHT: ${pwhtNorm ? 'YES' : 'NO'}).`, "Weld seams, HAZ, and piping within 10 feet downstream of caustic injection quills.");
  }

  // 6. Wet H2S (3.57)
  if (/sour|h2s|acid gas/.test(serviceNorm)) {
    if (/CS|CARBON/.test(matNorm) || !matNorm) {
      const susc = temp <= 200 ? "HIGH" : "MEDIUM";
      addThreat("3.57", susc, `Sour service containing free water below 200°F inducing atomic hydrogen cracking.`, "Circumferential pipe welds (SSC), plate mid-thickness laminations (HIC), and 6 o'clock water pooling line.");
    }
  }

  // 7. Sulfidation (3.61)
  if (/crude|gas oil|vacuum|resid|sulfur/.test(serviceNorm)) {
    if (temp >= 450) {
      const susc = (/CS|CARBON/.test(matNorm) || !matNorm) ? "HIGH" : "MEDIUM";
      addThreat("3.61", susc, `Sulfur-bearing hydrocarbon above 450°F threshold (${temp}°F) causing McConomy sulfidation.`, "Furnace transfer piping, elbow outer sweeps, and turbulent run sections.");
    }
  }

  // 8. Chloride SCC (3.17)
  if (/304|316|SS/.test(matNorm)) {
    if (temp >= 140) {
      addThreat("3.17", "HIGH", `Austenitic stainless steel operating at ${temp}°F (>140°F threshold) with aqueous chlorides.`, "Circumferential weld HAZ, deadleg crevices, and external surface under wet insulation.");
    }
  }

  // 9. MIC (3.45)
  if (/treated water|cooling water|firewater|untreated water/.test(serviceNorm)) {
    if (temp <= 140) {
      addThreat("3.45", "HIGH", `Aqueous water service at ambient/moderate temperature (${temp}°F) favoring bacterial colonies.`, "Deadleg sumps, lowest horizontal inverts, and stagnant pipe branch loops.");
    }
  }

  // 10. Vibration Fatigue (3.43)
  addThreat("3.43", "MEDIUM", "Piping system pulsations and cyclic flow fluctuations acting on cantilever small-bore branches.", "Small Bore Piping connections (NPS <= 2\"), bleeder valve socket welds, and drain nipple attachments.");

  return results;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { API_571_MECHANISMS, screenDamageMechanisms };
}
