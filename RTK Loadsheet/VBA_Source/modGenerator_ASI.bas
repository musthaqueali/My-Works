Attribute VB_Name = "modGenerator_ASI"
Option Explicit

' ==============================================================================
' Module: modGenerator_ASI
' Purpose: Populates RTK ASI Loadsheet Template v2 (Data starts at Row 2)
'          Strictly adheres to RTK ASI Loading Procedure 1.docx & Sample LP585.
' ==============================================================================

Public Function Generate_ASI_Loadsheet(ByVal sDestPath As String, ByRef asiOps() As AsiOpRecord, ByVal nOps As Long, ByRef arrTargetCircuits() As String, ByVal nCircuits As Long, ByVal sBaseCircuit As String, ByVal sBaseStrategyId As String) As Boolean
    Dim wb As Workbook
    Dim wsActv As Worksheet, wsPkg As Worksheet, wsPrt As Worksheet, wsMat As Worksheet, wsImp As Worksheet
    Dim i As Long, j As Long, rowIdx As Long
    Dim sStratId As String, sCircuit As String
    
    Generate_ASI_Loadsheet = False
    If nCircuits <= 0 Or nOps <= 0 Then Exit Function
    
    Set wb = Workbooks.Open(sDestPath)
    Set wsActv = wb.Sheets("StrategyActivation")
    Set wsPkg = wb.Sheets("PackageStrategies")
    Set wsPrt = wb.Sheets("OperationPRTs")
    Set wsMat = wb.Sheets("OperationMaterials")
    Set wsImp = wb.Sheets("ImplementPackages")
    
    ' Clear old data rows from Row 2 downwards
    ClearSheetData wsActv, 1, 2
    ClearSheetData wsPkg, 45, 2
    ClearSheetData wsPrt, 11, 2
    ClearSheetData wsMat, 6, 2
    ClearSheetData wsImp, 1, 2
    
    ' --- 1. StrategyActivation Sheet (Data starts Row 2) ---
    Dim vActv() As Variant
    ReDim vActv(1 To nCircuits, 1 To 1)
    For i = 1 To nCircuits
        If Trim(arrTargetCircuits(i)) = Trim(sBaseCircuit) Then
            vActv(i, 1) = sBaseStrategyId
        Else
            vActv(i, 1) = "TBD-" & CStr(i)
        End If
    Next i
    wsActv.Range(wsActv.Cells(2, 1), wsActv.Cells(1 + nCircuits, 1)).Value = vActv
    TrimExtraRows wsActv, 1 + nCircuits
    
    ' --- 2. PackageStrategies Sheet (Data starts Row 2) ---
    Dim totalRows As Long
    totalRows = nCircuits * nOps
    Dim vPkg() As Variant
    ReDim vPkg(1 To totalRows, 1 To 45)
    
    rowIdx = 0
    For i = 1 To nCircuits
        sCircuit = arrTargetCircuits(i)
        If Trim(sCircuit) = Trim(sBaseCircuit) Then
            sStratId = sBaseStrategyId
        Else
            sStratId = "TBD-" & CStr(i)
        End If
        
        For j = 1 To nOps
            rowIdx = rowIdx + 1
            
            ' Strategy Info
            vPkg(rowIdx, 1) = sStratId
            vPkg(rowIdx, 2) = asiOps(j).ActionId
            vPkg(rowIdx, 3) = sStratId
            vPkg(rowIdx, 4) = asiOps(j).ImplementationType
            
            ' Date formatting (dd/mm/yyyy string)
            Dim sDt As String
            If IsDate(asiOps(j).StartDate) Then
                sDt = Format(CDate(asiOps(j).StartDate), "dd\/mm\/yyyy")
            Else
                sDt = CStr(asiOps(j).StartDate)
            End If
            
            ' Descriptions with standard 60 month subsequent frequency
            Dim sMpDesc As String, sItmDesc As String, sTlDesc As String, sOpDesc As String
            sMpDesc = Replace(asiOps(j).MpLongDesc, "SUBSEQUENT FREQUENCY: 120", "SUBSEQUENT FREQUENCY: 60")
            sItmDesc = Replace(asiOps(j).ItemLongDesc, "SUBSEQUENT FREQUENCY: 120", "SUBSEQUENT FREQUENCY: 60")
            sTlDesc = Replace(asiOps(j).TaskListLongDesc, "SUBSEQUENT FREQUENCY: 120", "SUBSEQUENT FREQUENCY: 60")
            sOpDesc = Replace(asiOps(j).OperationLongDesc, "SUBSEQUENT FREQUENCY: 120", "SUBSEQUENT FREQUENCY: 60")
            
            ' Maintenance Plan (Column J: Includes Circuit Name as in snap/procedure)
            vPkg(rowIdx, 5) = asiOps(j).AuthGroup
            vPkg(rowIdx, 6) = asiOps(j).SortField
            vPkg(rowIdx, 7) = asiOps(j).Category
            vPkg(rowIdx, 8) = 95 ' Standard RTK Call Horizon for all piping tactics
            vPkg(rowIdx, 9) = sDt
            vPkg(rowIdx, 10) = asiOps(j).ImplementationType & " " & sCircuit
            vPkg(rowIdx, 11) = sMpDesc
            
            ' Maintenance Item (Column S: Includes Circuit Name as in snap/procedure)
            vPkg(rowIdx, 12) = asiOps(j).PlanPlant
            vPkg(rowIdx, 13) = asiOps(j).PlanGroup
            vPkg(rowIdx, 14) = asiOps(j).WorkCenter
            vPkg(rowIdx, 15) = asiOps(j).WorkCenterPlant
            vPkg(rowIdx, 16) = asiOps(j).ActivityType
            vPkg(rowIdx, 17) = asiOps(j).Category
            vPkg(rowIdx, 18) = asiOps(j).Priority
            vPkg(rowIdx, 19) = asiOps(j).ImplementationType & " " & sCircuit
            vPkg(rowIdx, 20) = sItmDesc
            
            ' Task List (References Base Circuit)
            vPkg(rowIdx, 21) = asiOps(j).ImplementationType & " " & sBaseCircuit
            vPkg(rowIdx, 22) = sTlDesc
            vPkg(rowIdx, 23) = asiOps(j).WorkCenter
            vPkg(rowIdx, 24) = asiOps(j).PlanPlant
            vPkg(rowIdx, 25) = asiOps(j).WorkCenterPlant
            vPkg(rowIdx, 26) = asiOps(j).PlanGroup
            vPkg(rowIdx, 27) = "01"
            If Trim(asiOps(j).TaskListAssembly) <> "" Then
                vPkg(rowIdx, 28) = Right("000000000000000000" & Trim(asiOps(j).TaskListAssembly), 18)
            Else
                vPkg(rowIdx, 28) = Empty
            End If
            vPkg(rowIdx, 29) = asiOps(j).TaskListCondition
            
            ' Operation
            vPkg(rowIdx, 30) = "0010"
            vPkg(rowIdx, 31) = "0001 INSPECTION"
            vPkg(rowIdx, 32) = asiOps(j).ImplementationType & " " & sBaseCircuit
            vPkg(rowIdx, 33) = sOpDesc
            vPkg(rowIdx, 34) = asiOps(j).WorkCenter
            vPkg(rowIdx, 35) = asiOps(j).PlanPlant
            vPkg(rowIdx, 36) = asiOps(j).OperationControlKey
            vPkg(rowIdx, 37) = asiOps(j).OperationCondition
            vPkg(rowIdx, 38) = asiOps(j).OperationWork
            vPkg(rowIdx, 39) = asiOps(j).OperationWorkUnit
            vPkg(rowIdx, 40) = asiOps(j).OperationActivityType
            vPkg(rowIdx, 41) = asiOps(j).OperationResourceCount
            vPkg(rowIdx, 42) = asiOps(j).OperationDuration
            vPkg(rowIdx, 43) = asiOps(j).OperationDurationUnit
            vPkg(rowIdx, 44) = asiOps(j).UserField10
            vPkg(rowIdx, 45) = asiOps(j).UserField11
        Next j
    Next i
    
    wsPkg.Cells(1, 1).Value = "Strategy ID - ASM"
    wsPkg.Cells(1, 2).Value = "Action ID-ASM"
    wsPkg.Cells(1, 3).Value = "Package ID - ASI"
    wsPkg.Columns("I:I").NumberFormat = "@"
    wsPkg.Columns("AA:AA").NumberFormat = "@"
    wsPkg.Columns("AB:AB").NumberFormat = "@"
    wsPkg.Columns("AD:AD").NumberFormat = "@"
    wsPkg.Range(wsPkg.Cells(2, 1), wsPkg.Cells(1 + totalRows, 45)).Value = vPkg
    TrimExtraRows wsPkg, 1 + totalRows
    
    ' --- 3. OperationPRTs Sheet (Data starts Row 2) ---
    Dim vPrt() As Variant
    ReDim vPrt(1 To totalRows, 1 To 11)
    
    rowIdx = 0
    For i = 1 To nCircuits
        If Trim(arrTargetCircuits(i)) = Trim(sBaseCircuit) Then
            sStratId = sBaseStrategyId
        Else
            sStratId = "TBD-" & CStr(i)
        End If
        
        For j = 1 To nOps
            rowIdx = rowIdx + 1
            vPrt(rowIdx, 1) = sStratId
            vPrt(rowIdx, 2) = asiOps(j).ActionId
            If asiOps(j).ActionId = "ACTION-003" Then
                vPrt(rowIdx, 3) = "0010"
            Else
                vPrt(rowIdx, 3) = "0020"
            End If
            vPrt(rowIdx, 4) = 1
            vPrt(rowIdx, 5) = asiOps(j).PrtDoc
            vPrt(rowIdx, 6) = asiOps(j).PrtType
            vPrt(rowIdx, 7) = asiOps(j).PrtPart
            vPrt(rowIdx, 8) = asiOps(j).PrtVersion
            vPrt(rowIdx, 9) = asiOps(j).PrtQty
            vPrt(rowIdx, 10) = asiOps(j).PrtQtyUnit
            vPrt(rowIdx, 11) = "1"
        Next j
    Next i
    
    ' Format text columns so leading zeros in PRT doc, Part 000, Version 00, Op ID are strictly preserved
    wsPrt.Columns("C:C").NumberFormat = "@"
    wsPrt.Columns("E:E").NumberFormat = "@"
    wsPrt.Columns("G:H").NumberFormat = "@"
    wsPrt.Columns("K:K").NumberFormat = "@"
    wsPrt.Range(wsPrt.Cells(2, 1), wsPrt.Cells(1 + totalRows, 11)).Value = vPrt
    TrimExtraRows wsPrt, 1 + totalRows
    
    ' --- 4. OperationMaterials Sheet (Data starts Row 2) ---
    Dim vMat() As Variant
    ReDim vMat(1 To totalRows, 1 To 6)
    
    rowIdx = 0
    For i = 1 To nCircuits
        If Trim(arrTargetCircuits(i)) = Trim(sBaseCircuit) Then
            sStratId = sBaseStrategyId
        Else
            sStratId = "TBD-" & CStr(i)
        End If
        
        For j = 1 To nOps
            rowIdx = rowIdx + 1
            vMat(rowIdx, 1) = sStratId
            vMat(rowIdx, 2) = asiOps(j).ActionId
            If asiOps(j).ActionId = "ACTION-003" Then
                vMat(rowIdx, 3) = "0010"
            Else
                vMat(rowIdx, 3) = "0020"
            End If
            vMat(rowIdx, 4) = Empty
            vMat(rowIdx, 5) = 1
            vMat(rowIdx, 6) = "EA"
        Next j
    Next i
    
    wsMat.Columns("C:C").NumberFormat = "@"
    wsMat.Range(wsMat.Cells(2, 1), wsMat.Cells(1 + totalRows, 6)).Value = vMat
    TrimExtraRows wsMat, 1 + totalRows
    
    ' --- 5. ImplementPackages Sheet (Data starts Row 2) ---
    wsImp.Range(wsImp.Cells(2, 1), wsImp.Cells(1 + nCircuits, 1)).Value = vActv
    TrimExtraRows wsImp, 1 + nCircuits
    
    wb.Save
    wb.Close SaveChanges:=True
    Generate_ASI_Loadsheet = True
End Function

Private Sub ClearSheetData(ByVal ws As Worksheet, ByVal numCols As Long, ByVal startRow As Long)
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    If lastRow >= startRow Then
        ws.Range(ws.Cells(startRow, 1), ws.Cells(lastRow, numCols)).ClearContents
    End If
End Sub

Private Sub TrimExtraRows(ByVal ws As Worksheet, ByVal lastKeepRow As Long)
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    If lastRow > lastKeepRow Then
        ws.Range(ws.Cells(lastKeepRow + 1, 1), ws.Cells(lastRow, 1)).EntireRow.Delete
    End If
End Sub
