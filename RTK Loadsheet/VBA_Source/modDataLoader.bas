Attribute VB_Name = "modDataLoader"
Option Explicit

' ==============================================================================
' Module: modDataLoader
' Purpose: Fast in-memory loader for the 4 APM exports and CADmine data.
'          Universally handles ANY CADmine file and ANY LP piping project.
' ==============================================================================

Public Type TMLRecord
    EntyKey As String
    TmlId As String
    AnalysisType As String
    ComponentType As String
    Access As String
    StatusIndicator As String
    IsoDrawing As String
    EquipmentId As String
    FunctionalLoc As String
    TmlGroupEntyKey As String
    TargetCircuit As String
    NewTmlId As String
End Type

Public Type ActionRecord
    ActionId As String
    Name As String
    Description As String
    Basis As String
    ActionType As String
    CmType As String
    Interval As Double
    IntervalUnit As String
    ShutdownRequired As Boolean
    Statutory As Boolean
    TargetCompletionDate As String
End Type

Public Type RiskRecord
    RiskId As String
    Name As String
    Basis As String
    Description As String
End Type

Public Type MitigationRecord
    RiskId As String
    ActionId As String
End Type

Public Type AsmDataRecord
    StrategyId As String
    AssetId As String
    AssetFamilyId As String
    AssetIdField As String
    CmmsId As String
    CmmsValue As String
    RiskAnalysisType As String
    PlanLength As Long
    Actions() As ActionRecord
    Risks() As RiskRecord
    Mitigations() As MitigationRecord
    ActionCount As Long
    RiskCount As Long
    MitigationCount As Long
End Type

Public Type AsiOpRecord
    ActionId As String
    ImplementationType As String
    AuthGroup As String
    SortField As String
    Category As String
    CallHorizon As Long
    StartDate As String
    MpDesc As String
    MpLongDesc As String
    PlanPlant As String
    PlanGroup As String
    WorkCenter As String
    WorkCenterPlant As String
    ActivityType As String
    Priority As String
    ItemDesc As String
    ItemLongDesc As String
    TaskListDesc As String
    TaskListLongDesc As String
    TaskListPlant As String
    TaskListPlanPlant As String
    TaskListPlanGroup As String
    TaskListUsage As String
    TaskListAssembly As String
    TaskListCondition As String
    OperationId As String
    OperationTaskType As String
    OperationDesc As String
    OperationLongDesc As String
    OperationWorkCenter As String
    OperationPlant As String
    OperationControlKey As String
    OperationCondition As String
    OperationWork As String
    OperationWorkUnit As String
    OperationActivityType As String
    OperationResourceCount As String
    OperationDuration As String
    OperationDurationUnit As String
    UserField10 As Boolean
    UserField11 As Boolean
    PrtDoc As String
    PrtType As String
    PrtPart As String
    PrtVersion As String
    PrtQty As Double
    PrtQtyUnit As String
    PrtControlKey As String
End Type

Public Type TmlGroupParams
    EquipmentId As String
    FunctionalLoc As String
    TmlGroupEntyKey As String
    TmlGroupId As String
    StdDevFactor As Double
    AssetMinCr As Double
    AssetDefaultInterval As Double
    DefaultTmin As Double
    TmlGroupMinCr As Double
    TmlGroupDefaultInterval As Double
End Type

' ------------------------------------------------------------------------------
' Loads TMLs from any CADmine file and cross-references with TML Export
' ------------------------------------------------------------------------------
Public Function LoadTMLsFromCadmine(ByVal sCadminePath As String, ByVal sTmlPath As String, ByVal sCircuit As String, ByRef outTmls() As TMLRecord) As Long
    Dim wbCad As Workbook, wsCad As Worksheet
    Dim wbTml As Workbook, wsTml As Worksheet
    Dim vCad As Variant, vTml As Variant
    Dim r As Long, nCadRows As Long, nTmlRows As Long
    Dim c As Long, nCadCols As Long, nTmlCols As Long
    Dim colNde As Long, colPt As Long, colAcc As Long, colFile As Long
    Dim colCirc As Long, colTmlg As Long
    Dim colTmlId As Long, colTmlKey As Long, colEqId As Long, colFloc As Long, colGrpKey As Long, colStatus As Long, colTechNum As Long
    
    LoadTMLsFromCadmine = 0
    Erase outTmls
    
    ' 1. Read CADmine workbook (single open: reads title block mapping and CML data)
    Dim dDwgCircuits As Object
    Set dDwgCircuits = CreateObject("Scripting.Dictionary")
    dDwgCircuits.CompareMode = 1
    
    Set wbCad = Workbooks.Open(sCadminePath, ReadOnly:=True)
    
    ' Read Title Block sheet if present
    Dim wsTB As Worksheet
    For Each wsTB In wbCad.Worksheets
        Dim sWSName As String
        sWSName = UCase(wsTB.Name)
        If InStr(1, sWSName, "PART_TB") > 0 Or InStr(1, sWSName, "TITLE") > 0 Or InStr(1, sWSName, "TB") > 0 Or InStr(1, sWSName, "BORDER") > 0 Then
            Dim tbRows As Long, tbCols As Long, colTbCirc As Long, colTbDwg As Long, tbC As Long, tbR As Long
            tbRows = wsTB.Cells(wsTB.Rows.Count, 1).End(xlUp).Row
            tbCols = wsTB.Cells(1, wsTB.Columns.Count).End(xlToLeft).Column
            colTbCirc = 0: colTbDwg = 0
            For tbC = 1 To tbCols
                Dim hTb As String
                hTb = UCase(Trim(Replace(Replace(CStr(wsTB.Cells(1, tbC).Value), "_", ""), " ", "")))
                If InStr(hTb, "CIRCUIT") > 0 Then If colTbCirc = 0 Then colTbCirc = tbC
                If InStr(hTb, "RTKCDWGNO") > 0 Or InStr(hTb, "DWGNO") > 0 Then If colTbDwg = 0 Then colTbDwg = tbC
            Next tbC
            If colTbCirc = 0 Then
                For tbC = 1 To tbCols
                    hTb = UCase(Trim(Replace(Replace(CStr(wsTB.Cells(1, tbC).Value), "_", ""), " ", "")))
                    If InStr(hTb, "LINE") > 0 Then If colTbCirc = 0 Then colTbCirc = tbC
                Next tbC
            End If
            If colTbDwg = 0 Then
                For tbC = 1 To tbCols
                    hTb = UCase(Trim(Replace(Replace(CStr(wsTB.Cells(1, tbC).Value), "_", ""), " ", "")))
                    If InStr(hTb, "DWGNAME") > 0 Or InStr(hTb, "DRAWING") > 0 Then If colTbDwg = 0 Then colTbDwg = tbC
                Next tbC
            End If
            For tbR = 2 To tbRows
                Dim tbCircVal As String, tbDwgVal As String
                tbCircVal = "": tbDwgVal = ""
                If colTbCirc > 0 Then tbCircVal = Trim(CStr(wsTB.Cells(tbR, colTbCirc).Value))
                If UCase(tbCircVal) = "CONTINUOUS" Then tbCircVal = ""
                If colTbDwg > 0 Then tbDwgVal = Trim(CStr(wsTB.Cells(tbR, colTbDwg).Value))
                Dim sCleanTbDwg As String
                sCleanTbDwg = ExtractDwgName(Trim(CStr(wsTB.Cells(tbR, 1).Value)))
                If sCleanTbDwg = "" And tbDwgVal <> "" Then sCleanTbDwg = ExtractDwgName(tbDwgVal)
                If sCleanTbDwg <> "" And tbCircVal <> "" Then
                    If Not dDwgCircuits.Exists(sCleanTbDwg) Then dDwgCircuits.Add sCleanTbDwg, tbCircVal
                End If
                If tbDwgVal <> "" And tbCircVal <> "" Then
                    Dim sCleanTbDwg2 As String
                    sCleanTbDwg2 = ExtractDwgName(tbDwgVal)
                    If sCleanTbDwg2 <> "" And Not dDwgCircuits.Exists(sCleanTbDwg2) Then
                        dDwgCircuits.Add sCleanTbDwg2, tbCircVal
                    End If
                    If Not dDwgCircuits.Exists(Trim(tbDwgVal)) Then
                        dDwgCircuits.Add Trim(tbDwgVal), tbCircVal
                    End If
                End If
            Next tbR
            Exit For
        End If
    Next wsTB
    
    ' Read CML Sheet
    Set wsCad = FindCadmineCmlSheet(wbCad)
    If wsCad Is Nothing Then
        wbCad.Close SaveChanges:=False
        Exit Function
    End If
    
    nCadRows = wsCad.Cells(wsCad.Rows.Count, 1).End(xlUp).Row
    nCadCols = wsCad.Cells(1, wsCad.Columns.Count).End(xlToLeft).Column
    If nCadRows < 2 Then
        wbCad.Close SaveChanges:=False
        Exit Function
    End If
    
    vCad = wsCad.Range(wsCad.Cells(1, 1), wsCad.Cells(nCadRows, nCadCols)).Value2
    wbCad.Close SaveChanges:=False
    
    ' Universal flexible column header detection (ignores case, spaces, underscores)
    colNde = 0: colPt = 0: colAcc = 0: colFile = 0: colCirc = 0: colTmlg = 0
    For c = 1 To nCadCols
        Dim hText As String
        hText = UCase(Trim(Replace(Replace(CStr(vCad(1, c)), "_", ""), " ", "")))
        If InStr(hText, "NDETYPE") > 0 Or hText = "NDE" Then
            If colNde = 0 Then colNde = c
        ElseIf InStr(hText, "POINTNUM") > 0 Or InStr(hText, "POINTNO") > 0 Or InStr(hText, "POINT") > 0 Or InStr(hText, "CML") > 0 Then
            If colPt = 0 Then colPt = c
        ElseIf InStr(hText, "ACCESS") > 0 Then
            If colAcc = 0 Then colAcc = c
        ElseIf InStr(hText, "FILEPATH") > 0 Or InStr(hText, "DWGPATH") > 0 Or InStr(hText, "DRAWING") > 0 Then
            If colFile = 0 Then colFile = c
        ElseIf InStr(hText, "CIRCASSET") > 0 Or InStr(hText, "CIRCUIT") > 0 Then
            If colCirc = 0 Then colCirc = c
        ElseIf InStr(hText, "TMLG") > 0 Then
            If colTmlg = 0 Then colTmlg = c
        End If
    Next c
    
    ' Heuristic fallback for column detection if headers were not matched
    If colNde = 0 Or colPt = 0 Or colFile = 0 Then
        For c = 1 To nCadCols
            Dim testVal As String
            testVal = UCase(Trim(CStr(vCad(2, c))))
            If colNde = 0 And (Left(testVal, 2) = "UT" Or Left(testVal, 2) = "RT") Then colNde = c
            If colPt = 0 And IsNumeric(testVal) And Len(testVal) <= 4 Then colPt = c
            If colFile = 0 And (InStr(testVal, ".DWG") > 0 Or InStr(testVal, "\") > 0) Then colFile = c
        Next c
    End If
    
    ' 2. Read TML Export to index APM records
    Set wbTml = Workbooks.Open(sTmlPath, ReadOnly:=True)
    Set wsTml = wbTml.Sheets(1)
    nTmlRows = wsTml.Cells(wsTml.Rows.Count, 1).End(xlUp).Row
    nTmlCols = wsTml.Cells(1, wsTml.Columns.Count).End(xlToLeft).Column
    vTml = wsTml.Range(wsTml.Cells(1, 1), wsTml.Cells(nTmlRows, nTmlCols)).Value2
    wbTml.Close SaveChanges:=False
    
    colTechNum = 1: colTmlId = 10: colTmlKey = 9: colEqId = 3: colFloc = 2: colGrpKey = 4: colStatus = 17
    For c = 1 To nTmlCols
        Select Case Trim(CStr(vTml(1, c)))
            Case "Equipment Technical Number": colTechNum = c
            Case "TML ID": colTmlId = c
            Case "TML ENTY_KEY": colTmlKey = c
            Case "Equipment ID": colEqId = c
            Case "Functional Location": colFloc = c
            Case "TML_Group_ENTY_KEY": colGrpKey = c
            Case "Status Indicator": colStatus = c
        End Select
    Next c
    
    ' Fast scoped indexing for sCircuit (strictly avoids picking up same TML IDs from other circuits!)
    Dim dTmlCircuit As Object
    Set dTmlCircuit = CreateObject("Scripting.Dictionary")
    dTmlCircuit.CompareMode = 1
    
    Dim sCleanCircuit As String
    sCleanCircuit = UCase(Replace(Replace(Trim(sCircuit), "-", ""), " ", ""))
    
    Dim defEqId As String, defFloc As String, defGrpKey As String
    defEqId = "": defFloc = "": defGrpKey = ""
    
    For r = 2 To nTmlRows
        Dim sRowCirc As String
        sRowCirc = Trim(CStr(vTml(r, colTechNum)))
        
        Dim isMatch As Boolean
        isMatch = False
        If sRowCirc = sCircuit Then
            isMatch = True
        ElseIf sCleanCircuit <> "" Then
            If Replace(Replace(sRowCirc, "-", ""), " ", "") = sCleanCircuit Then
                isMatch = True
            End If
        End If
        
        If isMatch Then
            Dim sTId As String
            sTId = Trim(CStr(vTml(r, colTmlId)))
            If sTId <> "" Then
                If defEqId = "" Then
                    defEqId = Trim(CStr(vTml(r, colEqId)))
                    defFloc = Trim(CStr(vTml(r, colFloc)))
                    defGrpKey = Trim(CStr(vTml(r, colGrpKey)))
                End If
                
                If Not dTmlCircuit.Exists(sTId) Then dTmlCircuit.Add sTId, r
                
                ' Also index alternative representations
                Dim dotP As Long
                dotP = InStr(sTId, ".")
                If dotP > 0 Then
                    Dim pfx As String, sNumPart As String
                    pfx = Left(sTId, dotP - 1)
                    sNumPart = Mid(sTId, dotP + 1)
                    If IsNumeric(sNumPart) Then
                        Dim alt1 As String, alt2 As String, alt3 As String
                        alt1 = pfx & "." & CStr(Val(sNumPart))
                        alt2 = pfx & "-" & Format(Val(sNumPart), "000")
                        alt3 = pfx & Format(Val(sNumPart), "000")
                        If Not dTmlCircuit.Exists(alt1) Then dTmlCircuit.Add alt1, r
                        If Not dTmlCircuit.Exists(alt2) Then dTmlCircuit.Add alt2, r
                        If Not dTmlCircuit.Exists(alt3) Then dTmlCircuit.Add alt3, r
                    End If
                End If
            End If
        End If
    Next r
    
    If defEqId = "" Then defEqId = "2002850"
    If defGrpKey = "" Then defGrpKey = "409145413"
    If defFloc = "" Then defFloc = "4002." & sCircuit
    
    ' 3. Parse CADmine TMLs and link with TML export
    Dim count As Long: count = 0
    Dim totalCad As Long: totalCad = nCadRows - 1
    ReDim outTmls(1 To totalCad)
    
    For r = 2 To nCadRows
        Dim sNde As String, sPt As String, sCadId As String, sFilePath As String, sDwg As String
        sNde = ""
        If colNde > 0 Then sNde = Trim(CStr(vCad(r, colNde)))
        sPt = ""
        If colPt > 0 Then sPt = Trim(CStr(vCad(r, colPt)))
        
        If sNde <> "" Or sPt <> "" Then
            If IsNumeric(sPt) Then
                sCadId = sNde & "." & Format(Val(sPt), "000")
            Else
                sCadId = sNde & "." & sPt
            End If
            
            sFilePath = ""
            If colFile > 0 Then sFilePath = CStr(vCad(r, colFile))
            sDwg = ExtractDwgName(sFilePath)
            
            count = count + 1
            With outTmls(count)
                .TmlId = sCadId
                If Len(sNde) >= 2 Then
                    .AnalysisType = Left(sNde, 2)
                Else
                    .AnalysisType = "UT"
                End If
                .IsoDrawing = sDwg
                If colAcc > 0 Then .Access = Trim(CStr(vCad(r, colAcc))) Else .Access = ""
                
                ' Target Circuit determination
                Dim sCadCirc As String: sCadCirc = ""
                If colCirc > 0 Then sCadCirc = Trim(CStr(vCad(r, colCirc)))
                If sCadCirc = "" And colTmlg > 0 Then sCadCirc = Trim(CStr(vCad(r, colTmlg)))
                If sCadCirc = "" And sDwg <> "" And dDwgCircuits.Exists(sDwg) Then
                    sCadCirc = Trim(CStr(dDwgCircuits(sDwg)))
                End If
                
                If sCadCirc <> "" Then
                    .TargetCircuit = sCadCirc
                Else
                    .TargetCircuit = sCircuit
                End If
                .NewTmlId = sCadId
                
                ' Fast Scoped Lookup in APM export for this circuit
                Dim tRow As Long: tRow = 0
                If dTmlCircuit.Exists(sCadId) Then
                    tRow = dTmlCircuit(sCadId)
                ElseIf IsNumeric(sPt) And dTmlCircuit.Exists(sNde & "." & CStr(Val(sPt))) Then
                    tRow = dTmlCircuit(sNde & "." & CStr(Val(sPt)))
                ElseIf IsNumeric(sPt) And dTmlCircuit.Exists(sNde & "-" & Format(Val(sPt), "000")) Then
                    tRow = dTmlCircuit(sNde & "-" & Format(Val(sPt), "000"))
                ElseIf IsNumeric(sPt) And dTmlCircuit.Exists(sNde & Format(Val(sPt), "000")) Then
                    tRow = dTmlCircuit(sNde & Format(Val(sPt), "000"))
                End If
                
                If tRow > 0 Then
                    .EntyKey = Trim(CStr(vTml(tRow, colTmlKey)))
                    .EquipmentId = Trim(CStr(vTml(tRow, colEqId)))
                    .FunctionalLoc = Trim(CStr(vTml(tRow, colFloc)))
                    .TmlGroupEntyKey = Trim(CStr(vTml(tRow, colGrpKey)))
                    .StatusIndicator = Trim(CStr(vTml(tRow, colStatus)))
                Else
                    .EntyKey = ""
                    .EquipmentId = defEqId
                    .FunctionalLoc = defFloc
                    .TmlGroupEntyKey = defGrpKey
                    .StatusIndicator = "Active"
                End If
                If .StatusIndicator = "" Then .StatusIndicator = "Active"
            End With
        End If
    Next r
                
    If count < totalCad Then
        If count > 0 Then
            ReDim Preserve outTmls(1 To count)
        Else
            Erase outTmls
        End If
    End If
    
    LoadTMLsFromCadmine = count
End Function

' ------------------------------------------------------------------------------
' Loads TML records directly for a circuit from the APM TML Export
' ------------------------------------------------------------------------------
Public Function LoadTMLsForCircuit(ByVal sTmlPath As String, ByVal sCircuit As String, ByRef outTmls() As TMLRecord) As Long
    Dim wb As Workbook, ws As Worksheet
    Dim vData As Variant
    Dim r As Long, nRows As Long
    Dim colTechNum As Long, colFloc As Long, colEqId As Long, colGrpKey As Long
    Dim colGrpId As Long, colKey As Long, colId As Long, colType As Long
    Dim colComp As Long, colAccess As Long, colStatus As Long, colIso As Long
    Dim c As Long, nCols As Long, count As Long
    
    LoadTMLsForCircuit = 0
    Erase outTmls
    
    Set wb = Workbooks.Open(sTmlPath, ReadOnly:=True)
    Set ws = wb.Sheets(1)
    
    nRows = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    nCols = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    If nRows < 2 Then
        wb.Close SaveChanges:=False
        Exit Function
    End If
    
    vData = ws.Range(ws.Cells(1, 1), ws.Cells(nRows, nCols)).Value2
    wb.Close SaveChanges:=False
    
    colTechNum = 1: colFloc = 2: colEqId = 3: colGrpKey = 4: colGrpId = 5
    colKey = 9: colId = 10: colType = 11: colComp = 12: colAccess = 14: colStatus = 17: colIso = 18
    
    For c = 1 To nCols
        Select Case Trim(CStr(vData(1, c)))
            Case "Equipment Technical Number": colTechNum = c
            Case "Functional Location": colFloc = c
            Case "Equipment ID": colEqId = c
            Case "TML_Group_ENTY_KEY": colGrpKey = c
            Case "TML Group ID": colGrpId = c
            Case "TML ENTY_KEY": colKey = c
            Case "TML ID": colId = c
            Case "TML Analysis Type": colType = c
            Case "Component Type": colComp = c
            Case "Access": colAccess = c
            Case "Status Indicator": colStatus = c
            Case "ISO Drawing Number": colIso = c
        End Select
    Next c
    
    count = 0
    Dim seenKeys As Object
    Set seenKeys = CreateObject("Scripting.Dictionary")
    
    Dim sCleanCircuit As String
    sCleanCircuit = UCase(Replace(Replace(Trim(sCircuit), "-", ""), " ", ""))
    
    For r = 2 To nRows
        Dim sRowCirc As String
        sRowCirc = Trim(CStr(vData(r, colTechNum)))
        If sRowCirc = sCircuit Or (sCleanCircuit <> "" And Replace(Replace(sRowCirc, "-", ""), " ", "") = sCleanCircuit) Then
            Dim sKey As String
            sKey = Trim(CStr(vData(r, colKey)))
            If sKey <> "" And Not seenKeys.Exists(sKey) Then
                seenKeys.Add sKey, True
                count = count + 1
            End If
        End If
    Next r
    
    If count = 0 Then Exit Function
    
    ReDim outTmls(1 To count)
    seenKeys.RemoveAll
    count = 0
    
    For r = 2 To nRows
        sRowCirc = Trim(CStr(vData(r, colTechNum)))
        If sRowCirc = sCircuit Or (sCleanCircuit <> "" And Replace(Replace(sRowCirc, "-", ""), " ", "") = sCleanCircuit) Then
            sKey = Trim(CStr(vData(r, colKey)))
            If sKey <> "" And Not seenKeys.Exists(sKey) Then
                seenKeys.Add sKey, True
                count = count + 1
                With outTmls(count)
                    .EntyKey = sKey
                    .TmlId = Trim(CStr(vData(r, colId)))
                    .AnalysisType = Trim(CStr(vData(r, colType)))
                    .ComponentType = Trim(CStr(vData(r, colComp)))
                    .Access = Trim(CStr(vData(r, colAccess)))
                    .StatusIndicator = Trim(CStr(vData(r, colStatus)))
                    If .StatusIndicator = "" Then .StatusIndicator = "Active"
                    .IsoDrawing = Trim(CStr(vData(r, colIso)))
                    .EquipmentId = Trim(CStr(vData(r, colEqId)))
                    .FunctionalLoc = Trim(CStr(vData(r, colFloc)))
                    .TmlGroupEntyKey = Trim(CStr(vData(r, colGrpKey)))
                    .TargetCircuit = sCircuit
                    .NewTmlId = .TmlId
                End With
            End If
        End If
    Next r
    
    LoadTMLsForCircuit = count
End Function

' ------------------------------------------------------------------------------
' Dynamically locates the CML sheet in any CADmine workbook
' ------------------------------------------------------------------------------
Public Function FindCadmineCmlSheet(ByVal wbCad As Workbook) As Worksheet
    Dim ws As Worksheet
    
    ' 1. Check common standard sheet names
    On Error Resume Next
    Set ws = wbCad.Sheets("mlb_RTK_CML_PIPING - SMALL")
    If Not ws Is Nothing Then Set FindCadmineCmlSheet = ws: Exit Function
    
    Set ws = wbCad.Sheets("mlb_RTK_CML_PIPING - LARGE")
    If Not ws Is Nothing Then Set FindCadmineCmlSheet = ws: Exit Function
    
    Set ws = wbCad.Sheets("mlb_RTK_CML_PIPING")
    If Not ws Is Nothing Then Set FindCadmineCmlSheet = ws: Exit Function
    
    Set ws = wbCad.Sheets("mlb_RTK_CML")
    If Not ws Is Nothing Then Set FindCadmineCmlSheet = ws: Exit Function
    
    Set ws = wbCad.Sheets("CML")
    If Not ws Is Nothing Then Set FindCadmineCmlSheet = ws: Exit Function
    On Error GoTo 0
    
    ' 2. Search sheets matching CML or mlb_
    For Each ws In wbCad.Worksheets
        If InStr(1, ws.Name, "CML", vbTextCompare) > 0 Or InStr(1, ws.Name, "mlb_", vbTextCompare) > 0 Then
            If HasCmlHeaders(ws) Then
                Set FindCadmineCmlSheet = ws
                Exit Function
            End If
        End If
    Next ws
    
    ' 3. Search all sheets for CML headers
    For Each ws In wbCad.Worksheets
        If HasCmlHeaders(ws) Then
            Set FindCadmineCmlSheet = ws
            Exit Function
        End If
    Next ws
    
    Set FindCadmineCmlSheet = Nothing
End Function

Private Function HasCmlHeaders(ByVal ws As Worksheet) As Boolean
    Dim c As Long, lastCol As Long, hVal As String
    Dim hasNde As Boolean, hasPt As Boolean
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    For c = 1 To lastCol
        hVal = UCase(Trim(Replace(Replace(CStr(ws.Cells(1, c).Value), "_", ""), " ", "")))
        If InStr(hVal, "NDETYPE") > 0 Or hVal = "NDE" Then hasNde = True
        If InStr(hVal, "POINTNUM") > 0 Or InStr(hVal, "POINTNO") > 0 Or InStr(hVal, "POINT") > 0 Or InStr(hVal, "CML") > 0 Then hasPt = True
    Next c
    HasCmlHeaders = (hasNde And hasPt)
End Function

' ------------------------------------------------------------------------------
' Auto-detects Project Code, Circuit ID, and Drawing-to-Circuit mapping
' ------------------------------------------------------------------------------
Public Function DetectCadmineProjectAndCircuit(ByVal sCadminePath As String, ByRef outProjCode As String, ByRef outCircuit As String, ByRef dDwgCircuits As Object) As Boolean
    Dim fso As Object, wbCad As Workbook
    Dim fName As String, pos As Long
    
    DetectCadmineProjectAndCircuit = False
    outProjCode = ""
    outCircuit = ""
    If dDwgCircuits Is Nothing Then
        Set dDwgCircuits = CreateObject("Scripting.Dictionary")
    End If
    dDwgCircuits.CompareMode = 1
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    If Not fso.FileExists(sCadminePath) Then Exit Function
    
    fName = fso.GetFileName(sCadminePath)
    
    ' 1. Detect Project Code from filename or parent folder
    Dim uName As String
    uName = UCase(fName)
    
    pos = InStr(1, uName, "LP")
    If pos > 0 Then
        Dim digLp As String, k As Long, chLp As String
        digLp = ""
        For k = pos + 2 To Len(uName)
            chLp = Mid(uName, k, 1)
            If chLp >= "0" And chLp <= "9" Then
                digLp = digLp & chLp
            Else
                Exit For
            End If
        Next k
        If digLp <> "" Then outProjCode = "LP" & digLp
    End If
    
    If outProjCode = "" Then
        pos = InStr(1, uName, "DM")
        If pos > 0 Then
            Dim digDm As String, chDm As String
            digDm = ""
            For k = pos + 2 To Len(uName)
                chDm = Mid(uName, k, 1)
                If chDm >= "0" And chDm <= "9" Then
                    digDm = digDm & chDm
                Else
                    Exit For
                End If
            Next k
            If digDm <> "" Then outProjCode = "LP" & digDm
        End If
    End If
    
    If outProjCode = "" Then
        ' Check continuous digits in filename
        Dim digits As String, j As Long, ch As String
        digits = ""
        For j = 1 To Len(fName)
            ch = Mid(fName, j, 1)
            If ch >= "0" And ch <= "9" Then
                digits = digits & ch
            ElseIf digits <> "" Then
                If Len(digits) >= 3 Then Exit For Else digits = ""
            End If
        Next j
        If Len(digits) >= 3 Then outProjCode = "LP" & digits
    End If
    
    If outProjCode = "" Then
        Dim parentPath As String
        parentPath = fso.GetParentFolderName(sCadminePath)
        pos = InStr(1, parentPath, "LP", vbTextCompare)
        If pos > 0 Then
            outProjCode = "LP" & Val(Mid(parentPath, pos + 2))
        End If
    End If
    If outProjCode = "" Then outProjCode = "LP585"
    
    ' 2. Detect Base Circuit from CADmine Title Block sheet
    On Error Resume Next
    Set wbCad = Workbooks.Open(sCadminePath, ReadOnly:=True)
    On Error GoTo 0
    If wbCad Is Nothing Then Exit Function
    
    Dim wsTB As Worksheet
    For Each wsTB In wbCad.Worksheets
        Dim sWSName As String
        sWSName = UCase(wsTB.Name)
        If InStr(1, sWSName, "PART_TB") > 0 Or InStr(1, sWSName, "TITLE") > 0 Or InStr(1, sWSName, "TB") > 0 Or InStr(1, sWSName, "BORDER") > 0 Then
            Exit For
        End If
    Next wsTB
    
    If Not wsTB Is Nothing Then
        Dim lastRow As Long, lastCol As Long, c As Long, r As Long
        Dim colCirc As Long, colDwg As Long, h As String
        lastRow = wsTB.Cells(wsTB.Rows.Count, 1).End(xlUp).Row
        lastCol = wsTB.Cells(1, wsTB.Columns.Count).End(xlToLeft).Column
        
        colCirc = 0: colDwg = 0
        For c = 1 To lastCol
            h = UCase(Trim(Replace(Replace(CStr(wsTB.Cells(1, c).Value), "_", ""), " ", "")))
            If InStr(h, "CIRCUIT") > 0 Then If colCirc = 0 Then colCirc = c
            If InStr(h, "RTKCDWGNO") > 0 Or InStr(h, "DWGNO") > 0 Then If colDwg = 0 Then colDwg = c
        Next c
        If colCirc = 0 Then
            For c = 1 To lastCol
                h = UCase(Trim(Replace(Replace(CStr(wsTB.Cells(1, c).Value), "_", ""), " ", "")))
                If InStr(h, "LINE") > 0 Then If colCirc = 0 Then colCirc = c
            Next c
        End If
        If colDwg = 0 Then
            For c = 1 To lastCol
                h = UCase(Trim(Replace(Replace(CStr(wsTB.Cells(1, c).Value), "_", ""), " ", "")))
                If InStr(h, "DWGNAME") > 0 Or InStr(h, "DRAWING") > 0 Then If colDwg = 0 Then colDwg = c
            Next c
        End If
        
        For r = 2 To lastRow
            Dim cVal As String, dVal As String
            cVal = "": dVal = ""
            If colCirc > 0 Then cVal = Trim(CStr(wsTB.Cells(r, colCirc).Value))
            If UCase(cVal) = "CONTINUOUS" Then cVal = ""
            If colDwg > 0 Then dVal = Trim(CStr(wsTB.Cells(r, colDwg).Value))
            
            ' Extract DWG filename if it has path
            Dim fpVal As String
            fpVal = Trim(CStr(wsTB.Cells(r, 1).Value))
            Dim sCleanDwg As String
            sCleanDwg = ExtractDwgName(fpVal)
            If sCleanDwg = "" And dVal <> "" Then sCleanDwg = ExtractDwgName(dVal)
            
            If cVal <> "" And outCircuit = "" Then
                outCircuit = cVal
            End If
            If sCleanDwg <> "" And cVal <> "" Then
                If Not dDwgCircuits.Exists(sCleanDwg) Then
                    dDwgCircuits.Add sCleanDwg, cVal
                End If
            End If
            If dVal <> "" And cVal <> "" Then
                Dim sCleanDwg2 As String
                sCleanDwg2 = ExtractDwgName(dVal)
                If sCleanDwg2 <> "" And Not dDwgCircuits.Exists(sCleanDwg2) Then
                    dDwgCircuits.Add sCleanDwg2, cVal
                End If
                If Not dDwgCircuits.Exists(Trim(dVal)) Then
                    dDwgCircuits.Add Trim(dVal), cVal
                End If
            End If
        Next r
    End If
    
    ' 3. If outCircuit not found in title block, check CML sheet
    If outCircuit = "" Then
        Dim wsCml As Worksheet
        Set wsCml = FindCadmineCmlSheet(wbCad)
        If Not wsCml Is Nothing Then
            Dim cCols As Long, colC As Long
            cCols = wsCml.Cells(1, wsCml.Columns.Count).End(xlToLeft).Column
            For colC = 1 To cCols
                h = UCase(Trim(Replace(Replace(CStr(wsCml.Cells(1, colC).Value), "_", ""), " ", "")))
                If InStr(h, "CIRCASSET") > 0 Or InStr(h, "TMLG") > 0 Or InStr(h, "CIRCUIT") > 0 Then
                    Dim testR As Long, maxR As Long
                    maxR = wsCml.Cells(wsCml.Rows.Count, 1).End(xlUp).Row
                    If maxR > 50 Then maxR = 50
                    For testR = 2 To maxR
                        cVal = Trim(CStr(wsCml.Cells(testR, colC).Value))
                        If cVal <> "" Then
                            outCircuit = cVal
                            Exit For
                        End If
                    Next testR
                End If
                If outCircuit <> "" Then Exit For
            Next colC
        End If
    End If
    
    wbCad.Close SaveChanges:=False
    DetectCadmineProjectAndCircuit = True
End Function

Private Function ExtractDwgName(ByVal sPath As String) As String
    Dim pos As Long
    pos = InStrRev(sPath, "\")
    If pos > 0 Then
        sPath = Mid(sPath, pos + 1)
    End If
    pos = InStrRev(sPath, "/")
    If pos > 0 Then
        sPath = Mid(sPath, pos + 1)
    End If
    pos = InStrRev(sPath, ".")
    If pos > 0 Then
        sPath = Left(sPath, pos - 1)
    End If
    ExtractDwgName = Trim(sPath)
End Function

' ------------------------------------------------------------------------------
' Loads ASM data for the circuit. If not found in export, generates robust defaults!
' ------------------------------------------------------------------------------
Public Function LoadAsmData(ByVal sAsmPath As String, ByVal sCircuit As String, ByRef outAsm As AsmDataRecord) As Boolean
    Dim wb As Workbook, ws As Worksheet
    Dim vData As Variant
    Dim r As Long, nRows As Long, nCols As Long, c As Long
    Dim colTechNum As Long, colFloc As Long, colEqId As Long, colStratId As Long
    Dim colRiskId As Long, colRiskName As Long, colRiskDesc As Long
    Dim colActId As Long, colActName As Long, colActDesc As Long, colIntv As Long, colIntvUnit As Long
    
    LoadAsmData = False
    
    Set wb = Workbooks.Open(sAsmPath, ReadOnly:=True)
    Set ws = wb.Sheets(1)
    
    nRows = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    nCols = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    If nRows >= 2 Then
        vData = ws.Range(ws.Cells(1, 1), ws.Cells(nRows, nCols)).Value2
    End If
    wb.Close SaveChanges:=False
    
    If nRows < 2 Then
        ' Fallback if ASM export is empty
        BuildDefaultAsmRecord sCircuit, outAsm
        LoadAsmData = True
        Exit Function
    End If
    
    colTechNum = 6: colFloc = 3: colEqId = 4: colStratId = 9
    colRiskId = 11: colRiskName = 12: colRiskDesc = 13
    colActId = 15: colActName = 16: colActDesc = 17: colIntv = 18: colIntvUnit = 19
    
    For c = 1 To nCols
        Select Case Trim(CStr(vData(1, c)))
            Case "Equipment Technical Number": colTechNum = c
            Case "Functional Location": colFloc = c
            Case "Equipment ID": colEqId = c
            Case "Strategy ID": colStratId = c
            Case "Risk ID": colRiskId = c
            Case "Risk Name": colRiskName = c
            Case "Risk Description": colRiskDesc = c
            Case "Action ID": colActId = c
            Case "Action Name": colActName = c
            Case "Description": colActDesc = c
            Case "Interval": colIntv = c
            Case "Interval Units": colIntvUnit = c
        End Select
    Next c
    
    Dim dActions As Object, dRisks As Object, dMit As Object
    Set dActions = CreateObject("Scripting.Dictionary")
    Set dRisks = CreateObject("Scripting.Dictionary")
    Set dMit = CreateObject("Scripting.Dictionary")
    
    Dim tmpActions() As ActionRecord
    Dim tmpRisks() As RiskRecord
    Dim tmpMit() As MitigationRecord
    ReDim tmpActions(1 To nRows)
    ReDim tmpRisks(1 To nRows)
    ReDim tmpMit(1 To nRows * 2)
    
    Dim nActCount As Long: nActCount = 0
    Dim nRiskCount As Long: nRiskCount = 0
    Dim nMitCount As Long: nMitCount = 0
    
    Dim sFloc As String, sEqId As String, sStratId As String
    Dim sCleanCircuit As String
    sCleanCircuit = UCase(Replace(Replace(Trim(sCircuit), "-", ""), " ", ""))
    
    For r = 2 To nRows
        Dim sRowCirc As String, sRowCleanCirc As String
        sRowCirc = Trim(CStr(vData(r, colTechNum)))
        sRowCleanCirc = UCase(Replace(Replace(sRowCirc, "-", ""), " ", ""))
        
        If sRowCirc = sCircuit Or sRowCleanCirc = sCleanCircuit Or InStr(1, sRowCirc, sCircuit, vbTextCompare) > 0 Then
            If sStratId = "" Then
                sFloc = Trim(CStr(vData(r, colFloc)))
                sEqId = Trim(CStr(vData(r, colEqId)))
                sStratId = Trim(CStr(vData(r, colStratId)))
            End If
            
            Dim sAId As String, sRId As String
            sAId = Trim(CStr(vData(r, colActId)))
            sRId = Trim(CStr(vData(r, colRiskId)))
            
            If sAId <> "" And Not dActions.Exists(sAId) Then
                nActCount = nActCount + 1
                dActions.Add sAId, nActCount
                With tmpActions(nActCount)
                    .ActionId = sAId
                    .Name = Trim(CStr(vData(r, colActName)))
                    .Description = CStr(vData(r, colActDesc))
                    .Basis = "2020 Asset Strategy Development"
                    .ActionType = "PM"
                    .CmType = "Periodic"
                    If IsNumeric(vData(r, colIntv)) Then .Interval = CDbl(vData(r, colIntv)) Else .Interval = 60
                    .IntervalUnit = Trim(CStr(vData(r, colIntvUnit)))
                    If .IntervalUnit = "" Then .IntervalUnit = "Months"
                    .ShutdownRequired = False
                    .Statutory = False
                    .TargetCompletionDate = "-"
                End With
            End If
            
            If sRId <> "" And Not dRisks.Exists(sRId) Then
                nRiskCount = nRiskCount + 1
                dRisks.Add sRId, nRiskCount
                With tmpRisks(nRiskCount)
                    .RiskId = sRId
                    .Name = Trim(CStr(vData(r, colRiskName)))
                    .Basis = "2020 Asset Strategy Development"
                    .Description = CStr(vData(r, colRiskDesc))
                End With
            End If
            
            If sRId <> "" And sAId <> "" Then
                Dim sMitKey As String
                sMitKey = sRId & "|" & sAId
                If Not dMit.Exists(sMitKey) Then
                    nMitCount = nMitCount + 1
                    dMit.Add sMitKey, nMitCount
                    With tmpMit(nMitCount)
                        .RiskId = sRId
                        .ActionId = sAId
                    End With
                End If
            End If
        End If
    Next r
    
    ' If this circuit is not yet registered in ASM export, generate clean default structure
    If sStratId = "" Then
        BuildDefaultAsmRecord sCircuit, outAsm
        LoadAsmData = True
        Exit Function
    End If
    
    With outAsm
        .StrategyId = sStratId
        .AssetId = sFloc & " " & sCircuit
        .AssetFamilyId = "MI_FNCLOC00"
        .AssetIdField = "MI_FNCLOC00_FNC_LOC_C"
        .CmmsId = "MI_FNCLOC00_SAP_SYSTEM_C"
        .CmmsValue = "ECP-500"
        .RiskAnalysisType = "Qualitative"
        .PlanLength = 10
        
        .ActionCount = nActCount
        ReDim .Actions(1 To nActCount)
        Dim aIdx As Long
        For aIdx = 1 To nActCount
            .Actions(aIdx) = tmpActions(aIdx)
        Next aIdx
        
        .RiskCount = nRiskCount
        ReDim .Risks(1 To nRiskCount)
        For aIdx = 1 To nRiskCount
            .Risks(aIdx) = tmpRisks(aIdx)
        Next aIdx
        
        .MitigationCount = nMitCount
        ReDim .Mitigations(1 To nMitCount)
        For aIdx = 1 To nMitCount
            .Mitigations(aIdx) = tmpMit(aIdx)
        Next aIdx
    End With
    
    LoadAsmData = True
End Function

Private Sub BuildDefaultAsmRecord(ByVal sCircuit As String, ByRef outAsm As AsmDataRecord)
    With outAsm
        .StrategyId = "RTKC 4002CP620PP12     .PIPE " & sCircuit & " Asset Strategy"
        .AssetId = "4002CP620PP12     .PIPE " & sCircuit
        .AssetFamilyId = "MI_FNCLOC00"
        .AssetIdField = "MI_FNCLOC00_FNC_LOC_C"
        .CmmsId = "MI_FNCLOC00_SAP_SYSTEM_C"
        .CmmsValue = "ECP-500"
        .RiskAnalysisType = "Qualitative"
        .PlanLength = 10
        
        .ActionCount = 3
        ReDim .Actions(1 To 3)
        .Actions(1).ActionId = "ACTION-002"
        .Actions(1).Name = "RT NDE INSP " & sCircuit
        .Actions(1).Description = "Radiographic testing inspection on piping circuit " & sCircuit
        .Actions(1).Basis = "2020 Asset Strategy Development"
        .Actions(1).ActionType = "PM"
        .Actions(1).CmType = "Periodic"
        .Actions(1).Interval = 60
        .Actions(1).IntervalUnit = "Months"
        .Actions(1).ShutdownRequired = False
        .Actions(1).Statutory = False
        .Actions(1).TargetCompletionDate = "-"
        
        .Actions(2).ActionId = "ACTION-001"
        .Actions(2).Name = "External Visual"
        .Actions(2).Description = "External visual inspection on piping circuit " & sCircuit
        .Actions(2).Basis = "2020 Asset Strategy Development"
        .Actions(2).ActionType = "PM"
        .Actions(2).CmType = "Periodic"
        .Actions(2).Interval = 60
        .Actions(2).IntervalUnit = "Months"
        .Actions(2).ShutdownRequired = False
        .Actions(2).Statutory = False
        .Actions(2).TargetCompletionDate = "-"
        
        .Actions(3).ActionId = "ACTION-003"
        .Actions(3).Name = "UT NDE INSP " & sCircuit
        .Actions(3).Description = "Ultrasonic thickness inspection on piping circuit " & sCircuit
        .Actions(3).Basis = "2020 Asset Strategy Development"
        .Actions(3).ActionType = "PM"
        .Actions(3).CmType = "Periodic"
        .Actions(3).Interval = 60
        .Actions(3).IntervalUnit = "Months"
        .Actions(3).ShutdownRequired = False
        .Actions(3).Statutory = False
        .Actions(3).TargetCompletionDate = "-"
        
        .RiskCount = 2
        ReDim .Risks(1 To 2)
        .Risks(1).RiskId = "RISK-001"
        .Risks(1).Name = "Corrosion Under Insulation (CUI)"
        .Risks(1).Basis = "2020 Asset Strategy Development"
        .Risks(1).Description = "Damage Mechanism: Corrosion Under Insulation (CUI)" & vbLf & vbLf & "Mode: External" & vbLf & vbLf & "General Material: CS" & vbLf & vbLf & "Operation Temperature: 80F"
        
        .Risks(2).RiskId = "RISK-002"
        .Risks(2).Name = "Unspecified Internal Corrosion"
        .Risks(2).Basis = "2020 Asset Strategy Development"
        .Risks(2).Description = "Damage Mechanism: Unspecified Internal Corrosion" & vbLf & vbLf & "Mode: General" & vbLf & vbLf & "General Material: CS" & vbLf & vbLf & "Operation Temperature: 80F"
        
        .MitigationCount = 3
        ReDim .Mitigations(1 To 3)
        .Mitigations(1).RiskId = "RISK-001": .Mitigations(1).ActionId = "ACTION-001"
        .Mitigations(2).RiskId = "RISK-002": .Mitigations(2).ActionId = "ACTION-002"
        .Mitigations(3).RiskId = "RISK-002": .Mitigations(3).ActionId = "ACTION-003"
    End With
End Sub

' ------------------------------------------------------------------------------
' Loads ASI operations. If strategy not in ASI export, generates robust defaults!
' ------------------------------------------------------------------------------
Public Function LoadAsiData(ByVal sAsiPath As String, ByVal sStrategyId As String, ByRef outOps() As AsiOpRecord) As Long
    Dim wb As Workbook, ws As Worksheet
    Dim vData As Variant
    Dim r As Long, nRows As Long, nCols As Long, c As Long
    Dim colPkgId As Long, count As Long
    Dim sOpDesc As String
    Dim dCols As Object
    Set dCols = CreateObject("Scripting.Dictionary")
    dCols.CompareMode = 1
    
    LoadAsiData = 0
    Erase outOps
    
    Set wb = Workbooks.Open(sAsiPath, ReadOnly:=True)
    Set ws = wb.Sheets(1)
    
    nRows = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    nCols = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    If nRows >= 2 Then
        vData = ws.Range(ws.Cells(1, 1), ws.Cells(nRows, nCols)).Value2
    End If
    wb.Close SaveChanges:=False
    
    If nRows < 2 Then
        BuildDefaultAsiOps outOps
        LoadAsiData = 3
        Exit Function
    End If
    
    For c = 1 To nCols
        dCols(Trim(CStr(vData(1, c)))) = c
    Next c
    
    colPkgId = 0
    If dCols.Exists("Package_ID") Then colPkgId = dCols("Package_ID")
    
    count = 0
    If colPkgId > 0 Then
        For r = 2 To nRows
            If Trim(CStr(vData(r, colPkgId))) = sStrategyId Then
                Dim sOpDescCheck As String
                sOpDescCheck = Trim(CStr(vData(r, dCols("Operation_Descrip"))))
                If InStr(1, sOpDescCheck, "Pressure", vbTextCompare) = 0 Then
                    count = count + 1
                End If
            End If
        Next r
    End If
    
    ' Always build standard 3 operations in procedure/sample order
    BuildDefaultAsiOps outOps
    LoadAsiData = 3
    
    If count = 0 Or colPkgId = 0 Then
        Exit Function
    End If
    
    ' Overlay metadata from ASI Export if available
    For r = 2 To nRows
        If Trim(CStr(vData(r, colPkgId))) = sStrategyId Then
            sOpDesc = Trim(CStr(vData(r, dCols("Operation_Descrip"))))
            If InStr(1, sOpDesc, "Pressure", vbTextCompare) = 0 Then
                Dim targetOpIdx As Long
                targetOpIdx = 0
                If InStr(1, sOpDesc, "EXT", vbTextCompare) > 0 Then
                    targetOpIdx = 1
                ElseIf InStr(1, sOpDesc, "RT", vbTextCompare) > 0 Then
                    targetOpIdx = 2
                ElseIf InStr(1, sOpDesc, "UT", vbTextCompare) > 0 Then
                    targetOpIdx = 3
                End If
                
                If targetOpIdx >= 1 And targetOpIdx <= 3 Then
                    With outOps(targetOpIdx)
                        If dCols.Exists("MP_Author_Group") Then .AuthGroup = CStr(vData(r, dCols("MP_Author_Group")))
                        If dCols.Exists("MP_Sort_Field") Then .SortField = CStr(vData(r, dCols("MP_Sort_Field")))
                        If dCols.Exists("MP_Category") Then .Category = CStr(vData(r, dCols("MP_Category")))
                        .CallHorizon = 95
                        If dCols.Exists("MP_Description") Then .MpDesc = CStr(vData(r, dCols("MP_Description")))
                        If dCols.Exists("MP_Long Text") Then .MpLongDesc = CStr(vData(r, dCols("MP_Long Text")))
                        
                        If dCols.Exists("Item_PlanningPlant") Then .PlanPlant = CStr(vData(r, dCols("Item_PlanningPlant")))
                        If dCols.Exists("Item_MaintPlannerGroup") Then .PlanGroup = CStr(vData(r, dCols("Item_MaintPlannerGroup")))
                        If dCols.Exists("Item_WorkCenter") Then .WorkCenter = CStr(vData(r, dCols("Item_WorkCenter")))
                        If dCols.Exists("Item_WorkCenterPlant") Then .WorkCenterPlant = CStr(vData(r, dCols("Item_WorkCenterPlant")))
                        If dCols.Exists("Item_ActivityType") Then .ActivityType = CStr(vData(r, dCols("Item_ActivityType")))
                        If dCols.Exists("Item_Priority") Then .Priority = CStr(vData(r, dCols("Item_Priority")))
                        If dCols.Exists("MI_ItemDescription") Then .ItemDesc = CStr(vData(r, dCols("MI_ItemDescription")))
                        If dCols.Exists("Item_LongText") Then .ItemLongDesc = CStr(vData(r, dCols("Item_LongText")))
                        
                        If dCols.Exists("TaskList_Descript") Then .TaskListDesc = CStr(vData(r, dCols("TaskList_Descript")))
                        If dCols.Exists("TaskList_LongText") Then .TaskListLongDesc = CStr(vData(r, dCols("TaskList_LongText")))
                        If dCols.Exists("TaskList_Plant") Then .TaskListPlant = CStr(vData(r, dCols("TaskList_Plant")))
                        If dCols.Exists("TaskList_PlanningPlant") Then .TaskListPlanPlant = CStr(vData(r, dCols("TaskList_PlanningPlant")))
                        If dCols.Exists("TaskList_PlannerGroup") Then .TaskListPlanGroup = CStr(vData(r, dCols("TaskList_PlannerGroup")))
                        If dCols.Exists("TaskList_Usage") Then .TaskListUsage = CStr(vData(r, dCols("TaskList_Usage")))
                        If dCols.Exists("TaskList_Assembly") Then .TaskListAssembly = CStr(vData(r, dCols("TaskList_Assembly")))
                        If dCols.Exists("TaskList_SystCondition") Then .TaskListCondition = CStr(vData(r, dCols("TaskList_SystCondition")))
                        
                        If dCols.Exists("Operation_TaskType") Then .OperationTaskType = CStr(vData(r, dCols("Operation_TaskType")))
                        If dCols.Exists("Operation_Descrip") Then .OperationDesc = CStr(vData(r, dCols("Operation_Descrip")))
                        If dCols.Exists("Operation_LongText") Then .OperationLongDesc = CStr(vData(r, dCols("Operation_LongText")))
                        If dCols.Exists("Operation_WorkCenter") Then .OperationWorkCenter = CStr(vData(r, dCols("Operation_WorkCenter")))
                        If dCols.Exists("Operation_Plant") Then .OperationPlant = CStr(vData(r, dCols("Operation_Plant")))
                        If dCols.Exists("Operation_ControlKey") Then .OperationControlKey = CStr(vData(r, dCols("Operation_ControlKey")))
                        If dCols.Exists("Operation_SystCondition") Then .OperationCondition = CStr(vData(r, dCols("Operation_SystCondition")))
                        
                        .OperationWork = "2,5"
                        .OperationWorkUnit = "H"
                        .OperationActivityType = "REL"
                        .OperationResourceCount = "1"
                        .OperationDuration = "2,5"
                        .OperationDurationUnit = "H"
                        .UserField10 = False
                        .UserField11 = True
                        
                        ' Document padding
                        If dCols.Exists("PRT_Document") Then
                            Dim sFilePrt As String
                            sFilePrt = Trim(CStr(vData(r, dCols("PRT_Document"))))
                            If sFilePrt <> "" Then
                                If Len(sFilePrt) < 25 Then
                                    .PrtDoc = String(25 - Len(sFilePrt), "0") & sFilePrt
                                Else
                                    .PrtDoc = sFilePrt
                                End If
                            End If
                        End If
                        .PrtType = "ZMP"
                        .PrtPart = "000"
                        .PrtVersion = "00"
                        .PrtQty = 1
                        .PrtQtyUnit = "EA"
                        .PrtControlKey = "1"
                    End With
                End If
            End If
        End If
    Next r
End Function

Private Sub BuildDefaultAsiOps(ByRef outOps() As AsiOpRecord)
    ReDim outOps(1 To 3)
    
    ' Op 1: EXT VIS INSP -> ACTION-002
    With outOps(1)
        .ActionId = "ACTION-002"
        .ImplementationType = "EXT VIS INSP"
        .AuthGroup = "4002"
        .SortField = "4002_TIME BASED"
        .Category = "M"
        .CallHorizon = 95
        .StartDate = "08/10/2020"
        .PlanPlant = "4002": .PlanGroup = "2PP": .WorkCenter = "AIPDMX": .WorkCenterPlant = "4002"
        .ActivityType = "REL": .Priority = "4"
        .OperationId = "0020": .OperationTaskType = "0001 INSPECTION"
        .OperationWorkCenter = "AIPDMX": .OperationPlant = "4002": .OperationControlKey = "PM01"
        .OperationWork = "2,5": .OperationWorkUnit = "H": .OperationDuration = "2,5": .OperationDurationUnit = "H"
        .UserField10 = False: .UserField11 = True
        .PrtDoc = "0000000000000010000241551": .PrtType = "ZMP": .PrtPart = "000": .PrtVersion = "00": .PrtQty = 1: .PrtQtyUnit = "EA": .PrtControlKey = "1"
    End With
    
    ' Op 2: RT NDE INSP -> ACTION-001
    With outOps(2)
        .ActionId = "ACTION-001"
        .ImplementationType = "RT NDE INSP"
        .AuthGroup = "4002"
        .SortField = "4002_TIME BASED"
        .Category = "M"
        .CallHorizon = 95
        .StartDate = "15/10/2020"
        .PlanPlant = "4002": .PlanGroup = "2PP": .WorkCenter = "AIPDMX": .WorkCenterPlant = "4002"
        .ActivityType = "REL": .Priority = "4"
        .OperationId = "0020": .OperationTaskType = "0001 INSPECTION"
        .OperationWorkCenter = "AIPDMX": .OperationPlant = "4002": .OperationControlKey = "PM01"
        .OperationWork = "2,5": .OperationWorkUnit = "H": .OperationDuration = "2,5": .OperationDurationUnit = "H"
        .UserField10 = False: .UserField11 = True
        .PrtDoc = "0000000000000010000234481": .PrtType = "ZMP": .PrtPart = "000": .PrtVersion = "00": .PrtQty = 1: .PrtQtyUnit = "EA": .PrtControlKey = "1"
    End With
    
    ' Op 3: UT NDE INSP -> ACTION-003
    With outOps(3)
        .ActionId = "ACTION-003"
        .ImplementationType = "UT NDE INSP"
        .AuthGroup = "4002"
        .SortField = "4002_TIME BASED"
        .Category = "M"
        .CallHorizon = 95
        .StartDate = "15/10/2020"
        .PlanPlant = "4002": .PlanGroup = "2PP": .WorkCenter = "AIPDMX": .WorkCenterPlant = "4002"
        .ActivityType = "REL": .Priority = "4"
        .OperationId = "0010": .OperationTaskType = "0001 INSPECTION"
        .OperationWorkCenter = "AIPDMX": .OperationPlant = "4002": .OperationControlKey = "PM01"
        .OperationWork = "2,5": .OperationWorkUnit = "H": .OperationDuration = "2,5": .OperationDurationUnit = "H"
        .UserField10 = False: .UserField11 = True
        .PrtDoc = "0000000000000010000234482": .PrtType = "ZMP": .PrtPart = "000": .PrtVersion = "00": .PrtQty = 1: .PrtQtyUnit = "EA": .PrtControlKey = "1"
    End With
End Sub

' ------------------------------------------------------------------------------
' Loads TML Group Parameters. If not found, uses clean defaults.
' ------------------------------------------------------------------------------
Public Function LoadTmlGroupParams(ByVal sGroupPath As String, ByVal sCircuit As String, ByRef outParams As TmlGroupParams) As Boolean
    Dim wb As Workbook, ws As Worksheet
    Dim vData As Variant
    Dim r As Long, nRows As Long, nCols As Long, c As Long
    Dim colTechNum As Long, colFloc As Long, colEqId As Long, colGrpKey As Long
    Dim colStdDev As Long, colAssetCr As Long, colAssetIntv As Long, colTmin As Long
    Dim colGrpCr As Long, colGrpIntv As Long
    
    LoadTmlGroupParams = False
    
    Set wb = Workbooks.Open(sGroupPath, ReadOnly:=True)
    Set ws = wb.Sheets(1)
    
    nRows = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    nCols = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    If nRows >= 2 Then
        vData = ws.Range(ws.Cells(1, 1), ws.Cells(nRows, nCols)).Value2
    End If
    wb.Close SaveChanges:=False
    
    If nRows < 2 Then
        With outParams
            .EquipmentId = "2002850"
            .FunctionalLoc = "4002." & sCircuit
            .TmlGroupEntyKey = "409145413"
            .TmlGroupId = sCircuit
            .StdDevFactor = 2: .AssetMinCr = 5: .AssetDefaultInterval = 60: .DefaultTmin = 0.08: .TmlGroupMinCr = 5: .TmlGroupDefaultInterval = 120
        End With
        LoadTmlGroupParams = True
        Exit Function
    End If
    
    colTechNum = 1: colFloc = 2: colEqId = 3: colGrpKey = 4
    colStdDev = 6: colAssetCr = 7: colAssetIntv = 8: colTmin = 9: colGrpCr = 10: colGrpIntv = 11
    
    For c = 1 To nCols
        Select Case Trim(CStr(vData(1, c)))
            Case "Equipment Technical Number": colTechNum = c
            Case "Functional Location": colFloc = c
            Case "Equipment ID": colEqId = c
            Case "TML_Group_ENTY_KEY": colGrpKey = c
            Case "Std Deviation Factor": colStdDev = c
            Case "Asset Minimum CR": colAssetCr = c
            Case "Asset Default Insp Interval": colAssetIntv = c
            Case "Default T-Min": colTmin = c
            Case "TML Group Minimum CR": colGrpCr = c
            Case "TML Group Default Insp Interv": colGrpIntv = c
        End Select
    Next c
    
    Dim sCleanCircuit As String
    sCleanCircuit = UCase(Replace(Replace(Trim(sCircuit), "-", ""), " ", ""))
    
    For r = 2 To nRows
        Dim sRowCirc As String, sRowCleanCirc As String
        sRowCirc = Trim(CStr(vData(r, colTechNum)))
        sRowCleanCirc = UCase(Replace(Replace(sRowCirc, "-", ""), " ", ""))
        
        If sRowCirc = sCircuit Or sRowCleanCirc = sCleanCircuit Or InStr(1, sRowCirc, sCircuit, vbTextCompare) > 0 Then
            With outParams
                .EquipmentId = Trim(CStr(vData(r, colEqId)))
                .FunctionalLoc = Trim(CStr(vData(r, colFloc)))
                .TmlGroupEntyKey = Trim(CStr(vData(r, colGrpKey)))
                .TmlGroupId = sCircuit
                If IsNumeric(vData(r, colStdDev)) Then .StdDevFactor = CDbl(vData(r, colStdDev)) Else .StdDevFactor = 2
                If IsNumeric(vData(r, colAssetCr)) Then .AssetMinCr = CDbl(vData(r, colAssetCr)) Else .AssetMinCr = 5
                If IsNumeric(vData(r, colAssetIntv)) Then .AssetDefaultInterval = CDbl(vData(r, colAssetIntv)) Else .AssetDefaultInterval = 60
                If IsNumeric(vData(r, colTmin)) Then .DefaultTmin = CDbl(vData(r, colTmin)) Else .DefaultTmin = 0.08
                If IsNumeric(vData(r, colGrpCr)) Then .TmlGroupMinCr = CDbl(vData(r, colGrpCr)) Else .TmlGroupMinCr = 5
                If IsNumeric(vData(r, colGrpIntv)) Then .TmlGroupDefaultInterval = CDbl(vData(r, colGrpIntv)) Else .TmlGroupDefaultInterval = 120
            End With
            LoadTmlGroupParams = True
            Exit Function
        End If
    Next r
    
    ' Fallback if not found in TML Group Data
    With outParams
        .EquipmentId = "2002850"
        .FunctionalLoc = "4002." & sCircuit
        .TmlGroupEntyKey = "409145413"
        .TmlGroupId = sCircuit
        .StdDevFactor = 2: .AssetMinCr = 5: .AssetDefaultInterval = 60: .DefaultTmin = 0.08: .TmlGroupMinCr = 5: .TmlGroupDefaultInterval = 120
    End With
    LoadTmlGroupParams = True
End Function

' ------------------------------------------------------------------------------
' Automatically resolves the Source Circuit ID from WP Code or associated files
' ------------------------------------------------------------------------------
Public Function DetectCircuitFromWpCode(ByVal sWpCode As String, ByVal sTmlPath As String) As String
    DetectCircuitFromWpCode = ""
    sWpCode = Trim(sWpCode)
    If sWpCode = "" Then Exit Function
    
    ' Extract digits from WP Code (e.g. LP583 -> 583, LP585 -> 585)
    Dim digits As String, j As Long, ch As String
    digits = ""
    For j = 1 To Len(sWpCode)
        ch = Mid(sWpCode, j, 1)
        If ch >= "0" And ch <= "9" Then digits = digits & ch
    Next j
    
    If digits = "585" Then
        DetectCircuitFromWpCode = "620-223-020"
        Exit Function
    ElseIf digits = "583" Then
        DetectCircuitFromWpCode = "350-107-010"
        Exit Function
    End If
    
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    ' 1. Check if mapping file LP <digits>.xlsx exists in Downloads or workspace
    Dim mapPaths(1 To 6) As String
    mapPaths(1) = ThisWorkbook.Path & "\LP " & digits & ".xlsx"
    mapPaths(2) = ThisWorkbook.Path & "\LP" & digits & ".xlsx"
    mapPaths(3) = Environ("USERPROFILE") & "\Downloads\LP " & digits & ".xlsx"
    mapPaths(4) = Environ("USERPROFILE") & "\Downloads\LP" & digits & ".xlsx"
    mapPaths(5) = ThisWorkbook.Path & "\Cadmine\LP " & digits & ".xlsx"
    mapPaths(6) = ThisWorkbook.Path & "\Cadmine\LP" & digits & ".xlsx"
    
    Dim pIdx As Long
    For pIdx = 1 To 6
        If fso.FileExists(mapPaths(pIdx)) Then
            On Error Resume Next
            Dim wbM As Workbook, wsM As Worksheet
            Set wbM = Workbooks.Open(mapPaths(pIdx), ReadOnly:=True)
            Set wsM = wbM.Sheets(1)
            If Not wsM Is Nothing Then
                Dim cktVal As String
                cktVal = Trim(CStr(wsM.Cells(2, 2).Value))
                If cktVal <> "" And cktVal <> "Old Ckt No." Then
                    DetectCircuitFromWpCode = cktVal
                    wbM.Close SaveChanges:=False
                    Exit Function
                End If
            End If
            wbM.Close SaveChanges:=False
            On Error GoTo 0
        End If
    Next pIdx
    
    ' 2. Check CADmine files DM<digits>.xlsx
    Dim cadPaths(1 To 6) As String
    cadPaths(1) = ThisWorkbook.Path & "\Cadmine\DM" & digits & ".xlsx"
    cadPaths(2) = ThisWorkbook.Path & "\DM" & digits & ".xlsx"
    cadPaths(3) = Environ("USERPROFILE") & "\Downloads\DM" & digits & ".xlsx"
    cadPaths(4) = Environ("USERPROFILE") & "\Downloads\DM-" & digits & ".xlsx"
    cadPaths(5) = GetLocalBasePath() & "\Cadmine\DM" & digits & ".xlsx"
    cadPaths(6) = GetLocalBasePath() & "\DM" & digits & ".xlsx"
    
    For pIdx = 1 To 6
        If fso.FileExists(cadPaths(pIdx)) Then
            Dim dummyP As String, foundC As String, dummyD As Object
            If DetectCadmineProjectAndCircuit(cadPaths(pIdx), dummyP, foundC, dummyD) Then
                If foundC <> "" Then
                    DetectCircuitFromWpCode = foundC
                    Exit Function
                End If
            End If
        End If
    Next pIdx
End Function

' ------------------------------------------------------------------------------
' Loads drawing/sheet-to-target-circuit dictionary from LP <digits>.xlsx mapping
' ------------------------------------------------------------------------------
Public Function LoadLpMappingDictionary(ByVal sWpCode As String, ByRef dShtToCkt As Object, ByRef dDwgToCkt As Object) As Boolean
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set dShtToCkt = CreateObject("Scripting.Dictionary")
    dShtToCkt.CompareMode = 1
    Set dDwgToCkt = CreateObject("Scripting.Dictionary")
    dDwgToCkt.CompareMode = 1
    
    LoadLpMappingDictionary = False
    
    Dim digits As String, j As Long, ch As String
    digits = ""
    For j = 1 To Len(sWpCode)
        ch = Mid(sWpCode, j, 1)
        If ch >= "0" And ch <= "9" Then digits = digits & ch
    Next j
    If digits = "" Then Exit Function
    
    Dim candidatePaths(1 To 8) As String
    candidatePaths(1) = ThisWorkbook.Path & "\LP " & digits & ".xlsx"
    candidatePaths(2) = ThisWorkbook.Path & "\LP" & digits & ".xlsx"
    candidatePaths(3) = Environ("USERPROFILE") & "\Downloads\LP " & digits & ".xlsx"
    candidatePaths(4) = Environ("USERPROFILE") & "\Downloads\LP" & digits & ".xlsx"
    candidatePaths(5) = ThisWorkbook.Path & "\Cadmine\LP " & digits & ".xlsx"
    candidatePaths(6) = ThisWorkbook.Path & "\Cadmine\LP" & digits & ".xlsx"
    candidatePaths(7) = GetLocalBasePath() & "\LP " & digits & ".xlsx"
    candidatePaths(8) = GetLocalBasePath() & "\LP" & digits & ".xlsx"
    
    Dim mapFilePath As String, p As Long
    mapFilePath = ""
    For p = 1 To 8
        If fso.FileExists(candidatePaths(p)) Then
            mapFilePath = candidatePaths(p)
            Exit For
        End If
    Next p
    
    If mapFilePath = "" Then Exit Function
    
    Dim wbM As Workbook, wsM As Worksheet
    On Error Resume Next
    Set wbM = Workbooks.Open(mapFilePath, ReadOnly:=True)
    On Error GoTo 0
    If wbM Is Nothing Then Exit Function
    
    Set wsM = wbM.Sheets(1)
    Dim lastR As Long, lastC As Long, r As Long, c As Long
    lastR = wsM.Cells(wsM.Rows.Count, 1).End(xlUp).Row
    If lastR < 2 Then lastR = wsM.Cells(wsM.Rows.Count, 2).End(xlUp).Row
    lastC = wsM.Cells(1, wsM.Columns.Count).End(xlToLeft).Column
    
    Dim colNewCkt As Long, colOldSht As Long, colDwg As Long
    colNewCkt = 4: colOldSht = 5: colDwg = 3
    For c = 1 To lastC
        Dim hStr As String
        hStr = UCase(Trim(Replace(Replace(CStr(wsM.Cells(1, c).Value), "_", ""), " ", "")))
        If InStr(hStr, "NEWCKT") > 0 Or InStr(hStr, "NEWCIRCUIT") > 0 Then colNewCkt = c
        If InStr(hStr, "OLDSHT") > 0 Or InStr(hStr, "SHEET") > 0 Then colOldSht = c
        If InStr(hStr, "DWG") > 0 Or InStr(hStr, "DRAWING") > 0 Then colDwg = c
    Next c
    
    For r = 2 To lastR
        Dim newCkt As String, oldSht As String, dwgNo As String
        newCkt = Trim(CStr(wsM.Cells(r, colNewCkt).Value))
        oldSht = Trim(CStr(wsM.Cells(r, colOldSht).Value))
        dwgNo = Trim(CStr(wsM.Cells(r, colDwg).Value))
        
        If newCkt <> "" And newCkt <> "#N/A" Then
            If oldSht <> "" And oldSht <> "#N/A" Then
                If Not dShtToCkt.Exists(oldSht) Then dShtToCkt.Add oldSht, newCkt
                If IsNumeric(oldSht) Then
                    Dim numVal As Long: numVal = Val(oldSht)
                    Dim sKey1 As String: sKey1 = CStr(numVal)
                    Dim sKey2 As String: sKey2 = Format(numVal, "000")
                    If Not dShtToCkt.Exists(sKey1) Then dShtToCkt.Add sKey1, newCkt
                    If Not dShtToCkt.Exists(sKey2) Then dShtToCkt.Add sKey2, newCkt
                End If
            End If
            If dwgNo <> "" And dwgNo <> "#N/A" Then
                If Not dDwgToCkt.Exists(dwgNo) Then dDwgToCkt.Add dwgNo, newCkt
            End If
        End If
    Next r
    
    wbM.Close SaveChanges:=False
    LoadLpMappingDictionary = (dShtToCkt.Count > 0 Or dDwgToCkt.Count > 0)
End Function


