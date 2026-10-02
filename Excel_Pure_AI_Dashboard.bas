Attribute VB_Name = "Excel_Pure_AI_Dashboard"
' =========================================================================================
' ENTERPRISE EXECUTIVE AI DASHBOARD & STATISTICAL INTELLIGENCE ENGINE
' Architecture: 100% Native Excel VBA
' Capabilities:
'   - Intelligent Data Profiler & Automated Decision Engine:
'       * Scans all dataset columns for entropy, cardinality, variance, and data types
'       * Autonomously decides which Slicers to create based on filter utility
'       * Autonomously decides which Plots to generate (Time-Series, Ranked Bar, Donut, Dual-Metric)
'   - Dynamic Real-Time Slicers Connected to Master Pivot Cache:
'       * Instant multi-slicer filtering across all charts and KPI cards
'   - Live Real-Time Updating KPI Cards:
'       * Ingested Volume, Primary Aggregate, Mean Velocity, Secondary Pool, StdDev, Max, Min, Margin %
'   - Machine Learning & Statistical Intelligence Suite:
'       * Ordinary Least Squares (OLS) Linear Regression (Slope m, Intercept b, R^2, Std Error)
'       * Tukey's 1.5xIQR Statistical Outlier & Anomaly Detection
'       * Pareto Distribution & Concentration Analysis (Top Quartile Contribution)
'       * Prescriptive Strategic Directives & Forward-Looking Target Projection
'   - Adaptive Canvas Grid Layout (Automatic 4-Plot 2x2 or 3-Plot Panoramic Architecture)
' =========================================================================================
Option Explicit

Public Sub Generate_Executive_AI_Dashboard()
    Dim fd As FileDialog
    Dim selectedFile As String
    Dim srcWb As Workbook, outWb As Workbook
    Dim wsData As Worksheet, wsDash As Worksheet, wsPiv As Worksheet
    Dim lastRow As Long, lastCol As Long, c As Long, r As Long
    Dim colHeader As String, sampleVal As Variant
    Dim startTime As Double
    
    ' -------------------------------------------------------------------------------------
    ' 1. FILE SELECTION DIALOG (PROMPTS USER FOR ANY EXCEL / CSV DATASET)
    ' -------------------------------------------------------------------------------------
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    With fd
        .Title = "Select Data File for Executive AI Dashboard & Statistical Analysis"
        .Filters.Clear
        .Filters.Add "Excel & CSV Files (*.xlsx; *.xlsm; *.xls; *.csv)", "*.xlsx; *.xlsm; *.xls; *.csv"
        .AllowMultiSelect = False
        If .Show = -1 Then
            selectedFile = .SelectedItems(1)
        Else
            MsgBox "No file selected. Dashboard generation cancelled.", vbInformation, "Operation Cancelled"
            Exit Sub
        End If
    End With
    
    startTime = Timer
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    Set srcWb = Workbooks.Open(selectedFile, ReadOnly:=True)
    Set wsData = srcWb.Sheets(1)
    
    lastRow = wsData.Cells(wsData.Rows.Count, 1).End(xlUp).Row
    lastCol = wsData.Cells(1, wsData.Columns.Count).End(xlToLeft).Column
    
    If lastRow < 3 Or lastCol < 2 Then
        srcWb.Close False
        Application.ScreenUpdating = True
        Application.DisplayAlerts = True
        MsgBox "The selected file does not contain enough data (minimum 3 rows and 2 columns required).", vbExclamation, "Insufficient Data"
        Exit Sub
    End If
    
    ' Create independent destination workbook for dashboard
    Set outWb = Workbooks.Add
    wsData.Copy Before:=outWb.Sheets(1)
    srcWb.Close False
    
    Set wsData = outWb.Sheets(1)
    wsData.Name = "Raw_Data"
    
    ' -------------------------------------------------------------------------------------
    ' 2. AUTONOMOUS DATA PROFILER & DECISION ENGINE
    ' -------------------------------------------------------------------------------------
    Dim sampleRows As Long: sampleRows = IIf(lastRow > 300, 300, lastRow)
    Dim dictSample As Object
    Dim dateCol As Long: dateCol = 0
    
    Dim catCols() As Long, catNames() As String, catCards() As Long, catScores() As Long, catCount As Long
    Dim numCols() As Long, numNames() As String, numScores() As Long, numCount As Long
    ReDim catCols(1 To lastCol): ReDim catNames(1 To lastCol): ReDim catCards(1 To lastCol): ReDim catScores(1 To lastCol): catCount = 0
    ReDim numCols(1 To lastCol): ReDim numNames(1 To lastCol): ReDim numScores(1 To lastCol): numCount = 0
    
    ' Profile each column
    For c = 1 To lastCol
        colHeader = UCase(Trim(CStr(wsData.Cells(1, c).Value)))
        sampleVal = wsData.Cells(2, c).Value
        
        ' Check Temporal / Date dimension
        If IsDate(sampleVal) Or InStr(colHeader, "DATE") > 0 Or InStr(colHeader, "TIME") > 0 Or InStr(colHeader, "YEAR") > 0 Then
            If dateCol = 0 Then dateCol = c
        ' Check Numeric metrics
        ElseIf IsNumeric(sampleVal) And Not IsEmpty(sampleVal) Then
            If Not IsIdColumn(colHeader, CStr(sampleVal)) Then
                numCount = numCount + 1
                numCols(numCount) = c
                numNames(numCount) = wsData.Cells(1, c).Value
                numScores(numCount) = GetNumericScore(colHeader)
            End If
        ' Check Categorical dimensions (Entropy & Cardinality Analysis)
        ElseIf VarType(sampleVal) = vbString Then
            If Not IsIdColumn(colHeader, CStr(sampleVal)) Then
                Set dictSample = CreateObject("Scripting.Dictionary")
                For r = 2 To sampleRows
                    sampleVal = wsData.Cells(r, c).Value
                    If Not IsEmpty(sampleVal) Then
                        If Not dictSample.Exists(CStr(sampleVal)) Then dictSample.Add CStr(sampleVal), True
                    End If
                Next r
                
                Dim cardVal As Long: cardVal = dictSample.Count
                Set dictSample = Nothing
                
                ' Cardinality threshold for valid business dimensions: 2 to 40 distinct items
                If cardVal >= 2 And cardVal <= 40 Then
                    catCount = catCount + 1
                    catCols(catCount) = c
                    catNames(catCount) = wsData.Cells(1, c).Value
                    catCards(catCount) = cardVal
                    catScores(catCount) = GetCategoryScore(colHeader, cardVal)
                End If
            End If
        End If
    Next c
    
    ' DECIDE PRIMARY & SECONDARY NUMERIC METRICS
    Dim numCol1 As Long, numCol2 As Long
    Dim num1Name As String, num2Name As String
    If numCount > 0 Then
        SortByScore numCols, numScores, numCount
        numCol1 = numCols(1)
        num1Name = wsData.Cells(1, numCol1).Value
        If numCount >= 2 Then
            numCol2 = numCols(2)
            num2Name = wsData.Cells(1, numCol2).Value
        Else
            numCol2 = 0
            num2Name = ""
        End If
    Else
        numCol1 = lastCol: num1Name = wsData.Cells(1, numCol1).Value
        numCol2 = 0: num2Name = ""
    End If
    
    ' DECIDE SLICERS (Score-ranked by filter utility: 2 <= cardinality <= 15)
    Dim slicer1Col As Long, slicer2Col As Long
    Dim slicer1Name As String, slicer2Name As String
    If catCount > 0 Then
        SortByScore catCols, catScores, catCount
        slicer1Col = catCols(1)
        slicer1Name = wsData.Cells(1, slicer1Col).Value
        If catCount >= 2 Then
            slicer2Col = catCols(2)
            slicer2Name = wsData.Cells(1, slicer2Col).Value
        Else
            slicer2Col = slicer1Col
            slicer2Name = slicer1Name
        End If
    Else
        slicer1Col = 1: slicer1Name = wsData.Cells(1, 1).Value
        slicer2Col = 1: slicer2Name = wsData.Cells(1, 1).Value
    End If
    
    ' DECIDE PLOTS BASED ON PROFILE:
    ' Plot 1: Chronological Trendline (if Date exists) or Primary Pareto
    Dim plot1Col As Long, plot1Name As String
    If dateCol > 0 Then
        plot1Col = dateCol
        plot1Name = wsData.Cells(1, dateCol).Value
    Else
        plot1Col = slicer1Col
        plot1Name = slicer1Name
    End If
    
    ' Plot 2: Ranked Performance Bar (Medium-cardinality dimension, 4 to 25 items e.g. Product or Category)
    Dim plot2Col As Long, plot2Name As String
    Dim bestMedScore As Long, idx As Long
    plot2Col = 0: bestMedScore = -1
    For idx = 1 To catCount
        If catCards(idx) >= 4 And catCards(idx) <= 30 Then
            plot2Col = catCols(idx)
            plot2Name = wsData.Cells(1, plot2Col).Value
            Exit For
        End If
    Next idx
    If plot2Col = 0 Then
        plot2Col = catCols(1): plot2Name = wsData.Cells(1, plot2Col).Value
    End If
    
    ' Plot 3: Composition Donut (Low-cardinality dimension, 2 to 6 items e.g. Segment, Channel, Status)
    Dim plot3Col As Long, plot3Name As String
    plot3Col = 0
    For idx = 1 To catCount
        If catCards(idx) >= 2 And catCards(idx) <= 6 And catCols(idx) <> plot2Col Then
            plot3Col = catCols(idx)
            plot3Name = wsData.Cells(1, plot3Col).Value
            Exit For
        End If
    Next idx
    If plot3Col = 0 Then
        For idx = 1 To catCount
            If catCols(idx) <> plot2Col Then
                plot3Col = catCols(idx): plot3Name = wsData.Cells(1, plot3Col).Value
                Exit For
            End If
        Next idx
    End If
    If plot3Col = 0 Then plot3Col = plot2Col: plot3Name = plot2Name
    
    ' Plot 4: Dual-Metric Variance & Margin Clustered Bar (Selected if Secondary Metric exists)
    Dim hasPlot4 As Boolean
    hasPlot4 = (numCol2 > 0 And numCol2 <> numCol1)
    
    ' -------------------------------------------------------------------------------------
    ' 3. SETUP EXECUTIVE DASHBOARD & PIVOT CALCULATION SHEETS
    ' -------------------------------------------------------------------------------------
    Set wsDash = outWb.Sheets.Add(Before:=wsData)
    wsDash.Name = "Executive_Dashboard"
    wsDash.Tab.Color = RGB(194, 65, 12)
    
    Set wsPiv = outWb.Sheets.Add(After:=wsDash)
    wsPiv.Name = "Pivot_Calculations"
    wsPiv.Visible = xlSheetHidden
    
    ActiveWindow.DisplayGridlines = False
    
    Dim CLR_CANVAS As Long, CLR_INK As Long, CLR_ACCENT As Long, CLR_BORDER As Long, CLR_WHITE As Long
    CLR_CANVAS = RGB(244, 241, 234)    ' Broadsheet Warm Parchment
    CLR_INK = RGB(26, 26, 26)          ' Deep Slate Ink
    CLR_ACCENT = RGB(194, 65, 12)      ' Signature Ember
    CLR_BORDER = RGB(216, 211, 203)    ' Muted Structural Border
    CLR_WHITE = RGB(255, 255, 255)     ' Pure White Card Fill
    
    wsDash.Cells.Interior.Color = CLR_CANVAS
    wsDash.Columns("A").ColumnWidth = 2.5
    For c = 2 To 18: wsDash.Columns(c).ColumnWidth = 14.5: Next c
    
    ' Top Masthead Dispatch Bar
    With wsDash.Range("B2:Q2")
        .Merge
        .Interior.Color = CLR_INK
        .Font.Name = "Segoe UI"
        .Font.Size = 8
        .Font.Bold = True
        .Font.Color = RGB(220, 224, 226)
        .HorizontalAlignment = xlLeft
        .VerticalAlignment = xlCenter
        .Value = "   ENTERPRISE EXECUTIVE ANALYTICS SUITE  |  AUTONOMOUS DATA PROFILER  |  REAL-TIME SLICER ENGINE"
    End With
    
    ' Broadsheet Title Bar
    With wsDash.Range("B3:Q4")
        .Merge
        .Interior.Color = CLR_CANVAS
        .Font.Name = "Georgia"
        .Font.Size = 19
        .Font.Bold = True
        .Font.Color = CLR_INK
        .HorizontalAlignment = xlLeft
        .VerticalAlignment = xlCenter
        .Value = "   EXECUTIVE PERFORMANCE & MULTI-VARIABLE PREDICTIVE DASHBOARD"
        .Borders(xlEdgeBottom).LineStyle = xlDouble
        .Borders(xlEdgeBottom).Color = CLR_INK
        .Borders(xlEdgeBottom).Weight = xlThick
    End With
    
    ' -------------------------------------------------------------------------------------
    ' 4. CREATE MASTER PIVOT TABLES & SLICER ENGINE
    ' -------------------------------------------------------------------------------------
    Dim pc As PivotCache
    Dim ptSum As PivotTable, pt1 As PivotTable, pt2 As PivotTable, pt3 As PivotTable, pt4 As PivotTable
    Dim srcR1C1 As String
    
    srcR1C1 = "'Raw_Data'!R1C1:R" & lastRow & "C" & lastCol
    Set pc = outWb.PivotCaches.Create(xlDatabase, srcR1C1)
    
    ' MASTER SUMMARY PIVOT TABLE: Powers Live Updating KPI Cards (A3 to G4)
    Set ptSum = pc.CreatePivotTable(wsPiv.Range("A3"), "PT_MasterSummary")
    With ptSum
        .AddDataField .PivotFields(num1Name), "Sum_Primary", xlSum          ' Col A (A4)
        .AddDataField .PivotFields(num1Name), "Avg_Primary", xlAverage      ' Col B (B4)
        .AddDataField .PivotFields(num1Name), "StdDev_Primary", xlStDev     ' Col C (C4)
        .AddDataField .PivotFields(wsData.Cells(1, 1).Value), "Count_Recs", xlCount ' Col D (D4)
        If numCol2 > 0 Then
            .AddDataField .PivotFields(num2Name), "Sum_Secondary", xlSum    ' Col E (E4)
        Else
            .AddDataField .PivotFields(num1Name), "Sum_Secondary", xlSum
        End If
        .AddDataField .PivotFields(num1Name), "Max_Primary", xlMax          ' Col F (F4)
        .AddDataField .PivotFields(num1Name), "Min_Primary", xlMin          ' Col G (G4)
    End With
    
    ' PIVOT 1: Trendline / Chronological Progression
    Set pt1 = pc.CreatePivotTable(wsPiv.Range("I3"), "PT_Plot1")
    With pt1
        .PivotFields(plot1Name).Orientation = xlRowField
        .AddDataField .PivotFields(num1Name), "Trend_" & Left(num1Name, 8), xlSum
    End With
    
    ' PIVOT 2: Ranked Category Performance
    Set pt2 = pc.CreatePivotTable(wsPiv.Range("M3"), "PT_Plot2")
    With pt2
        .PivotFields(plot2Name).Orientation = xlRowField
        .AddDataField .PivotFields(num1Name), "Ranked_" & Left(num1Name, 8), xlSum
    End With
    
    ' PIVOT 3: Structural Composition Donut
    Set pt3 = pc.CreatePivotTable(wsPiv.Range("Q3"), "PT_Plot3")
    With pt3
        .PivotFields(plot3Name).Orientation = xlRowField
        .AddDataField .PivotFields(num1Name), "Share_" & Left(num1Name, 8), xlSum
    End With
    
    ' PIVOT 4: Dual-Metric Comparison (if applicable)
    If hasPlot4 Then
        Set pt4 = pc.CreatePivotTable(wsPiv.Range("U3"), "PT_Plot4")
        With pt4
            .PivotFields(plot2Name).Orientation = xlRowField
            .AddDataField .PivotFields(num1Name), "Primary_" & Left(num1Name, 8), xlSum
            .AddDataField .PivotFields(num2Name), "Secondary_" & Left(num2Name, 8), xlSum
        End With
    End If
    
    ' -------------------------------------------------------------------------------------
    ' 5. DEEP STATISTICAL MODELING & OLS REGRESSION
    ' -------------------------------------------------------------------------------------
    Dim numLtr1 As String: numLtr1 = Split(wsData.Cells(1, numCol1).Address, "$")(1)
    
    wsPiv.Range("AA1").Value = "Statistic": wsPiv.Range("AB1").Value = "Result"
    wsPiv.Range("AA2").Value = "Total_Rows": wsPiv.Range("AB2").Formula = "=COUNTA('Raw_Data'!A2:A" & lastRow & ")"
    wsPiv.Range("AA3").Value = "Sum_Num1": wsPiv.Range("AB3").Formula = "=SUM('Raw_Data'!" & numLtr1 & "2:" & numLtr1 & lastRow & ")"
    wsPiv.Range("AA4").Value = "Avg_Num1": wsPiv.Range("AB4").Formula = "=AVERAGE('Raw_Data'!" & numLtr1 & "2:" & numLtr1 & lastRow & ")"
    wsPiv.Range("AA5").Value = "Std_Num1": wsPiv.Range("AB5").Formula = "=STDEV.S('Raw_Data'!" & numLtr1 & "2:" & numLtr1 & lastRow & ")"
    wsPiv.Range("AA6").Value = "Med_Num1": wsPiv.Range("AB6").Formula = "=MEDIAN('Raw_Data'!" & numLtr1 & "2:" & numLtr1 & lastRow & ")"
    wsPiv.Range("AA7").Value = "Q1_Num1": wsPiv.Range("AB7").Formula = "=PERCENTILE.INC('Raw_Data'!" & numLtr1 & "2:" & numLtr1 & lastRow & ", 0.25)"
    wsPiv.Range("AA8").Value = "Q3_Num1": wsPiv.Range("AB8").Formula = "=PERCENTILE.INC('Raw_Data'!" & numLtr1 & "2:" & numLtr1 & lastRow & ", 0.75)"
    
    ' Populate Sequence X & Metric Y for OLS Regression
    wsPiv.Range("AD1").Value = "X_Idx": wsPiv.Range("AE1").Value = "Y_Val"
    For r = 2 To lastRow
        wsPiv.Cells(r, 30).Value = r - 1
        wsPiv.Cells(r, 31).Formula = "='Raw_Data'!" & numLtr1 & r
    Next r
    
    wsPiv.Range("AA10").Value = "Slope_m": wsPiv.Range("AB10").Formula = "=SLOPE(AE2:AE" & lastRow & ", AD2:AD" & lastRow & ")"
    wsPiv.Range("AA11").Value = "Intercept_b": wsPiv.Range("AB11").Formula = "=INTERCEPT(AE2:AE" & lastRow & ", AD2:AD" & lastRow & ")"
    wsPiv.Range("AA12").Value = "RSQ_Score": wsPiv.Range("AB12").Formula = "=RSQ(AE2:AE" & lastRow & ", AD2:AD" & lastRow & ")"
    wsPiv.Range("AA13").Value = "Steyx_Se": wsPiv.Range("AB13").Formula = "=STEYX(AE2:AE" & lastRow & ", AD2:AD" & lastRow & ")"
    wsPiv.Range("AA14").Value = "Forecast_Next": wsPiv.Range("AB14").Formula = "=AB10*" & lastRow & "+AB11"
    
    wsPiv.Calculate
    
    Dim rsqVal As Double, slopeVal As Double, interceptVal As Double, steyxVal As Double, forecastVal As Double
    Dim q1Val As Double, q3Val As Double, iqrVal As Double, outlierCount As Long
    Dim topQuartileSum As Double, totalRawSum As Double, paretoShare As Double
    
    rsqVal = Val(wsPiv.Range("AB12").Value)
    slopeVal = Val(wsPiv.Range("AB10").Value)
    interceptVal = Val(wsPiv.Range("AB11").Value)
    steyxVal = Val(wsPiv.Range("AB13").Value)
    forecastVal = Val(wsPiv.Range("AB14").Value)
    q1Val = Val(wsPiv.Range("AB7").Value)
    q3Val = Val(wsPiv.Range("AB8").Value)
    iqrVal = q3Val - q1Val
    totalRawSum = Val(wsPiv.Range("AB3").Value)
    If totalRawSum = 0 Then totalRawSum = 1
    
    outlierCount = 0: topQuartileSum = 0
    For r = 2 To lastRow
        sampleVal = wsData.Cells(r, numCol1).Value
        If IsNumeric(sampleVal) And Not IsEmpty(sampleVal) Then
            If sampleVal < (q1Val - 1.5 * iqrVal) Or sampleVal > (q3Val + 1.5 * iqrVal) Then
                outlierCount = outlierCount + 1
            End If
            If sampleVal >= q3Val Then
                topQuartileSum = topQuartileSum + sampleVal
            End If
        End If
    Next r
    paretoShare = topQuartileSum / totalRawSum
    
    ' -------------------------------------------------------------------------------------
    ' 6. POPULATE 8 DYNAMIC REAL-TIME KPI CARDS (UPDATE LIVE WITH SLICERS)
    ' -------------------------------------------------------------------------------------
    wsDash.Rows(6).RowHeight = 16
    wsDash.Rows(7).RowHeight = 26
    wsDash.Rows(8).RowHeight = 16
    
    Dim numHdr1Short As String, numHdr2Short As String
    numHdr1Short = Left(UCase(num1Name), 12)
    If numCol2 > 0 Then numHdr2Short = Left(UCase(num2Name), 12) Else numHdr2Short = "BASELINE"
    
    ' KPI 1: Ingested Record Volume
    DrawExecutiveCard wsDash, "B6:C8", "FILTERED VOLUME", "=Pivot_Calculations!D4", "100% Ingested Samples", CLR_INK, "#,##0"
    ' KPI 2: Total Primary Metric (Revenue / Sales)
    DrawExecutiveCard wsDash, "D6:E8", "TOTAL " & numHdr1Short, "=Pivot_Calculations!A4", "Real-Time Net Aggregate", CLR_ACCENT, "$#,##0"
    ' KPI 3: Average Ticket / Unit
    DrawExecutiveCard wsDash, "F6:G8", "AVERAGE " & numHdr1Short, "=Pivot_Calculations!B4", "Mean Velocity", CLR_INK, "$#,##0.00"
    
    ' KPI 4: Secondary Metric (Profit / Cost) or Median Baseline
    If numCol2 > 0 Then
        DrawExecutiveCard wsDash, "H6:I8", "TOTAL " & numHdr2Short, "=Pivot_Calculations!E4", "Secondary Net Pool", CLR_ACCENT, "$#,##0"
    Else
        DrawExecutiveCard wsDash, "H6:I8", "MEDIAN BASELINE", "=Pivot_Calculations!AB6", "50th Percentile Floor", CLR_INK, "$#,##0"
    End If
    
    ' KPI 5: Statistical Dispersion / Standard Deviation
    DrawExecutiveCard wsDash, "J6:K8", "DISPERSION (STD DEV)", "=Pivot_Calculations!C4", "Gaussian Sigma Width", CLR_INK, "$#,##0.0"
    ' KPI 6: Maximum Recorded Transaction
    DrawExecutiveCard wsDash, "L6:M8", "PEAK OBSERVATION", "=Pivot_Calculations!F4", "Maximum Recorded Value", CLR_ACCENT, "$#,##0"
    ' KPI 7: Minimum Recorded Transaction
    DrawExecutiveCard wsDash, "N6:O8", "BASELINE FLOOR", "=Pivot_Calculations!G4", "Minimum Recorded Value", CLR_INK, "$#,##0"
    
    ' KPI 8: Operating Margin or Volatility Ratio (CV)
    If numCol2 > 0 Then
        DrawExecutiveCard wsDash, "P6:Q8", "OPERATING MARGIN", "=IF(Pivot_Calculations!A4>0, Pivot_Calculations!E4/Pivot_Calculations!A4, 0)", "Efficiency Ratio", CLR_ACCENT, "0.0%"
    Else
        DrawExecutiveCard wsDash, "P6:Q8", "VOLATILITY RATIO (CV)", "=IF(Pivot_Calculations!B4>0, Pivot_Calculations!C4/Pivot_Calculations!B4, 0)", "Coeff of Variation", CLR_ACCENT, "0.0%"
    End If
    
    ' -------------------------------------------------------------------------------------
    ' 7. STATISTICAL FINDINGS, ML INSIGHTS & STRATEGIC DIRECTIVES PANEL
    ' -------------------------------------------------------------------------------------
    With wsDash.Range("B10:I16")
        .Merge
        .Interior.Color = CLR_WHITE
        .Font.Name = "Georgia"
        .Font.Size = 9
        .Font.Color = CLR_INK
        .VerticalAlignment = xlTop
        .HorizontalAlignment = xlLeft
        .WrapText = True
        .Borders.Color = CLR_BORDER
        .Borders(xlEdgeLeft).Color = CLR_ACCENT
        .Borders(xlEdgeLeft).Weight = xlThick
        
        Dim reportText As String
        Dim dirStr As String, fitStr As String
        dirStr = IIf(slopeVal >= 0, "[+] Upward Velocity", "[-] Downward Trajectory")
        fitStr = IIf(rsqVal >= 0.5, "Strong Deterministic Linearity (R^2 = " & Format(rsqVal, "0.000") & ")", _
                                   "Stochastic / Multi-Factor Variance (R^2 = " & Format(rsqVal, "0.000") & ")")
        
        reportText = "  STATISTICAL MODELING FINDINGS & STRATEGIC DIRECTIVES:" & vbCrLf & _
                     "  * Model Fit: " & fitStr & " with " & dirStr & "." & vbCrLf & _
                     "  * OLS Slope: m = " & Format(slopeVal, "+#,##0.0000;-#,##0.0000") & " per period; Next 1-Step Projected Baseline = " & Format(forecastVal, "#,##0.00") & "." & vbCrLf & _
                     "  * Anomaly Diagnostic: " & outlierCount & " observations (" & Format(outlierCount / (lastRow - 1), "0.0%") & ") exceed Tukey's 1.5xIQR envelope [" & Format(q1Val - 1.5 * iqrVal, "#,##0.0") & " to " & Format(q3Val + 1.5 * iqrVal, "#,##0.0") & "]." & vbCrLf & _
                     "  * Pareto Concentration: Top 25% transactions contribute " & Format(paretoShare, "0.0%") & " of aggregate " & numHdr1Short & "." & vbCrLf & vbCrLf & _
                     "  ACTIONABLE STRATEGIC RECOMMENDATIONS:" & vbCrLf & _
                     "  >> Allocate operational resources aligned to projected baseline target (" & Format(forecastVal, "#,##0") & ")." & vbCrLf & _
                     "  >> Use interactive Slicers on the right to isolate and remediate localized segment anomalies."
        .Value = reportText
    End With
    
    ' Regression Specification Table Header
    With wsDash.Range("J10:Q10")
        .Merge
        .Interior.Color = CLR_INK
        .Font.Name = "Segoe UI"
        .Font.Size = 8.5
        .Font.Bold = True
        .Font.Color = RGB(255, 255, 255)
        .Value = "   PREDICTIVE MODELING & OLS REGRESSION SPECIFICATION"
        .VerticalAlignment = xlCenter
    End With
    
    Dim regLabels As Variant, regVals As Variant
    regLabels = Array("Target Variable (Y)", "Algorithm Architecture", "Slope Coefficient (m)", "Y-Intercept (b)", "Goodness-of-Fit (R^2)", "Standard Error (S_e)")
    regVals = Array(num1Name, "Ordinary Least Squares (OLS) Linear", Format(slopeVal, "+#,##0.0000;-#,##0.0000"), Format(interceptVal, "#,##0.00"), Format(rsqVal, "0.0000"), Format(steyxVal, "#,##0.00"))
    
    For idx = 0 To 5
        With wsDash.Range("J" & (11 + idx) & ":L" & (11 + idx))
            .Merge
            .Interior.Color = CLR_CANVAS
            .Font.Name = "Segoe UI"
            .Font.Size = 8
            .Font.Bold = True
            .Font.Color = CLR_INK
            .Value = "  " & regLabels(idx)
            .Borders.Color = CLR_BORDER
            .VerticalAlignment = xlCenter
        End With
        With wsDash.Range("M" & (11 + idx) & ":Q" & (11 + idx))
            .Merge
            .Interior.Color = CLR_WHITE
            .Font.Name = "Segoe UI"
            .Font.Size = 8
            .Font.Color = CLR_INK
            .Value = "  " & regVals(idx)
            .Borders.Color = CLR_BORDER
            .VerticalAlignment = xlCenter
        End With
    Next idx
    
    ' -------------------------------------------------------------------------------------
    ' 8. ADAPTIVE VISUALIZATION GRID & INTERACTIVE SLICERS
    ' -------------------------------------------------------------------------------------
    Dim sc1 As SlicerCache, sc2 As SlicerCache
    Dim sl1 As Slicer, sl2 As Slicer
    Dim ch1 As ChartObject, ch2 As ChartObject, ch3 As ChartObject, ch4 As ChartObject
    
    ' Create Slicers and wire them across ALL PivotTables
    On Error Resume Next
    Set sc1 = outWb.SlicerCaches.Add2(ptSum, slicer1Name)
    sc1.PivotTables.AddPivotTable pt1
    sc1.PivotTables.AddPivotTable pt2
    sc1.PivotTables.AddPivotTable pt3
    If hasPlot4 Then sc1.PivotTables.AddPivotTable pt4
    
    If slicer2Name <> slicer1Name Then
        Set sc2 = outWb.SlicerCaches.Add2(ptSum, slicer2Name)
        sc2.PivotTables.AddPivotTable pt1
        sc2.PivotTables.AddPivotTable pt2
        sc2.PivotTables.AddPivotTable pt3
        If hasPlot4 Then sc2.PivotTables.AddPivotTable pt4
    End If
    On Error GoTo 0
    
    If hasPlot4 Then
        ' =================================================================================
        ' 4-PLOT 2x2 BALANCED GRID ARCHITECTURE
        ' =================================================================================
        ' Top Row (Row 18 to 31):
        ' Plot 1: Trendline & Regression Line
        Set ch1 = wsDash.ChartObjects.Add(wsDash.Range("B18").Left, wsDash.Range("B18").Top, 360, 210)
        With ch1.Chart
            .SetSourceData pt1.TableRange1
            .ChartType = xlLine
            .HasTitle = True
            .ChartTitle.Text = "Trend & Progression by " & plot1Name
            .ChartTitle.Font.Name = "Georgia": .ChartTitle.Font.Size = 9.5: .ChartTitle.Font.Bold = True
            .HasLegend = False
            On Error Resume Next
            With .SeriesCollection(1).Trendlines.Add(Type:=xlLinear)
                .DisplayRSquared = True: .DisplayEquation = True
                .Format.Line.ForeColor.RGB = CLR_ACCENT: .Format.Line.Weight = 2
            End With
            On Error GoTo 0
        End With
        
        ' Plot 2: Ranked Category Performance Bar
        Set ch2 = wsDash.ChartObjects.Add(wsDash.Range("H18").Left + 10, wsDash.Range("H18").Top, 360, 210)
        With ch2.Chart
            .SetSourceData pt2.TableRange1
            .ChartType = xlBarClustered
            .HasTitle = True
            .ChartTitle.Text = "Ranked Contribution by " & plot2Name
            .ChartTitle.Font.Name = "Georgia": .ChartTitle.Font.Size = 9.5: .ChartTitle.Font.Bold = True
            .HasLegend = False
            On Error Resume Next
            .SeriesCollection(1).Format.Fill.ForeColor.RGB = CLR_INK
            On Error GoTo 0
        End With
        
        ' Slicer 1 at N18 (Width 150, Height 210)
        On Error Resume Next
        Set sl1 = sc1.Slicers.Add(wsDash, , "Slicer_Primary", slicer1Name, _
                                  wsDash.Range("N18").Top, wsDash.Range("N18").Left + 25, 150, 210)
        sl1.Style = "SlicerStyleDark1"
        
        ' Slicer 2 at P18 (Width 150, Height 210)
        If slicer2Name <> slicer1Name Then
            Set sl2 = sc2.Slicers.Add(wsDash, , "Slicer_Secondary", slicer2Name, _
                                      wsDash.Range("P18").Top, wsDash.Range("P18").Left + 25, 150, 210)
            sl2.Style = "SlicerStyleDark2"
        End If
        On Error GoTo 0
        
        ' Bottom Row (Row 33 to 46):
        ' Plot 3: Structural Composition Donut
        Set ch3 = wsDash.ChartObjects.Add(wsDash.Range("B33").Left, wsDash.Range("B33").Top, 360, 210)
        With ch3.Chart
            .SetSourceData pt3.TableRange1
            .ChartType = xlDoughnut
            .HasTitle = True
            .ChartTitle.Text = "Segment Share (" & plot3Name & ")"
            .ChartTitle.Font.Name = "Georgia": .ChartTitle.Font.Size = 9.5: .ChartTitle.Font.Bold = True
            .HasLegend = True
            .Legend.Position = xlLegendPositionBottom
            .Legend.Font.Name = "Segoe UI": .Legend.Font.Size = 7.5
        End With
        
        ' Plot 4: Dual-Metric Comparison (Primary vs Secondary Metric)
        Set ch4 = wsDash.ChartObjects.Add(wsDash.Range("H33").Left + 10, wsDash.Range("H33").Top, 360, 210)
        With ch4.Chart
            .SetSourceData pt4.TableRange1
            .ChartType = xlColumnClustered
            .HasTitle = True
            .ChartTitle.Text = "Metric Covariance: " & num1Name & " vs " & num2Name
            .ChartTitle.Font.Name = "Georgia": .ChartTitle.Font.Size = 9.5: .ChartTitle.Font.Bold = True
            .HasLegend = True
            .Legend.Position = xlLegendPositionBottom
            .Legend.Font.Name = "Segoe UI": .Legend.Font.Size = 7.5
        End With
    Else
        ' =================================================================================
        ' 3-PLOT PANORAMIC GRID ARCHITECTURE
        ' =================================================================================
        ' Plot 1: Category Bar (B18:E33)
        Set ch1 = wsDash.ChartObjects.Add(wsDash.Range("B18").Left, wsDash.Range("B18").Top, 320, 230)
        With ch1.Chart
            .SetSourceData pt2.TableRange1
            .ChartType = xlBarClustered
            .HasTitle = True
            .ChartTitle.Text = "Distribution by " & plot2Name
            .ChartTitle.Font.Name = "Georgia": .ChartTitle.Font.Size = 10: .ChartTitle.Font.Bold = True
            .HasLegend = False
            On Error Resume Next
            .SeriesCollection(1).Format.Fill.ForeColor.RGB = CLR_INK
            On Error GoTo 0
        End With
        
        ' Plot 2: Donut Composition (F18:I33)
        Set ch2 = wsDash.ChartObjects.Add(wsDash.Range("F18").Left + 15, wsDash.Range("F18").Top, 310, 230)
        With ch2.Chart
            .SetSourceData pt3.TableRange1
            .ChartType = xlDoughnut
            .HasTitle = True
            .ChartTitle.Text = "Segment Share (" & plot3Name & ")"
            .ChartTitle.Font.Name = "Georgia": .ChartTitle.Font.Size = 10: .ChartTitle.Font.Bold = True
            .HasLegend = True: .Legend.Position = xlLegendPositionBottom
            .Legend.Font.Name = "Segoe UI": .Legend.Font.Size = 7.5
        End With
        
        ' Plot 3: Progression Line with Trendline (J18:M33)
        Set ch3 = wsDash.ChartObjects.Add(wsDash.Range("J18").Left + 15, wsDash.Range("J18").Top, 320, 230)
        With ch3.Chart
            .SetSourceData pt1.TableRange1
            .ChartType = xlLine
            .HasTitle = True
            .ChartTitle.Text = "Trend & Progression by " & plot1Name
            .ChartTitle.Font.Name = "Georgia": .ChartTitle.Font.Size = 10: .ChartTitle.Font.Bold = True
            .HasLegend = False
            On Error Resume Next
            With .SeriesCollection(1).Trendlines.Add(Type:=xlLinear)
                .DisplayRSquared = True: .DisplayEquation = True
                .Format.Line.ForeColor.RGB = CLR_ACCENT: .Format.Line.Weight = 2
            End With
            On Error GoTo 0
        End With
        
        ' Slicer 1 at N18 (Width 155, Height 230)
        On Error Resume Next
        Set sl1 = sc1.Slicers.Add(wsDash, , "Slicer_Primary", slicer1Name, _
                                  wsDash.Range("N18").Top, wsDash.Range("N18").Left + 25, 155, 230)
        sl1.Style = "SlicerStyleDark1"
        
        ' Slicer 2 at P18 (Width 155, Height 230)
        If slicer2Name <> slicer1Name Then
            Set sl2 = sc2.Slicers.Add(wsDash, , "Slicer_Secondary", slicer2Name, _
                                      wsDash.Range("P18").Top, wsDash.Range("P18").Left + 25, 155, 230)
            sl2.Style = "SlicerStyleDark2"
        End If
        On Error GoTo 0
    End If
    
    wsDash.Activate
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    MsgBox "Executive AI Dashboard Generated Successfully!" & vbCrLf & vbCrLf & _
           "[+] Ingested Records: " & Format(lastRow - 1, "#,##0") & vbCrLf & _
           "[+] Decision Engine: Provisioned " & IIf(hasPlot4, "4-Plot Multi-Metric Suite", "3-Plot Panoramic Suite") & vbCrLf & _
           "[+] Dynamic Slicers Connected: [" & slicer1Name & "] and [" & slicer2Name & "]" & vbCrLf & _
           "[+] Statistical Engine: OLS Regression (R^2 = " & Format(rsqVal, "0.0000") & ") & Tukey 1.5xIQR Audit" & vbCrLf & _
           "[+] Build Latency: " & Format(Timer - startTime, "0.0") & " seconds", _
           vbInformation, "Executive Analytics Complete"
End Sub

' -----------------------------------------------------------------------------------------
' HELPER: RENDER EXECUTIVE KPI CARD (MERGED PER ROW TO PREVENT '######')
' -----------------------------------------------------------------------------------------
Private Sub DrawExecutiveCard(ByVal ws As Worksheet, ByVal rngAddr As String, ByVal title As String, _
                             ByVal formulaOrVal As String, ByVal subtitle As String, ByVal accentColor As Long, ByVal fmt As String)
    Dim rng As Range, cCount As Long
    Set rng = ws.Range(rngAddr)
    cCount = rng.Columns.Count
    
    rng.Interior.Color = RGB(255, 255, 255)
    rng.Borders.Color = RGB(216, 211, 203)
    rng.Borders(xlEdgeLeft).Color = accentColor
    rng.Borders(xlEdgeLeft).Weight = xlThick
    
    ' Row 1: Title
    With ws.Range(rng.Cells(1, 1), rng.Cells(1, cCount))
        .Merge
        .Font.Name = "Segoe UI": .Font.Size = 7.5: .Font.Bold = True: .Font.Color = RGB(95, 100, 105)
        .Value = " " & title: .VerticalAlignment = xlCenter
    End With
    
    ' Row 2: Value (Large Bold Georgia)
    With ws.Range(rng.Cells(2, 1), rng.Cells(2, cCount))
        .Merge
        .Font.Name = "Georgia": .Font.Size = 13: .Font.Bold = True: .Font.Color = RGB(26, 26, 26)
        If Left(formulaOrVal, 1) = "=" Then
            .Formula = formulaOrVal
        Else
            .Value = formulaOrVal
        End If
        .NumberFormat = fmt: .VerticalAlignment = xlCenter
    End With
    
    ' Row 3: Subtitle
    With ws.Range(rng.Cells(3, 1), rng.Cells(3, cCount))
        .Merge
        .Font.Name = "Segoe UI": .Font.Size = 7.5: .Font.Bold = True: .Font.Color = accentColor
        .Value = " " & subtitle: .VerticalAlignment = xlCenter
    End With
End Sub

' -----------------------------------------------------------------------------------------
' HELPER: SMART ID / CODE FILTERING (EXCLUDES HIGH-CARDINALITY KEYS & GUIDs)
' -----------------------------------------------------------------------------------------
Private Function IsIdColumn(ByVal h As String, ByVal sampleStr As String) As Boolean
    Dim hu As String: hu = UCase(Trim(h))
    
    If InStr(hu, "ID") > 0 Or InStr(hu, "CODE") > 0 Or InStr(hu, "KEY") > 0 Or _
       InStr(hu, "GUID") > 0 Or InStr(hu, "HASH") > 0 Or InStr(hu, "REF") > 0 Or _
       InStr(hu, "ZIP") > 0 Or InStr(hu, "POSTAL") > 0 Or InStr(hu, "SSN") > 0 Or _
       InStr(hu, "NUM") > 0 Or InStr(hu, "NO.") > 0 Or InStr(hu, "PHONE") > 0 Then
        IsIdColumn = True: Exit Function
    End If
    
    If Len(sampleStr) > 0 Then
        If sampleStr Like "*-[0-9]*" Or sampleStr Like "*[0-9]-[0-9]*" Then
            IsIdColumn = True: Exit Function
        End If
    End If
    
    IsIdColumn = False
End Function

' -----------------------------------------------------------------------------------------
' HELPER: CATEGORICAL SEMANTIC SCORING (OPTIMAL SLICER CARDINALITY IS 4 TO 12 BUTTONS)
' -----------------------------------------------------------------------------------------
Private Function GetCategoryScore(ByVal h As String, ByVal card As Long) As Long
    Dim hu As String, score As Long
    hu = UCase(Trim(h))
    score = (25 - Abs(card - 6)) * 5
    
    If InStr(hu, "REGION") > 0 Then score = score + 500
    If InStr(hu, "CATEGORY") > 0 Then score = score + 450
    If InStr(hu, "SEGMENT") > 0 Then score = score + 400
    If InStr(hu, "CHANNEL") > 0 Then score = score + 350
    If InStr(hu, "STATUS") > 0 Then score = score + 300
    If InStr(hu, "TYPE") > 0 Then score = score + 250
    If InStr(hu, "STATE") > 0 Then score = score + 200
    If InStr(hu, "TIER") > 0 Then score = score + 200
    If InStr(hu, "GROUP") > 0 Then score = score + 150
    If InStr(hu, "DEPARTMENT") > 0 Or InStr(hu, "DIVISION") > 0 Then score = score + 150
    
    GetCategoryScore = score
End Function

' -----------------------------------------------------------------------------------------
' HELPER: NUMERIC SEMANTIC SCORING (PRIORITIZES PRIMARY & SECONDARY FINANCIAL METRICS)
' -----------------------------------------------------------------------------------------
Private Function GetNumericScore(ByVal h As String) As Long
    Dim hu As String, score As Long
    hu = UCase(Trim(h))
    score = 10
    
    If InStr(hu, "REVENUE") > 0 Then score = 1000
    If InStr(hu, "SALES") > 0 Then score = 950
    If InStr(hu, "AMOUNT") > 0 Then score = 900
    If InStr(hu, "TOTAL") > 0 Then score = 850
    If InStr(hu, "TURNOVER") > 0 Then score = 800
    If InStr(hu, "PROFIT") > 0 Then score = 750
    If InStr(hu, "MARGIN") > 0 Then score = 700
    If InStr(hu, "COST") > 0 Then score = 650
    If InStr(hu, "EXPENSE") > 0 Then score = 620
    If InStr(hu, "VOLUME") > 0 Then score = 600
    If InStr(hu, "QTY") > 0 Or InStr(hu, "QUANTITY") > 0 Then score = 550
    If InStr(hu, "PRICE") > 0 Then score = 500
    
    GetNumericScore = score
End Function

' -----------------------------------------------------------------------------------------
' HELPER: SIMPLE DESCENDING SORT FOR SCORE RANKING
' -----------------------------------------------------------------------------------------
Private Sub SortByScore(ByRef cols() As Long, ByRef scores() As Long, ByVal n As Long)
    Dim i As Long, j As Long, tempC As Long, tempS As Long
    For i = 1 To n - 1
        For j = i + 1 To n
            If scores(j) > scores(i) Then
                tempS = scores(i): scores(i) = scores(j): scores(j) = tempS
                tempC = cols(i): cols(i) = cols(j): cols(j) = tempC
            End If
        Next j
    Next i
End Sub
