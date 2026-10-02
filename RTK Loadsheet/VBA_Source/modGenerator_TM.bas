Attribute VB_Name = "modGenerator_TM"
Option Explicit

' ==============================================================================
' Module: modGenerator_TM
' Purpose: Populates TM New Loadsheet (Assets, TML_Group, Asset_CAS, TML_Group_CAS)
'          Strictly adheres to RTK TM Loadsheet Creation Procedure 9.12.2025 1.docx
' ==============================================================================

Public Function Generate_TM_Loadsheet(ByVal sDestPath As String, ByRef tmlParams As TmlGroupParams, ByRef arrTargetCircuits() As String, ByVal nCircuits As Long, ByVal sBaseCircuit As String) As Boolean
    Dim wb As Workbook
    Dim wsAssets As Worksheet, wsGrp As Worksheet, wsAssetCas As Worksheet, wsGrpCas As Worksheet
    Dim wsTml As Worksheet, wsTmlCas As Worksheet, wsMeas As Worksheet
    Dim i As Long, rowIdx As Long
    Dim sEqId As String, sCircuit As String
    
    Generate_TM_Loadsheet = False
    If nCircuits <= 0 Then Exit Function
    
    Set wb = Workbooks.Open(sDestPath)
    Set wsAssets = wb.Sheets("Assets")
    Set wsGrp = wb.Sheets("TML_Group")
    Set wsAssetCas = wb.Sheets("Asset_CAS")
    Set wsGrpCas = wb.Sheets("TML_Group_CAS")
    
    On Error Resume Next
    Set wsTml = wb.Sheets("TML")
    Set wsTmlCas = wb.Sheets("TML_CAS")
    Set wsMeas = wb.Sheets("Measurements")
    On Error GoTo 0
    
    ' Clear old data starting row 3
    ClearDataRows wsAssets, 3
    ClearDataRows wsGrp, 7
    ClearDataRows wsAssetCas, 26
    ClearDataRows wsGrpCas, 27
    If Not wsTml Is Nothing Then ClearDataRows wsTml, 64: TrimExtraRows wsTml, 2
    If Not wsTmlCas Is Nothing Then ClearDataRows wsTmlCas, 11: TrimExtraRows wsTmlCas, 2
    If Not wsMeas Is Nothing Then ClearDataRows wsMeas, 7: TrimExtraRows wsMeas, 2
    
    ' --- 1. Assets Sheet ---
    Dim vAssets() As Variant
    ReDim vAssets(1 To nCircuits, 1 To 3)
    For i = 1 To nCircuits
        sCircuit = arrTargetCircuits(i)
        If Trim(sCircuit) = Trim(sBaseCircuit) Then
            sEqId = FormatEquipmentId(tmlParams.EquipmentId)
        Else
            sEqId = "TBD-EQ-" & CStr(i)
        End If
        vAssets(i, 1) = sEqId
        vAssets(i, 2) = "ECP-500"
        vAssets(i, 3) = sCircuit
    Next i
    wsAssets.Columns("A:A").NumberFormat = "@"
    wsAssets.Range(wsAssets.Cells(3, 1), wsAssets.Cells(2 + nCircuits, 3)).Value = vAssets
    TrimExtraRows wsAssets, 2 + nCircuits
    
    ' --- 2. TML_Group Sheet ---
    Dim vGrp() As Variant
    ReDim vGrp(1 To nCircuits, 1 To 7)
    For i = 1 To nCircuits
        sCircuit = arrTargetCircuits(i)
        If Trim(sCircuit) = Trim(sBaseCircuit) Then
            sEqId = FormatEquipmentId(tmlParams.EquipmentId)
        Else
            sEqId = "TBD-EQ-" & CStr(i)
        End If
        vGrp(i, 1) = sEqId
        vGrp(i, 2) = "ECP-500"
        vGrp(i, 3) = sCircuit
        vGrp(i, 4) = sCircuit
        vGrp(i, 5) = Empty
        vGrp(i, 6) = "PIPE"
        vGrp(i, 7) = Empty
    Next i
    wsGrp.Columns("A:A").NumberFormat = "@"
    wsGrp.Range(wsGrp.Cells(3, 1), wsGrp.Cells(2 + nCircuits, 7)).Value = vGrp
    TrimExtraRows wsGrp, 2 + nCircuits
    
    ' --- 3. Asset_CAS Sheet (2 rows per circuit: UT and RT) ---
    Dim totalCasRows As Long
    totalCasRows = nCircuits * 2
    Dim vAssetCas() As Variant
    ReDim vAssetCas(1 To totalCasRows, 1 To 26)
    
    rowIdx = 0
    For i = 1 To nCircuits
        sCircuit = arrTargetCircuits(i)
        If Trim(sCircuit) = Trim(sBaseCircuit) Then
            sEqId = FormatEquipmentId(tmlParams.EquipmentId)
        Else
            sEqId = "TBD-EQ-" & CStr(i)
        End If
        
        ' UT row
        rowIdx = rowIdx + 1
        PopulateCasRow vAssetCas, rowIdx, sEqId, sCircuit, "UT", tmlParams
        
        ' RT row
        rowIdx = rowIdx + 1
        PopulateCasRow vAssetCas, rowIdx, sEqId, sCircuit, "RT", tmlParams
    Next i
    wsAssetCas.Columns("A:A").NumberFormat = "@"
    wsAssetCas.Range(wsAssetCas.Cells(3, 1), wsAssetCas.Cells(2 + totalCasRows, 26)).Value = vAssetCas
    TrimExtraRows wsAssetCas, 2 + totalCasRows
    
    ' --- 4. TML_Group_CAS Sheet (2 rows per circuit: UT and RT) ---
    Dim vGrpCas() As Variant
    ReDim vGrpCas(1 To totalCasRows, 1 To 27)
    
    rowIdx = 0
    For i = 1 To nCircuits
        sCircuit = arrTargetCircuits(i)
        If Trim(sCircuit) = Trim(sBaseCircuit) Then
            sEqId = FormatEquipmentId(tmlParams.EquipmentId)
        Else
            sEqId = "TBD-EQ-" & CStr(i)
        End If
        
        ' UT row
        rowIdx = rowIdx + 1
        PopulateGrpCasRow vGrpCas, rowIdx, sEqId, sCircuit, "UT", tmlParams
        
        ' RT row
        rowIdx = rowIdx + 1
        PopulateGrpCasRow vGrpCas, rowIdx, sEqId, sCircuit, "RT", tmlParams
    Next i
    wsGrpCas.Columns("A:A").NumberFormat = "@"
    wsGrpCas.Range(wsGrpCas.Cells(3, 1), wsGrpCas.Cells(2 + totalCasRows, 27)).Value = vGrpCas
    TrimExtraRows wsGrpCas, 2 + totalCasRows
    
    wb.Save
    wb.Close SaveChanges:=True
    Generate_TM_Loadsheet = True
End Function

Private Sub ClearDataRows(ByVal ws As Worksheet, ByVal numCols As Long)
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    If lastRow >= 3 Then
        ws.Range(ws.Cells(3, 1), ws.Cells(lastRow, numCols)).ClearContents
    End If
End Sub

Private Sub TrimExtraRows(ByVal ws As Worksheet, ByVal lastKeepRow As Long)
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    If lastRow > lastKeepRow Then
        ws.Range(ws.Cells(lastKeepRow + 1, 1), ws.Cells(lastRow, 1)).EntireRow.Delete
    End If
End Sub

Private Function FormatEquipmentId(ByVal sId As String) As String
    sId = Trim(sId)
    If sId = "" Then
        FormatEquipmentId = ""
        Exit Function
    End If
    If IsNumeric(sId) And Len(sId) < 18 Then
        FormatEquipmentId = String(18 - Len(sId), "0") & sId
    Else
        FormatEquipmentId = sId
    End If
End Function

Private Sub PopulateCasRow(ByRef v() As Variant, ByVal r As Long, ByVal sEqId As String, ByVal sCircuit As String, ByVal sInspType As String, ByRef p As TmlGroupParams)
    v(r, 1) = sEqId
    v(r, 2) = "ECP-500"
    v(r, 3) = sCircuit
    v(r, 4) = sInspType
    v(r, 5) = "Maximum"
    v(r, 6) = Empty
    v(r, 7) = Empty
    v(r, 8) = Empty
    v(r, 9) = Empty
    v(r, 10) = Empty
    v(r, 11) = "2"
    v(r, 12) = "1"
    v(r, 13) = False
    v(r, 14) = "TRUE"
    v(r, 15) = "TRUE"
    v(r, 16) = "FALSE"
    v(r, 17) = "FALSE"
    v(r, 18) = p.AssetDefaultInterval
    v(r, 19) = "TRUE"
    v(r, 20) = "TRUE"
    v(r, 21) = p.DefaultTmin
    v(r, 22) = p.AssetMinCr
    v(r, 23) = "TRUE"
    v(r, 24) = 0.5
    v(r, 25) = 0
    v(r, 26) = 0
End Sub

Private Sub PopulateGrpCasRow(ByRef v() As Variant, ByVal r As Long, ByVal sEqId As String, ByVal sCircuit As String, ByVal sInspType As String, ByRef p As TmlGroupParams)
    v(r, 1) = sEqId
    v(r, 2) = "ECP-500"
    v(r, 3) = sCircuit
    v(r, 4) = sInspType
    v(r, 5) = sCircuit ' TML Group ID
    v(r, 6) = "Maximum"
    v(r, 7) = Empty
    v(r, 8) = Empty
    v(r, 9) = Empty
    v(r, 10) = Empty
    v(r, 11) = Empty
    v(r, 12) = "2"
    v(r, 13) = "1"
    v(r, 14) = "FALSE"
    v(r, 15) = "TRUE"
    v(r, 16) = "TRUE"
    v(r, 17) = "FALSE"
    v(r, 18) = "FALSE"
    v(r, 19) = p.AssetDefaultInterval
    v(r, 20) = "TRUE"
    v(r, 21) = "TRUE"
    v(r, 22) = p.DefaultTmin
    v(r, 23) = p.AssetMinCr
    v(r, 24) = "TRUE"
    v(r, 25) = 0.5
    v(r, 26) = 0
    v(r, 27) = 0
End Sub
