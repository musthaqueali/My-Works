Attribute VB_Name = "modGenerator_MoveRename"
Option Explicit

' ==============================================================================
' Module: modGenerator_MoveRename
' Purpose: Populates APM Family - TML Move_Rename loadsheet (Move_TML tab)
'          Strictly adheres to RTK TML Move_Rename Procedure 1.docx & Sample LP585.
' ==============================================================================

Public Function Generate_MoveRename_Loadsheet(ByVal sDestPath As String, ByRef tmls() As TMLRecord, ByVal tmlCount As Long, ByVal sBaseCircuit As String, ByVal sBaseGroupKey As String, ByRef arrCircuits() As String, ByVal nCircuits As Long) As Boolean
    Dim wb As Workbook, ws As Worksheet
    Dim vOut() As Variant
    Dim i As Long
    
    Generate_MoveRename_Loadsheet = False
    If tmlCount <= 0 Then Exit Function
    
    Set wb = Workbooks.Open(sDestPath)
    On Error Resume Next
    Set ws = wb.Sheets("Move_TML")
    On Error GoTo 0
    
    If ws Is Nothing Then
        wb.Close SaveChanges:=False
        Exit Function
    End If
    
    ' Clear old data rows and remove orange/template fill color completely
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    If lastRow >= 3 Then
        With ws.Range(ws.Cells(3, 1), ws.Cells(lastRow, 7))
            .ClearContents
            .Interior.Pattern = xlNone
            .Interior.ColorIndex = xlNone
        End With
    End If
    With ws.Range(ws.Cells(3, 1), ws.Cells(3, 7))
        .Interior.Pattern = xlNone
        .Interior.ColorIndex = xlNone
    End With
    
    ' Sort TML records:
    ' 1. By Circuit order (Base circuit e.g. 620-223-020, then 620-223-021, then 620-223-022, etc.)
    ' 2. By sequential number of New TML ID (001, 002, 003, ... regardless of UT or RT prefix)
    Dim p As Long, q As Long
    Dim tmpTml As TMLRecord
    Dim rankP As Long, rankQ As Long
    Dim numP As Long, numQ As Long
    
    For p = 1 To tmlCount - 1
        For q = p + 1 To tmlCount
            rankP = GetCircuitRank(tmls(p).TargetCircuit, arrCircuits, nCircuits)
            rankQ = GetCircuitRank(tmls(q).TargetCircuit, arrCircuits, nCircuits)
            
            If rankP > rankQ Then
                tmpTml = tmls(p): tmls(p) = tmls(q): tmls(q) = tmpTml
            ElseIf rankP = rankQ Then
                numP = ExtractSeqNum(tmls(p).NewTmlId)
                numQ = ExtractSeqNum(tmls(q).NewTmlId)
                If numP > numQ Then
                    tmpTml = tmls(p): tmls(p) = tmls(q): tmls(q) = tmpTml
                End If
            End If
        Next q
    Next p
    
    ReDim vOut(1 To tmlCount, 1 To 7)
    
    For i = 1 To tmlCount
        ' Destination TML Group ENTY_KEY:
        ' Base circuit uses existing APM TML Group Key; new circuits use "TBD" per procedure and sample
        If Trim(tmls(i).TargetCircuit) = Trim(sBaseCircuit) Then
            vOut(i, 1) = CStr(sBaseGroupKey)
        Else
            vOut(i, 1) = "TBD"
        End If
        
        ' TML ENTY_KEY (Text per approved format)
        vOut(i, 2) = CStr(tmls(i).EntyKey)
        
        ' New TML ID
        vOut(i, 3) = tmls(i).NewTmlId
        
        ' New TML Group ID (Target Circuit)
        vOut(i, 4) = tmls(i).TargetCircuit
        
        ' Status Indicator
        If tmls(i).StatusIndicator <> "" Then
            vOut(i, 5) = tmls(i).StatusIndicator
        Else
            vOut(i, 5) = "Active"
        End If
        
        ' FMLY_ID
        vOut(i, 6) = "MI Thickness Measurement Location"
        
        ' PRE_FMLY_ID
        vOut(i, 7) = "MI_TMLGROUP"
    Next i
    
    ' Ensure column formatting matches before writing (All text format per approved reference)
    ws.Columns("A:G").NumberFormat = "@"
    
    ' Bulk write to sheet and format as plain cells (no orange background)
    With ws.Range(ws.Cells(3, 1), ws.Cells(2 + tmlCount, 7))
        .Value = vOut
        .Interior.Pattern = xlNone
        .Interior.ColorIndex = xlNone
        .Font.ColorIndex = xlAutomatic
        .Font.Bold = False
    End With
    
    ' If there were leftover rows beyond 2 + tmlCount, delete them cleanly
    If lastRow > 2 + tmlCount Then
        ws.Range(ws.Cells(3 + tmlCount, 1), ws.Cells(lastRow, 7)).EntireRow.Delete
    End If
    
    wb.Save
    wb.Close SaveChanges:=True
    Generate_MoveRename_Loadsheet = True
End Function

Private Function GetCircuitRank(ByVal sCircuit As String, ByRef arrCircuits() As String, ByVal nCircuits As Long) As Long
    Dim k As Long
    sCircuit = Trim(sCircuit)
    For k = 1 To nCircuits
        If StrComp(Trim(arrCircuits(k)), sCircuit, vbTextCompare) = 0 Then
            GetCircuitRank = k
            Exit Function
        End If
    Next k
    GetCircuitRank = 999999
End Function

Private Function ExtractSeqNum(ByVal sId As String) As Long
    Dim dotPos As Long
    sId = Trim(sId)
    dotPos = InStrRev(sId, ".")
    If dotPos > 0 Then
        ExtractSeqNum = Val(Mid(sId, dotPos + 1))
    Else
        Dim j As Long, numStr As String
        numStr = ""
        For j = Len(sId) To 1 Step -1
            Dim ch As String
            ch = Mid(sId, j, 1)
            If ch >= "0" And ch <= "9" Then
                numStr = ch & numStr
            Else
                Exit For
            End If
        Next j
        If numStr <> "" Then
            ExtractSeqNum = Val(numStr)
        Else
            ExtractSeqNum = 0
        End If
    End If
End Function
