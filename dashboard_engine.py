import os
import sys
import datetime
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, Reference, Series

def analyze_and_build_dashboard(input_file, output_file=None):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")
    
    if output_file is None:
        base_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(base_dir, f"{base_name}_Executive_AI_Dashboard.xlsx")

    # 1. Load Data
    if input_file.lower().endswith(('.xlsx', '.xlsm', '.xltx')):
        excel_file = pd.ExcelFile(input_file)
        # pick the largest sheet by rows or active sheet
        sheet_to_use = excel_file.sheet_names[0]
        max_rows = 0
        for s in excel_file.sheet_names:
            df_temp = pd.read_excel(excel_file, sheet_name=s, nrows=50)
            if len(df_temp.columns) > 1 and len(df_temp) > max_rows:
                max_rows = len(df_temp)
                sheet_to_use = s
        df = pd.read_excel(input_file, sheet_name=sheet_to_use)
    elif input_file.lower().endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        raise ValueError("Unsupported file format. Please provide .xlsx, .xls, or .csv")

    df = df.dropna(how='all')
    if len(df) < 2 or len(df.columns) < 2:
        raise ValueError("Dataset has insufficient rows or columns for statistical modeling.")

    # 2. Schema Classification
    date_cols = []
    num_cols = []
    cat_cols = []

    for col in df.columns:
        # Check date
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        else:
            # Try parsing date if string
            if df[col].dtype == object:
                sample = df[col].dropna().astype(str).head(15)
                # heuristic
                if any(k in col.lower() for k in ['date', 'time', 'period', 'month', 'year']):
                    try:
                        pd.to_datetime(sample, errors='raise')
                        date_cols.append(col)
                        continue
                    except:
                        pass
        
        # Check numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            # If unique values are very small (e.g. 0/1 or ID with 2 vals), can be cat
            if df[col].nunique() > 5 and not any(k in col.lower() for k in ['id', 'code', 'zip']):
                num_cols.append(col)
            else:
                cat_cols.append(col)
        elif df[col].dtype == object:
            cat_cols.append(col)

    # Fallback if no numeric
    if not num_cols:
        for col in df.columns:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > len(df) * 0.5:
                df[col] = converted
                num_cols.append(col)

    # 3. Deep Statistical & Dynamic KPI Extraction
    kpis = []
    insights = []
    recommendations = []

    total_records = len(df)
    kpis.append({
        "title": "TOTAL RECORD COUNT",
        "value": f"{total_records:,}",
        "subtitle": "Total Active Records",
        "color": "2563EB", # Blue
        "trend": "100% Ingested"
    })

    # Numeric Stats
    primary_num = num_cols[0] if num_cols else None
    secondary_num = num_cols[1] if len(num_cols) > 1 else None

    if primary_num:
        vals = df[primary_num].dropna()
        p_sum = vals.sum()
        p_mean = vals.mean()
        p_std = vals.std()
        p_median = vals.median()
        
        # Format
        fmt = "${:,.2f}" if any(k in primary_num.lower() for k in ['cost', 'price', 'rev', 'gmv', 'sales']) else "{:,.1f}"
        
        kpis.append({
            "title": f"TOTAL {primary_num.upper()[:18]}",
            "value": fmt.format(p_sum),
            "subtitle": f"Aggregated Total",
            "color": "0D9488", # Teal
            "trend": f"Median: {fmt.format(p_median)}"
        })

        kpis.append({
            "title": f"AVG {primary_num.upper()[:18]}",
            "value": fmt.format(p_mean),
            "subtitle": f"Std Dev (σ): {p_std:,.1f}",
            "color": "D97706", # Amber
            "trend": f"CV: {(p_std/p_mean if p_mean else 0):.1%}"
        })

        # Outlier Detection (Tukey's IQR method)
        q1 = vals.quantile(0.25)
        q3 = vals.quantile(0.75)
        iqr = q3 - q1
        outliers = vals[(vals < q1 - 1.5 * iqr) | (vals > q3 + 1.5 * iqr)]
        outlier_pct = len(outliers) / len(vals) if len(vals) > 0 else 0

        kpis.append({
            "title": "ANOMALY / OUTLIER COUNT",
            "value": f"{len(outliers):,}",
            "subtitle": f"{outlier_pct:.1%} of Total Records",
            "color": "EF4444" if len(outliers) > 0 else "10B981", # Red/Green
            "trend": "Bounds: ±1.5 IQR"
        })

    if secondary_num:
        vals2 = df[secondary_num].dropna()
        fmt2 = "${:,.2f}" if any(k in secondary_num.lower() for k in ['cost', 'price', 'rev', 'gmv', 'sales']) else "{:,.1f}"
        kpis.append({
            "title": f"TOTAL {secondary_num.upper()[:18]}",
            "value": fmt2.format(vals2.sum()),
            "subtitle": f"Mean: {fmt2.format(vals2.mean())}",
            "color": "7C3AED", # Violet
            "trend": f"Max: {fmt2.format(vals2.max())}"
        })

    # Categorical Analysis
    primary_cat = cat_cols[0] if cat_cols else None
    if primary_cat:
        cat_counts = df[primary_cat].value_counts()
        top_cat_name = cat_counts.index[0] if len(cat_counts) > 0 else "N/A"
        top_cat_share = (cat_counts.iloc[0] / total_records) if len(cat_counts) > 0 else 0
        
        kpis.append({
            "title": f"TOP {primary_cat.upper()[:16]}",
            "value": f"{top_cat_name[:16]}",
            "subtitle": f"{top_cat_share:.1%} Concentration Share",
            "color": "4F46E5", # Indigo
            "trend": f"{len(cat_counts)} Unique Groups"
        })

    # Completeness Rate KPI
    null_count = df.isnull().sum().sum()
    total_cells = df.size
    health_rate = 1.0 - (null_count / total_cells if total_cells else 0)
    kpis.append({
        "title": "DATA HEALTH SCORE",
        "value": f"{health_rate:.1%}",
        "subtitle": f"{null_count:,} Null Cells Detected",
        "color": "10B981", # Emerald
        "trend": "Audit Compliant" if health_rate > 0.95 else "Requires Cleaning"
    })

    # 4. Regression & Predictive Modeling
    regression_results = []
    
    if primary_num:
        # Check against Date or Index
        if date_cols:
            d_col = date_cols[0]
            df_temp = df[[d_col, primary_num]].dropna().copy()
            df_temp['date_parsed'] = pd.to_datetime(df_temp[d_col], errors='coerce')
            df_temp = df_temp.dropna().sort_values('date_parsed')
            if len(df_temp) > 5:
                # Group by period (daily or monthly)
                df_grouped = df_temp.groupby(df_temp['date_parsed'].dt.to_period('M'))[primary_num].sum().reset_index()
                if len(df_grouped) >= 3:
                    X = np.arange(len(df_grouped)).reshape(-1, 1)
                    y = df_grouped[primary_num].values
                    reg = LinearRegression().fit(X, y)
                    r2 = reg.score(X, y)
                    slope = reg.coef_[0]
                    # Forecast next 3 periods
                    X_future = np.arange(len(df_grouped), len(df_grouped) + 3).reshape(-1, 1)
                    y_pred = reg.predict(X_future)
                    
                    trend_dir = "Accelerating Growth" if slope > 0 else "Downward Contraction"
                    regression_results.append({
                        "name": f"Time-Series Trend ({primary_num} vs {d_col})",
                        "r2": r2,
                        "slope": slope,
                        "trajectory": trend_dir,
                        "forecast": [float(v) for v in y_pred]
                    })
                    insights.append(f"Regression model demonstrates {trend_dir} (R² = {r2:.3f}) with an average period delta of {slope:+,.2f}.")
                    recommendations.append(f"Plan resource capacity around next-period forecast: {y_pred[0]:,.1f} units based on historical trajectory.")

        # Numeric to Numeric Regression
        if secondary_num:
            df_pair = df[[secondary_num, primary_num]].dropna()
            if len(df_pair) > 10:
                X = df_pair[[secondary_num]].values
                y = df_pair[primary_num].values
                reg2 = LinearRegression().fit(X, y)
                r2_num = reg2.score(X, y)
                slope2 = reg2.coef_[0]
                corr = np.corrcoef(df_pair[secondary_num], df_pair[primary_num])[0, 1]
                
                regression_results.append({
                    "name": f"Predictive Correlation ({secondary_num} → {primary_num})",
                    "r2": r2_num,
                    "slope": slope2,
                    "trajectory": f"Correlation r = {corr:+.2f}",
                    "forecast": []
                })
                if abs(corr) >= 0.5:
                    insights.append(f"Statistically significant relationship identified between {secondary_num} and {primary_num} (r = {corr:.2f}, R² = {r2_num:.2f}).")
                    recommendations.append(f"Leverage {secondary_num} as an operational leading indicator to optimize {primary_num} variance.")

    # Additional Insights
    if primary_cat and top_cat_share > 0.40:
        insights.append(f"Concentration Risk: '{top_cat_name}' accounts for {top_cat_share:.1%} of overall activity across {primary_cat}.")
        recommendations.append(f"Diversify operational allocation to mitigate over-dependence on top segment '{top_cat_name}'.")

    if len(outliers) > 0 and len(outliers) / total_records > 0.03:
        insights.append(f"Statistical Anomaly Alert: {len(outliers)} data points exceed the 1.5×IQR threshold ({outlier_pct:.1%} of records).")
        recommendations.append(f"Execute root-cause audit on extreme values to prevent metric skewing in reporting.")

    if not insights:
        insights.append("Normal Gaussian distribution observed across key quantitative parameters.")
        recommendations.append("Maintain baseline monitoring intervals and scheduled reviews.")

    # 5. Build Formatted Excel Workbook with OpenPyXL
    wb = openpyxl.Workbook()
    # Sheet 1: Executive Dashboard
    ws_dash = wb.active
    ws_dash.title = "Executive_Dashboard"
    ws_dash.views.sheetView[0].showGridLines = False

    # Theme Colors
    DARK_NAVY = "0F172A" # #0F172A Slate-900
    SLATE_BAR = "1E293B" # #1E293B
    BG_LIGHT  = "F8FAFC"
    CARD_BG   = "FFFFFF"
    BORDER_CLR= "E2E8F0"
    MUTED_TXT = "64748B"

    # Fill background
    for row in range(1, 45):
        for col in range(1, 16):
            ws_dash.cell(row, col).fill = PatternFill(start_color=BG_LIGHT, end_color=BG_LIGHT, fill_type="solid")

    # Set Column widths
    ws_dash.column_dimensions['A'].width = 3
    for c_idx in range(2, 15):
        ws_dash.column_dimensions[get_column_letter(c_idx)].width = 17

    # Banner Header
    ws_dash.merge_cells("B2:N3")
    banner = ws_dash["B2"]
    banner.value = "   EXECUTIVE INTELLIGENCE & STATISTICAL DASHBOARD"
    banner.fill = PatternFill(start_color=DARK_NAVY, end_color=DARK_NAVY, fill_type="solid")
    banner.font = Font(name="Segoe UI", size=16, bold=True, color="FFFFFF")
    banner.alignment = Alignment(vertical="center", horizontal="left")

    ws_dash.merge_cells("B4:N4")
    sub_banner = ws_dash["B4"]
    sub_banner.value = f"   Dataset: {os.path.basename(input_file)}   |   Ingested Records: {total_records:,}   |   Analyzed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    sub_banner.fill = PatternFill(start_color=SLATE_BAR, end_color=SLATE_BAR, fill_type="solid")
    sub_banner.font = Font(name="Segoe UI", size=9, color="94A3B8")
    sub_banner.alignment = Alignment(vertical="center", horizontal="left")

    # Render Dynamic KPIs across rows 6 to 9 (Up to 7-8 cards side by side in pairs)
    thin_border = Border(
        left=Side(style='thin', color=BORDER_CLR),
        right=Side(style='thin', color=BORDER_CLR),
        top=Side(style='thin', color=BORDER_CLR),
        bottom=Side(style='thin', color=BORDER_CLR)
    )

    card_col_start = 2
    card_width = 2
    row_start = 6

    for i, kpi in enumerate(kpis):
        # Calculate cell coordinates
        c1 = card_col_start + (i % 6) * card_width
        r_offset = row_start if i < 6 else row_start + 4
        
        c1_let = get_column_letter(c1)
        c2_let = get_column_letter(c1 + card_width - 1)
        
        # Merge card block
        ws_dash.merge_cells(f"{c1_let}{r_offset}:{c2_let}{r_offset}")
        ws_dash.merge_cells(f"{c1_let}{r_offset+1}:{c2_let}{r_offset+1}")
        ws_dash.merge_cells(f"{c1_let}{r_offset+2}:{c2_let}{r_offset+2}")
        
        # Card Header
        t_cell = ws_dash[f"{c1_let}{r_offset}"]
        t_cell.value = f" {kpi['title']}"
        t_cell.font = Font(name="Segoe UI", size=8, bold=True, color=MUTED_TXT)
        t_cell.fill = PatternFill(start_color=CARD_BG, end_color=CARD_BG, fill_type="solid")
        
        # Big Value
        v_cell = ws_dash[f"{c1_let}{r_offset+1}"]
        v_cell.value = f" {kpi['value']}"
        v_cell.font = Font(name="Segoe UI", size=15, bold=True, color="0F172A")
        v_cell.fill = PatternFill(start_color=CARD_BG, end_color=CARD_BG, fill_type="solid")
        
        # Subtitle / Indicator
        s_cell = ws_dash[f"{c1_let}{r_offset+2}"]
        s_cell.value = f" {kpi['subtitle']}  •  {kpi['trend']}"
        s_cell.font = Font(name="Segoe UI", size=7.5, bold=True, color=kpi['color'])
        s_cell.fill = PatternFill(start_color=CARD_BG, end_color=CARD_BG, fill_type="solid")
        
        # Style border
        for r_b in range(r_offset, r_offset + 3):
            for c_b in range(c1, c1 + card_width):
                ws_dash.cell(r_b, c_b).border = thin_border
        
        # Accent left line
        ws_dash.cell(r_offset, c1).border = Border(left=Side(style='thick', color=kpi['color']), top=Side(style='thin', color=BORDER_CLR))
        ws_dash.cell(r_offset+1, c1).border = Border(left=Side(style='thick', color=kpi['color']))
        ws_dash.cell(r_offset+2, c1).border = Border(left=Side(style='thick', color=kpi['color']), bottom=Side(style='thin', color=BORDER_CLR))

    # Next Section: Executive Statistical Insights & Strategic Recommendations Box
    box_row = 10 if len(kpis) <= 6 else 14
    ws_dash.merge_cells(f"B{box_row}:G{box_row+6}")
    box_left = ws_dash[f"B{box_row}"]
    box_left.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    
    # Text inside Insights box
    txt_insights = "  KEY STATISTICAL FINDINGS & PREDICTIVE DRIVERS:\n"
    for ins in insights:
        txt_insights += f"  • {ins}\n"
    txt_insights += "\n  STRATEGIC RECOMMENDATIONS:\n"
    for rec in recommendations:
        txt_insights += f"  → {rec}\n"

    box_left.value = txt_insights
    box_left.font = Font(name="Segoe UI", size=8.5, color="1E293B")
    box_left.alignment = Alignment(vertical="top", horizontal="left", wrap_text=True)

    for r_b in range(box_row, box_row + 7):
        for c_b in range(2, 8):
            ws_dash.cell(r_b, c_b).border = thin_border
    ws_dash.cell(box_row, 2).border = Border(left=Side(style='thick', color="2563EB"), top=Side(style='thin', color=BORDER_CLR))

    # Regression Table on the Right of Insights Box
    ws_dash.merge_cells(f"H{box_row}:N{box_row}")
    r_hdr = ws_dash[f"H{box_row}"]
    r_hdr.value = "  REGRESSION & STATISTICAL MODELING SUMMARY"
    r_hdr.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    r_hdr.font = Font(name="Segoe UI", size=9, bold=True, color="FFFFFF")
    
    headers_reg = ["Model / Variable Pair", "Trajectory", "R² Score", "Slope (m)"]
    for idx_h, h_name in enumerate(headers_reg):
        cell_h = ws_dash.cell(box_row + 1, 8 + idx_h * 2 if idx_h < 2 else 11 + (idx_h - 2))
        cell_h.value = h_name
        cell_h.font = Font(name="Segoe UI", size=8, bold=True, color="64748B")
        cell_h.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    row_reg_curr = box_row + 2
    for reg_item in regression_results:
        ws_dash.cell(row_reg_curr, 8).value = reg_item['name']
        ws_dash.cell(row_reg_curr, 10).value = reg_item['trajectory']
        ws_dash.cell(row_reg_curr, 12).value = f"{reg_item['r2']:.3f}"
        ws_dash.cell(row_reg_curr, 13).value = f"{reg_item['slope']:+,.2f}"
        for col_i in range(8, 14):
            ws_dash.cell(row_reg_curr, col_i).font = Font(name="Segoe UI", size=8)
        row_reg_curr += 1

    # Sheet 2: Data Aggregations & Pivot Calculations
    ws_calc = wb.create_sheet(title="Aggregated_Metrics")
    
    # 1. Category aggregation
    if primary_cat and primary_num:
        cat_grp = df.groupby(primary_cat)[primary_num].agg(['sum', 'count']).reset_index().sort_values('sum', ascending=False).head(10)
        ws_calc.cell(1, 1).value = primary_cat
        ws_calc.cell(1, 2).value = f"Total {primary_num}"
        ws_calc.cell(1, 3).value = "Record Count"
        for r_i, row_val in cat_grp.iterrows():
            row_num = ws_calc.max_row + 1
            ws_calc.cell(row_num, 1).value = str(row_val[primary_cat])
            ws_calc.cell(row_num, 2).value = float(row_val['sum'])
            ws_calc.cell(row_num, 3).value = int(row_val['count'])

        # Add Horizontal Bar Chart to Dashboard
        chart_bar = BarChart()
        chart_bar.type = "bar" # horizontal
        chart_bar.style = 10
        chart_bar.title = f"Top {primary_cat} by {primary_num}"
        chart_bar.font = "Segoe UI"
        chart_bar.height = 10
        chart_bar.width = 18
        
        data_ref = Reference(ws_calc, min_col=2, min_row=1, max_row=len(cat_grp)+1)
        cats_ref = Reference(ws_calc, min_col=1, min_row=2, max_row=len(cat_grp)+1)
        chart_bar.add_data(data_ref, titles_from_data=True)
        chart_bar.set_categories(cats_ref)
        chart_bar.legend = None
        ws_dash.add_chart(chart_bar, f"B{box_row+8}")

    # 2. Time-Series aggregation
    if date_cols and primary_num:
        d_col = date_cols[0]
        df_ts = df[[d_col, primary_num]].dropna().copy()
        df_ts['period'] = pd.to_datetime(df_ts[d_col], errors='coerce').dt.strftime('%Y-%m')
        ts_grp = df_ts.groupby('period')[primary_num].sum().reset_index().sort_values('period').tail(15)
        
        start_c = 6
        ws_calc.cell(1, start_c).value = "Period"
        ws_calc.cell(1, start_c + 1).value = f"Sum {primary_num}"
        for _, row_val in ts_grp.iterrows():
            r_idx = ws_calc.cell(ws_calc.max_row + 1, start_c).row
            ws_calc.cell(r_idx, start_c).value = str(row_val['period'])
            ws_calc.cell(r_idx, start_c + 1).value = float(row_val[primary_num])
            
        chart_line = LineChart()
        chart_line.title = f"Timeline Velocity & Trend ({primary_num})"
        chart_line.style = 13
        chart_line.height = 10
        chart_line.width = 18
        data_ts_ref = Reference(ws_calc, min_col=start_c+1, min_row=1, max_row=len(ts_grp)+1)
        cats_ts_ref = Reference(ws_calc, min_col=start_c, min_row=2, max_row=len(ts_grp)+1)
        chart_line.add_data(data_ts_ref, titles_from_data=True)
        chart_line.set_categories(cats_ts_ref)
        chart_line.legend = None
        ws_dash.add_chart(chart_line, f"H{box_row+8}")

    # Sheet 3: Statistical Summary (Full Descriptive Statistics)
    ws_stats = wb.create_sheet(title="Statistical_Deep_Dive")
    ws_stats.views.sheetView[0].showGridLines = True
    
    desc_df = df[num_cols].describe().T.reset_index() if num_cols else pd.DataFrame()
    if not desc_df.empty:
        ws_stats.cell(1, 1).value = "Metric Name"
        headers_desc = list(desc_df.columns)
        for c_i, h in enumerate(headers_desc):
            ws_stats.cell(1, c_i + 1).value = str(h).title()
            ws_stats.cell(1, c_i + 1).font = Font(name="Segoe UI", bold=True, color="FFFFFF")
            ws_stats.cell(1, c_i + 1).fill = PatternFill(start_color=DARK_NAVY, end_color=DARK_NAVY, fill_type="solid")
            
        for r_i, r_val in desc_df.iterrows():
            for c_i, h in enumerate(headers_desc):
                c_cell = ws_stats.cell(r_i + 2, c_i + 1)
                val_raw = r_val[h]
                c_cell.value = float(val_raw) if isinstance(val_raw, (int, float, np.number)) else str(val_raw)
                c_cell.font = Font(name="Segoe UI", size=9)
                if isinstance(val_raw, (int, float, np.number)):
                    c_cell.number_format = "#,##0.00"

    # Sheet 4: Raw Ingested Data
    ws_raw = wb.create_sheet(title="Raw_Data")
    for c_i, col_name in enumerate(df.columns):
        ws_raw.cell(1, c_i + 1).value = str(col_name)
        ws_raw.cell(1, c_i + 1).font = Font(name="Segoe UI", bold=True, color="FFFFFF")
        ws_raw.cell(1, c_i + 1).fill = PatternFill(start_color=DARK_NAVY, end_color=DARK_NAVY, fill_type="solid")

    for r_i, row in enumerate(df.head(5000).itertuples(index=False)):
        for c_i, val in enumerate(row):
            cell = ws_raw.cell(r_i + 2, c_i + 1)
            if pd.isna(val):
                cell.value = ""
            elif isinstance(val, (int, float, np.number)):
                cell.value = float(val)
                cell.number_format = "#,##0.00" if isinstance(val, float) else "#,##0"
            else:
                cell.value = str(val)
            cell.font = Font(name="Segoe UI", size=9)

    # Auto-fit column widths
    for s in [ws_calc, ws_stats, ws_raw]:
        for col in s.columns:
            max_len = max(len(str(cell.value or '')) for cell in col[:50])
            col_letter = get_column_letter(col[0].column)
            s.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(output_file)
    return output_file

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        out = analyze_and_build_dashboard(target_file)
        print("SUCCESS:", out)
    else:
        print("Usage: python dashboard_engine.py <path_to_excel_or_csv>")
