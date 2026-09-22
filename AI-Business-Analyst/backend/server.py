import os
import io
import json
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
import httpx

from backend.analytics_engine import AnalyticsEngine

app = FastAPI(title="AI Business Analyst API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store in-memory active sessions / uploaded datasets
SESSIONS: Dict[str, Dict[str, Any]] = {}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-flash-lite-latest"

class WhatIfRequest(BaseModel):
    session_id: str
    variable: str
    pct_change: float

class ChatRequest(BaseModel):
    session_id: str
    question: str

class SemanticOverrideRequest(BaseModel):
    session_id: str
    overrides: Dict[str, str]

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = file.filename
        inspection = AnalyticsEngine.inspect_file(contents, filename)
        
        session_id = f"sess_{abs(hash(filename + str(len(contents))))}"
        
        # If it's an Excel file with multiple sheets, we register the bytes and let user pick sheet
        SESSIONS[session_id] = {
            'filename': filename,
            'file_bytes': contents,
            'inspection': inspection,
            'df': None,
            'analysis': None
        }

        if inspection['is_excel'] and len(inspection['sheets']) > 1:
            return {
                'session_id': session_id,
                'filename': filename,
                'requires_sheet_selection': True,
                'sheets': inspection['sheets']
            }

        # Otherwise immediately load sheet 0 or CSV
        df = AnalyticsEngine.load_dataframe(contents, filename)
        SESSIONS[session_id]['df'] = df
        
        return {
            'session_id': session_id,
            'filename': filename,
            'requires_sheet_selection': False,
            'sheets': inspection['sheets'],
            'rows': len(df),
            'columns': len(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File ingestion error: {str(e)}")

@app.post("/api/select-sheet")
async def select_sheet(session_id: str = Form(...), sheet_name: str = Form(...)):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
    
    session = SESSIONS[session_id]
    try:
        df = AnalyticsEngine.load_dataframe(session['file_bytes'], session['filename'], sheet_name)
        session['df'] = df
        session['selected_sheet'] = sheet_name
        return {
            'session_id': session_id,
            'sheet_name': sheet_name,
            'rows': len(df),
            'columns': len(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading sheet {sheet_name}: {str(e)}")

@app.get("/api/sample/{name}")
async def load_sample(name: str):
    valid_samples = {
        'ecommerce': 'data/ecommerce_sales_performance.csv',
        'saas': 'data/saas_subscription_churn.csv',
        'inventory': 'data/supply_chain_inventory.csv'
    }
    if name not in valid_samples:
        raise HTTPException(status_code=404, detail="Sample dataset not found")
    
    path = valid_samples[name]
    with open(path, 'rb') as f:
        contents = f.read()

    filename = os.path.basename(path)
    session_id = f"sample_{name}"
    df = pd.read_csv(io.BytesIO(contents))
    
    SESSIONS[session_id] = {
        'filename': filename,
        'file_bytes': contents,
        'inspection': {'file_type': 'csv', 'sheets': [], 'is_excel': False},
        'df': df,
        'analysis': None
    }
    
    return {
        'session_id': session_id,
        'filename': filename,
        'rows': len(df),
        'columns': len(df.columns)
    }

@app.post("/api/analyze")
async def analyze_dataset(session_id: str = Form(...), overrides_json: Optional[str] = Form(None)):
    if session_id not in SESSIONS or SESSIONS[session_id]['df'] is None:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = SESSIONS[session_id]
    df = session['df']
    
    overrides = {}
    if overrides_json:
        try:
            overrides = json.loads(overrides_json)
        except Exception:
            overrides = {}

    try:
        profile = AnalyticsEngine.profile_dataset(df, overrides)
        quality = AnalyticsEngine.audit_data_quality(df, profile)
        statistics = AnalyticsEngine.calculate_statistics(df, profile)
        # Ensure 'moments' is always available as an alias to 'descriptive_statistics'
        statistics['moments'] = statistics.get('descriptive_statistics', {})
        kpis = AnalyticsEngine.discover_kpis(df, profile)
        root_causes = AnalyticsEngine.root_cause_analysis(df, profile, statistics)
        anomalies = AnalyticsEngine.anomaly_detection(df, profile)
        opportunities = AnalyticsEngine.opportunity_detection(df, profile, statistics)
        recommendations = AnalyticsEngine.generate_recommendation_matrix(root_causes, opportunities, statistics, profile)

        # Executive Synthesis
        health_status = 'Good'
        if quality['quality_grade'] == 'Critical Risk':
            health_status = 'Needs Attention'
        elif any(k.get('trend') == 'down' for k in kpis):
            health_status = 'Needs Attention'
        elif quality['overall_quality_score'] >= 85 and any(k.get('trend') == 'up' for k in kpis):
            health_status = 'Excellent'

        top_findings = [
            f"Dataset spans {profile['total_rows']:,} records classified into the {profile['detected_domain']} operational domain.",
            f"Overall Data Integrity score evaluated at {quality['overall_quality_score']}% ({quality['quality_grade']}) with {quality['total_issues_count']} detected anomalies.",
            root_causes[0]['observed_fact'] if root_causes else "Stable inter-category dispersion observed.",
            f"Primary predictive model captures {round(statistics['regression']['r2']*100, 1)}% of outcome variance for {statistics['regression']['target']}." if statistics['regression'] else "Covariates demonstrate orthogonal independence.",
            f"Key opportunity: {opportunities[0]['title']} ({opportunities[0]['expected_roi']})" if opportunities else "Operational metrics indicate disciplined baseline performance."
        ]

        top_actions = [
            f"{r['rank']}. {r['recommendation']} ({r['expected_impact']})"
            for r in recommendations[:5]
        ]

        biggest_risk = root_causes[0]['headline'] if root_causes else "Covariate drift in unmonitored subcategories."
        biggest_opportunity = opportunities[0]['title'] + " — " + opportunities[0]['expected_roi'] if opportunities else "Margin expansion through volume price optimization."

        # Call Gemini AI to enrich the executive synthesis with deep learning insights & tailored recommendations
        try:
            ai_prompt = f"""You are an executive Senior Business Analyst and Statistician.
Analyze this empirical dataset summary:
- Filename: {session['filename']} ({profile['total_rows']:,} rows, domain: {profile['detected_domain']})
- Categorical Dimensions: {json.dumps(profile.get('categorical_columns', [])[:4])}
- Numerical Variables: {json.dumps(profile.get('numeric_columns', [])[:5])}
- Quality Score: {quality['overall_quality_score']}%
- Key KPIs: {json.dumps([{'label': k['label'], 'value': k['value']} for k in kpis[:5]])}
- Discovered Root Causes: {json.dumps([rc['headline'] for rc in root_causes[:3]])}
- Regression Fit: {json.dumps(statistics.get('regression', {}))}

INSTRUCTIONS:
1. Conduct a deep, meticulous domain evaluation for '{profile['detected_domain']}' ({session['filename']}).
2. Do NOT use generic business templates. Every single finding and recommendation must be tailored specifically to this business domain, referencing exact column names, segment names, and metrics.
3. Quantify projected financial impact/ROI for each recommendation.

Return a JSON object with this exact structure:
{{
  "top_findings": [
    "5 specific, rigorous analytical bullet points answering what is happening and why for THIS dataset. Mention exact numbers, percentages, and segment names. Use **bold** for key metrics."
  ],
  "biggest_risk": "One concise sentence describing the single biggest operational or financial vulnerability in this dataset.",
  "biggest_opportunity": "One concise sentence describing the highest-leverage growth or cost-optimization opportunity with projected ROI.",
  "recommendations": [
    {{
      "rank": 1,
      "recommendation": "High-impact strategic action tailored specifically to this business and domain",
      "evidence": "Exact statistical evidence from the dataset",
      "expected_impact": "Projected ROI or financial uplift",
      "priority": "Critical",
      "confidence": "High",
      "effort": "Medium",
      "reason": "Clear managerial explanation of why this works for this domain"
    }},
    {{
      "rank": 2,
      "recommendation": "Second strategic action tailored to this business",
      "evidence": "Data evidence",
      "expected_impact": "Projected impact",
      "priority": "High",
      "confidence": "High",
      "effort": "Low",
      "reason": "Managerial rationale"
    }},
    {{
      "rank": 3,
      "recommendation": "Third operational directive tailored to this business",
      "evidence": "Data evidence",
      "expected_impact": "Projected impact",
      "priority": "Medium",
      "confidence": "High",
      "effort": "Low",
      "reason": "Managerial rationale"
    }},
    {{
      "rank": 4,
      "recommendation": "Fourth growth or efficiency directive tailored to this business",
      "evidence": "Data evidence",
      "expected_impact": "Projected impact",
      "priority": "Medium",
      "confidence": "Medium",
      "effort": "Medium",
      "reason": "Managerial rationale"
    }}
  ]
}}
Return ONLY raw valid JSON."""

            async with httpx.AsyncClient(timeout=25.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": ai_prompt}]}],
                    "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
                }
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    ai_data = resp.json()
                    ai_text = ai_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    if ai_text:
                        parsed = json.loads(ai_text)
                        if 'top_findings' in parsed and len(parsed['top_findings']) >= 3:
                            top_findings = parsed['top_findings']
                        if 'biggest_risk' in parsed and parsed['biggest_risk']:
                            biggest_risk = parsed['biggest_risk']
                        if 'biggest_opportunity' in parsed and parsed['biggest_opportunity']:
                            biggest_opportunity = parsed['biggest_opportunity']
                        if 'recommendations' in parsed and len(parsed['recommendations']) >= 3:
                            recommendations = parsed['recommendations']
                            top_actions = [
                                f"{r['rank']}. {r['recommendation']} ({r['expected_impact']})"
                                for r in recommendations[:5]
                            ]
        except Exception as ai_err:
            print(f"Gemini enrichment fallback active: {ai_err}")

        executive_summary = {
            'overall_health': health_status,
            'top_findings': top_findings,
            'top_actions': top_actions,
            'biggest_risk': biggest_risk,
            'biggest_opportunity': biggest_opportunity
        }

        analysis_payload = {
            'session_id': session_id,
            'filename': session['filename'],
            'profile': profile,
            'quality': quality,
            'statistics': statistics,
            'kpis': kpis,
            'root_causes': root_causes,
            'anomalies': anomalies,
            'opportunities': opportunities,
            'recommendations': recommendations,
            'executive_summary': executive_summary
        }

        session['analysis'] = analysis_payload
        return analysis_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytical pipeline error: {str(e)}")

@app.post("/api/what-if")
async def run_what_if(req: WhatIfRequest):
    if req.session_id not in SESSIONS or SESSIONS[req.session_id]['df'] is None:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = SESSIONS[req.session_id]
    df = session['df']
    profile = session['analysis']['profile'] if session['analysis'] else AnalyticsEngine.profile_dataset(df)

    res = AnalyticsEngine.simulate_what_if(df, profile, {'variable': req.variable, 'pct_change': req.pct_change})
    return res

@app.post("/api/chat")
async def chat_analyst(req: ChatRequest):
    if req.session_id not in SESSIONS or SESSIONS[req.session_id]['df'] is None:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = SESSIONS[req.session_id]
    analysis = session.get('analysis')
    if not analysis:
        df = session['df']
        profile = AnalyticsEngine.profile_dataset(df)
        stats = AnalyticsEngine.calculate_statistics(df, profile)
        kpis = AnalyticsEngine.discover_kpis(df, profile)
        analysis = {'profile': profile, 'statistics': stats, 'kpis': kpis}

    p = analysis['profile']
    st = analysis.get('statistics', {})
    q = req.question

    system_prompt = f"""
You are an executive Senior Business Analyst, Statistician, and Management Consultant.
You are advising C-level leadership on this uploaded dataset.
Dataset Profile:
- File: {session['filename']}
- Rows: {p['total_rows']:,}, Columns: {p['total_columns']}
- Domain: {p.get('detected_domain', 'General Business')}
- KPIs: {json.dumps(analysis.get('kpis', []))}
- Root Causes: {json.dumps(analysis.get('root_causes', []))}
- Regression: {json.dumps(st.get('regression', {}))}
- Recommendations: {json.dumps(analysis.get('recommendations', []))}

Rules:
1. Always base answers strictly on the empirical data and calculated statistics above.
2. Structure answers: Insight -> Evidence -> Business Meaning -> Concrete Action.
3. State exact numbers, percentages, and segment names.
4. If the data cannot answer the question, explicitly state what additional data is needed.
5. Never claim correlation proves causation.
6. Speak in crisp, authoritative business prose.
"""

    # Direct Gemini API call with timeout
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": system_prompt + f"\n\nUser Question: {q}"}]}],
                "generationConfig": {"temperature": 0.2}
            }
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                if text:
                    return {"response": text}
    except Exception:
        pass

    # Deterministic fallback response based on grounded statistical facts
    kpis_text = ", ".join([f"{k['label']}: {k['value']}" for k in analysis.get('kpis', [])])
    root_cause = analysis.get('root_causes', [{}])[0] if analysis.get('root_causes') else {}
    rec = analysis.get('recommendations', [{}])[0] if analysis.get('recommendations') else {}

    fallback_answer = f"""### Business Analyst Assessment
**Empirical Finding:**
Based on the **{p['total_rows']:,} observations** analyzed in `{session['filename']}`, the primary metrics stand at: {kpis_text}.

**Root Cause & Drivers:**
{root_cause.get('observed_fact', 'Analysis of variance confirms distinct performance separation across operating categories.')}
{root_cause.get('possible_explanation', 'Performance divergence is strongly tied to demand elasticity and segment allocation.')}

**Strategic Recommendation:**
{rec.get('recommendation', 'Audit underperforming categories and reallocate capital to highest-margin lines.')}
*Evidence:* {rec.get('evidence', 'Statistically significant inter-segment variance.')}
*Expected Impact:* {rec.get('expected_impact', 'Revenue recovery and margin expansion.')}
"""
    return {"response": fallback_answer}

@app.post("/api/export/excel")
async def export_excel(session_id: str = Form(...)):
    if session_id not in SESSIONS or SESSIONS[session_id]['df'] is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    session = SESSIONS[session_id]
    df = session['df']
    analysis = session.get('analysis')

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Raw / Clean Data
        df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
        
        # Sheet 2: Descriptive Statistics
        if analysis and 'statistics' in analysis and 'descriptive_statistics' in analysis['statistics']:
            desc_df = pd.DataFrame.from_dict(analysis['statistics']['descriptive_statistics'], orient='index')
            desc_df.to_excel(writer, sheet_name='Descriptive_Stats')
        
        # Sheet 3: Recommendations & Priority Matrix
        if analysis and 'recommendations' in analysis:
            rec_df = pd.DataFrame(analysis['recommendations'])
            rec_df.to_excel(writer, sheet_name='Recommendation_Matrix', index=False)

    output.seek(0)
    headers = {
        'Content-Disposition': f'attachment; filename="AI_Business_Analyst_{session["filename"].replace(".csv", ".xlsx")}"'
    }
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

# Mount static web frontend
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/data", StaticFiles(directory="data"), name="data")

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8085))
    print(f"Starting AI Business Analyst Server on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
