Option Explicit

Sub Interactive_XLookup()
    Dim wsLookup As Worksheet, wsSearch As Worksheet, wsReturn As Worksheet, wsDest As Worksheet
    Dim rngLookup As Range, rngSearch As Range, rngReturn As Range, rngDest As Range
    Dim startRowLookup As Long, endRowLookup As Long, numRows As Long
    Dim maxSearchRow As Long, maxReturnRow As Long
    Dim dict As Object, r As Long, sKey As String, numStr As String
    Dim lookupVals As Variant, searchVals As Variant
    Dim ar As Range, col As Range, colNum As Long, outCol As Long
    Dim colVals As Variant, outVals() As Variant, matchRow As Long
    Dim startCell As Range

    ' ----------------------------------------------------
    ' Step 1: Select PRIMARY KEY in Current Sheet
    ' ----------------------------------------------------
    On Error Resume Next
    Set rngLookup = Application.InputBox( _
        "Step 1: Select the PRIMARY KEY column in this sheet:" & vbCrLf & _
        "• Click column header (e.g. Column C)" & vbCrLf & _
        "• Or select data cells (e.g. C2:C300)", _
        "Step 1: Primary Key", Type:=8)
    On Error GoTo 0

    If rngLookup Is Nothing Then Exit Sub
    Set wsLookup = rngLookup.Worksheet

    ' Auto-detect data bounds (handles C:C, C1:C300, or C2:C300)
    If rngLookup.Rows.Count > 10000 Then
        startRowLookup = 2
        endRowLookup = wsLookup.Cells(wsLookup.Rows.Count, rngLookup.Column).End(xlUp).Row
        If endRowLookup < 2 Then endRowLookup = 2
    ElseIf rngLookup.Row = 1 And rngLookup.Rows.Count > 1 Then
        startRowLookup = 2
        endRowLookup = rngLookup.Row + rngLookup.Rows.Count - 1
    Else
        startRowLookup = rngLookup.Row
        endRowLookup = rngLookup.Row + rngLookup.Rows.Count - 1
    End If

    numRows = endRowLookup - startRowLookup + 1
    lookupVals = wsLookup.Range(wsLookup.Cells(startRowLookup, rngLookup.Column), _
                                wsLookup.Cells(endRowLookup, rngLookup.Column)).Value2

    ' ----------------------------------------------------
    ' Step 2: Select PRIMARY KEY in Master Sheet / Other File
    ' ----------------------------------------------------
    On Error Resume Next
    Set rngSearch = Application.InputBox( _
        "Step 2: Select matching PRIMARY KEY column in Master sheet / other file:" & vbCrLf & _
        "• Click across to the Master sheet or side-by-side window" & vbCrLf & _
        "• Click the primary key column (e.g. Column A)", _
        "Step 2: Master Primary Key", Type:=8)
    On Error GoTo 0

    If rngSearch Is Nothing Then Exit Sub
    Set wsSearch = rngSearch.Worksheet

    If rngSearch.Rows.Count > 10000 Then
        maxSearchRow = wsSearch.Cells(wsSearch.Rows.Count, rngSearch.Column).End(xlUp).Row
    Else
        maxSearchRow = rngSearch.Row + rngSearch.Rows.Count - 1
    End If
    If maxSearchRow < 2 Then maxSearchRow = 2

    searchVals = wsSearch.Range(wsSearch.Cells(1, rngSearch.Column), _
                                wsSearch.Cells(maxSearchRow, rngSearch.Column)).Value2

    ' Build dictionary mapping Key -> Exact Sheet Row (handles numbers & text formats)
    Set dict = CreateObject("Scripting.Dictionary")
    dict.CompareMode = 1

    For r = 1 To maxSearchRow
        sKey = Trim(CStr(searchVals(r, 1)))
        sKey = Replace(sKey, Chr(160), " ")
        sKey = Trim(sKey)
        If sKey <> "" Then
            If Not dict.Exists(sKey) Then dict.Add sKey, r
            If IsNumeric(sKey) Then
                numStr = CStr(Val(sKey))
                If Not dict.Exists(numStr) Then dict.Add numStr, r
            End If
        End If
    Next r

    ' ----------------------------------------------------
    ' Step 3: Select RETURN Column(s)
    ' ----------------------------------------------------
    On Error Resume Next
    Set rngReturn = Application.InputBox( _
        "Step 3: Select RETURN column(s) in Master sheet / other file:" & vbCrLf & _
        "• Click & drag across adjacent columns (e.g. B:C)" & vbCrLf & _
        "• OR hold CTRL to select separated columns (e.g. B:B, E:E)", _
        "Step 3: Return Columns", Type:=8)
    On Error GoTo 0

    If rngReturn Is Nothing Then Exit Sub
    Set wsReturn = rngReturn.Worksheet

    ' ----------------------------------------------------
    ' Step 4: Select Destination Cell
    ' ----------------------------------------------------
    On Error Resume Next
    Set rngDest = Application.InputBox( _
        "Step 4: Select the FIRST destination cell in your sheet (e.g. D2):", _
        "Step 4: Destination Cell", Type:=8)
    On Error GoTo 0

    If rngDest Is Nothing Then Exit Sub
    Set wsDest = rngDest.Worksheet

    Set startCell = rngDest.Cells(1, 1)
    If startCell.Row = 1 And startRowLookup = 2 Then
        Set startCell = wsDest.Cells(2, startCell.Column)
    End If

    maxReturnRow = wsReturn.Cells.SpecialCells(xlCellTypeLastCell).Row
    If maxReturnRow < maxSearchRow Then maxReturnRow = maxSearchRow

    ' ----------------------------------------------------
    ' In-Memory Population
    ' ----------------------------------------------------
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual

    outCol = 0
    For Each ar In rngReturn.Areas
        For Each col In ar.Columns
            colNum = col.Column
            colVals = wsReturn.Range(wsReturn.Cells(1, colNum), _
                                     wsReturn.Cells(maxReturnRow, colNum)).Value2

            ReDim outVals(1 To numRows, 1 To 1)

            For r = 1 To numRows
                sKey = Trim(CStr(lookupVals(r, 1)))
                sKey = Replace(sKey, Chr(160), " ")
                sKey = Trim(sKey)

                matchRow = 0
                If dict.Exists(sKey) Then
                    matchRow = dict(sKey)
                ElseIf IsNumeric(sKey) Then
                    numStr = CStr(Val(sKey))
                    If dict.Exists(numStr) Then matchRow = dict(numStr)
                End If

                If matchRow > 0 And matchRow <= maxReturnRow Then
                    outVals(r, 1) = colVals(matchRow, 1)
                Else
                    outVals(r, 1) = ""
                End If
            Next r

            wsDest.Range(startCell.Offset(0, outCol), _
                         startCell.Offset(numRows - 1, outCol)).Value = outVals
            outCol = outCol + 1
        Next col
    Next ar

    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
End Sub

