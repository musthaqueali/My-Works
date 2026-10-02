Attribute VB_Name = "modMainOrchestrator"
Option Explicit

' ==============================================================================
' Module: modMainOrchestrator
' Purpose: Master workflow controller, orchestrates data extraction and template writing.
'          Universally supports ANY LP piping CADmine file and APM master exports.
' ==============================================================================

Public Sub LoadTMLMapping()
    Dim wsCtrl As Worksheet, wsMap As Worksheet
    Dim sTmlPath As String, sCadPath As String, sCircuit As String, sProjCode As String
    Dim tmls() As TMLRecord
    Dim tmlCount As Long, i As Long
    
    Set wsCtrl = ThisWorkbook.Sheets("Control Panel")
    Set wsMap = ThisWorkbook.Sheets("Circuit_Mapping")
    
    sTmlPath = Trim(wsCtrl.Range("D9").Value)
    sCadPath = Trim(wsCtrl.Range("D11").Value)
    sProjCode = Trim(wsCtrl.Range("D15").Value)
    sCircuit = Trim(wsCtrl.Range("D16").Value)
    
    ' 1. Auto-detect Circuit from WP Code (No need for user to enter circuit manually)
    If sCircuit = "" And sProjCode <> "" Then
        sCircuit = DetectCircuitFromWpCode(sProjCode, sTmlPath)
        If sCircuit <> "" Then
            wsCtrl.Range("D16").Value = sCircuit
        End If
    End If
    
    ' 2. Auto-detect project code and circuit from CADmine if still missing
    If sCadPath <> "" And SafeFileExists(sCadPath) Then
        Dim autoProj As String, autoCirc As String, dDwg As Object
        If DetectCadmineProjectAndCircuit(sCadPath, autoProj, autoCirc, dDwg) Then
            If sProjCode = "" And autoProj <> "" Then
                sProjCode = autoProj
                wsCtrl.Range("D15").Value = autoProj
            End If
            If sCircuit = "" And autoCirc <> "" Then
                sCircuit = autoCirc
                wsCtrl.Range("D16").Value = autoCirc
            End If
        End If
    End If
    
    If sTmlPath = "" Or Not SafeFileExists(sTmlPath) Then
        SafeMsgBox "Please select a valid TML Export file first!", vbExclamation, "File Missing"
        Exit Sub
    End If
    
    If sCircuit = "" Then
        SafeMsgBox "Could not automatically resolve Source Circuit ID from WP Code '" & sProjCode & "'." & vbCrLf & _
                   "Please enter it in cell D16 or select the CADmine file.", vbExclamation, "Circuit Missing"
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    Application.StatusBar = "Loading TML records..."
    
    ' 3. Extract TML records:
    ' Try CADmine first if provided
    If sCadPath <> "" And SafeFileExists(sCadPath) Then
        Application.StatusBar = "Extracting TMLs from CADmine: " & sCadPath & "..."
        tmlCount = LoadTMLsFromCadmine(sCadPath, sTmlPath, sCircuit, tmls)
    End If
    
    ' If CADmine has no CML points (e.g. DM583 has title block only) or no CADmine provided, extract directly from APM TML Export
    If tmlCount = 0 And sCircuit <> "" Then
        Application.StatusBar = "Extracting TMLs from APM Export for circuit " & sCircuit & "..."
        tmlCount = LoadTMLsForCircuit(sTmlPath, sCircuit, tmls)
    End If
    
    If tmlCount = 0 Then
        Application.ScreenUpdating = True
        Application.StatusBar = False
        SafeMsgBox "No TML records found for circuit '" & sCircuit & "' in CADmine or APM export.", vbInformation, "No Records"
        Exit Sub
    End If
    
    ' Clear existing mapping sheet data
    wsMap.Cells.Clear
    
    ' Setup Headers
    wsMap.Range("A1:I1").Value = Array("TML ENTY_KEY", "Current TML ID", "Analysis Type", "ISO Drawing Number", "Target Circuit / Group", "New TML ID", "Status Indicator", "Component Type", "Access")
    With wsMap.Range("A1:I1")
        .Font.Bold = True
        .Interior.Color = RGB(0, 51, 102) ' Rio Tinto Navy
        .Font.Color = RGB(255, 255, 255)
    End With
    
    Dim vOut() As Variant
    ReDim vOut(1 To tmlCount, 1 To 9)
    
    Dim isSampleCircuit As Boolean
    isSampleCircuit = (sCircuit = "620-223-020")
    
    ' Load external LP mapping dictionary if present (e.g. LP 583.xlsx)
    Dim dShtMap As Object, dDwgMap As Object
    Dim hasLpMap As Boolean
    hasLpMap = LoadLpMappingDictionary(sProjCode, dShtMap, dDwgMap)
    
    For i = 1 To tmlCount
        vOut(i, 1) = tmls(i).EntyKey
        vOut(i, 2) = tmls(i).TmlId
        vOut(i, 3) = tmls(i).AnalysisType
        vOut(i, 4) = tmls(i).IsoDrawing
        
        ' Target circuit assignment
        If isSampleCircuit Then
            Dim sIso As String
            sIso = Trim(tmls(i).IsoDrawing)
            If InStr(1, "620-M-983, 620-M-984, 620-M-985, 620-M-9004", sIso, vbTextCompare) > 0 Then
                vOut(i, 5) = "620-223-020"
            ElseIf InStr(1, "620-M-986, 620-M-987, 620-M-988, 620-M-989, 620-M-990, 620-M-991, 620-M-992, 620-M-993, 620-M-995", sIso, vbTextCompare) > 0 Then
                vOut(i, 5) = "620-223-021"
            Else
                vOut(i, 5) = "620-223-022"
            End If
        ElseIf hasLpMap Then
            Dim sTmlIso As String, matchedCkt As String
            sTmlIso = Trim(tmls(i).IsoDrawing)
            matchedCkt = ""
            
            ' 1. Check exact DWG or ISO match
            If dDwgMap.Exists(sTmlIso) Then
                matchedCkt = dDwgMap(sTmlIso)
            ElseIf dShtMap.Exists(sTmlIso) Then
                matchedCkt = dShtMap(sTmlIso)
            End If
            
            ' 2. Check SHT number (e.g. 350-107-010_SHT141 or SHT001)
            If matchedCkt = "" Then
                Dim posSht As Long
                posSht = InStr(1, sTmlIso, "SHT", vbTextCompare)
                If posSht > 0 Then
                    Dim rawSht As String, shtDig As String, mIdx As Long, chM As String
                    rawSht = Mid(sTmlIso, posSht + 3)
                    shtDig = ""
                    For mIdx = 1 To Len(rawSht)
                        chM = Mid(rawSht, mIdx, 1)
                        If chM >= "0" And chM <= "9" Then
                            shtDig = shtDig & chM
                        Else
                            Exit For
                        End If
                    Next mIdx
                    
                    If shtDig <> "" Then
                        If dShtMap.Exists(shtDig) Then
                            matchedCkt = dShtMap(shtDig)
                        ElseIf dShtMap.Exists(CStr(Val(shtDig))) Then
                            matchedCkt = dShtMap(CStr(Val(shtDig)))
                        ElseIf dShtMap.Exists(Format(Val(shtDig), "000")) Then
                            matchedCkt = dShtMap(Format(Val(shtDig), "000"))
                        End If
                    End If
                End If
            End If
            
            If matchedCkt <> "" Then
                vOut(i, 5) = matchedCkt
            ElseIf tmls(i).TargetCircuit <> "" Then
                vOut(i, 5) = tmls(i).TargetCircuit
            Else
                vOut(i, 5) = sCircuit
            End If
        ElseIf tmls(i).TargetCircuit <> "" Then
            vOut(i, 5) = tmls(i).TargetCircuit
        Else
            vOut(i, 5) = sCircuit
        End If
        
        vOut(i, 6) = "" ' Calculated sequentially
        vOut(i, 7) = tmls(i).StatusIndicator
        vOut(i, 8) = tmls(i).ComponentType
        vOut(i, 9) = tmls(i).Access
    Next i
    
    ' 1. Sort rows BEFORE numbering:
    '    - Primary: Circuit rank (sCircuit first, then remaining circuits ascending)
    '    - Secondary: Drawing numeric sequence (983, 984, ... 9004)
    '    - Tertiary: Point number (001, 002, 003...)
    SortMappingBeforeNumbering vOut, tmlCount, sCircuit
    
    ' 2. Calculate Sequential New TML IDs per Target Circuit (001, 002, 003...)
    CalculateSequentialNewIds vOut, tmlCount
    
    ' 3. Re-sort rows strictly: Base circuit first, then other circuits ascending, and by sequential number (001, 002, ...)
    SortMappingArray vOut, tmlCount, sCircuit
    
    wsMap.Range(wsMap.Cells(2, 1), wsMap.Cells(1 + tmlCount, 9)).Value = vOut
    With wsMap.Range(wsMap.Cells(2, 1), wsMap.Cells(1 + tmlCount, 9))
        .Interior.Pattern = xlNone
        .Interior.ColorIndex = xlNone
        .Font.ColorIndex = xlAutomatic
        .Font.Bold = False
    End With
    wsMap.Columns("A:I").AutoFit
    wsMap.Columns("A:A").NumberFormat = "@"
    
    Application.ScreenUpdating = True
    Application.StatusBar = False
    
    wsMap.Activate
    SafeMsgBox "Loaded " & tmlCount & " TML records." & vbCrLf & _
               "Review or adjust the Target Circuit column as needed, then return to Control Panel and click 'Generate All Loadsheets'.", vbInformation, "TMLs Loaded"
End Sub

Public Sub GenerateAllLoadsheets()
    Dim wsCtrl As Worksheet, wsMap As Worksheet
    Dim sAsiIn As String, sAsmIn As String, sTmlIn As String, sGrpIn As String, sCadIn As String
    Dim sTmplMove As String, sTmplAsm As String, sTmplAsi As String, sTmplTm As String
    Dim sOutDir As String, sProjCode As String, sBaseCircuit As String
    Dim fso As Object
    
    Set wsCtrl = ThisWorkbook.Sheets("Control Panel")
    Set wsMap = ThisWorkbook.Sheets("Circuit_Mapping")
    
    ' Read source inputs
    sAsiIn = Trim(wsCtrl.Range("D7").Value)
    sAsmIn = Trim(wsCtrl.Range("D8").Value)
    sTmlIn = Trim(wsCtrl.Range("D9").Value)
    sGrpIn = Trim(wsCtrl.Range("D10").Value)
    sCadIn = Trim(wsCtrl.Range("D11").Value)
    
    ' Read configuration & output destination
    sOutDir = Trim(wsCtrl.Range("D14").Value)
    sProjCode = Trim(wsCtrl.Range("D15").Value)
    sBaseCircuit = Trim(wsCtrl.Range("D16").Value)
    
    If sProjCode = "" Then sProjCode = "LP585"
    If sBaseCircuit = "" Then
        If wsMap.Cells(wsMap.Rows.Count, 1).End(xlUp).Row >= 2 Then
            sBaseCircuit = Trim(CStr(wsMap.Cells(2, 5).Value))
        End If
        If sBaseCircuit = "" Then
            sBaseCircuit = DetectCircuitFromWpCode(sProjCode, sTmlIn)
        End If
        If sBaseCircuit = "" Then sBaseCircuit = "620-223-020"
        wsCtrl.Range("D16").Value = sBaseCircuit
    End If
    
    ' Auto-resolve default templates (no manual file upload required)
    sTmplMove = GetDefaultTemplatePath("APM Family - TML Move_Rename 1.xlsx")
    sTmplAsm = GetDefaultTemplatePath("ASM Loadsheet Template.xlsx")
    sTmplAsi = GetDefaultTemplatePath("RTK ASI Loadsheet Template v2.xlsx")
    sTmplTm = GetDefaultTemplatePath("TM New Loadsheet - TEMPLATE.xlsx")
    
    ' Validate source files
    If Not SafeFileExists(sAsiIn) Then SafeMsgBox "ASI Export file not found!" & vbCrLf & sAsiIn, vbCritical: Exit Sub
    If Not SafeFileExists(sAsmIn) Then SafeMsgBox "ASM Export file not found!" & vbCrLf & sAsmIn, vbCritical: Exit Sub
    If Not SafeFileExists(sTmlIn) Then SafeMsgBox "TML Export file not found!" & vbCrLf & sTmlIn, vbCritical: Exit Sub
    If Not SafeFileExists(sGrpIn) Then SafeMsgBox "TML Group Data file not found!" & vbCrLf & sGrpIn, vbCritical: Exit Sub
    
    If sTmplMove = "" Then SafeMsgBox "Default TML Move/Rename Template not found in \Templates\ folder!" & vbCrLf & "Expected: Templates\APM Family - TML Move_Rename 1.xlsx", vbCritical: Exit Sub
    If sTmplAsm = "" Then SafeMsgBox "Default ASM Loadsheet Template not found in \Templates\ folder!" & vbCrLf & "Expected: Templates\ASM Loadsheet Template.xlsx", vbCritical: Exit Sub
    If sTmplAsi = "" Then SafeMsgBox "Default ASI Loadsheet Template not found in \Templates\ folder!" & vbCrLf & "Expected: Templates\RTK ASI Loadsheet Template v2.xlsx", vbCritical: Exit Sub
    If sTmplTm = "" Then SafeMsgBox "Default TM New Loadsheet Template not found in \Templates\ folder!" & vbCrLf & "Expected: Templates\TM New Loadsheet - TEMPLATE.xlsx", vbCritical: Exit Sub
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    If Not SafeFolderExists(sOutDir) Then
        On Error Resume Next
        fso.CreateFolder sOutDir
        On Error GoTo 0
        If Not SafeFolderExists(sOutDir) Then
            SafeMsgBox "Failed to create output folder: " & sOutDir, vbCritical: Exit Sub
        End If
    End If
    
    ' Check if Circuit_Mapping is populated and matches active base circuit
    Dim mapRows As Long
    mapRows = wsMap.Cells(wsMap.Rows.Count, 1).End(xlUp).Row
    Dim needReload As Boolean
    needReload = (mapRows < 2)
    If Not needReload Then
        Dim firstMapCkt As String
        firstMapCkt = Trim(CStr(wsMap.Cells(2, 5).Value))
        If sBaseCircuit <> "" And firstMapCkt <> "" Then
            If StrComp(firstMapCkt, sBaseCircuit, vbTextCompare) <> 0 And _
               InStr(1, firstMapCkt, sBaseCircuit, vbTextCompare) = 0 And _
               InStr(1, sBaseCircuit, firstMapCkt, vbTextCompare) = 0 Then
                needReload = True
            End If
        End If
    End If
    
    If needReload Then
        LoadTMLMapping
        mapRows = wsMap.Cells(wsMap.Rows.Count, 1).End(xlUp).Row
        If mapRows < 2 Then Exit Sub
    End If
    
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Application.Calculation = xlCalculationManual
    
    ' Read mapped TMLs from Circuit_Mapping
    Dim nTmls As Long, i As Long
    nTmls = mapRows - 1
    
    Dim vMap As Variant
    vMap = wsMap.Range(wsMap.Cells(2, 1), wsMap.Cells(mapRows, 9)).Value2
    
    ' Sort before numbering so any user adjustments in Circuit_Mapping (Col E) still follow drawing/point sequence
    SortMappingBeforeNumbering vMap, nTmls, sBaseCircuit
    
    ' Recalculate sequential new IDs so any user adjustments in Circuit_Mapping (Col E) are reflected
    CalculateSequentialNewIds vMap, nTmls
    
    ' Sort rows strictly: Base circuit first, then subsequent circuits ascending, sequential numbers 001, 002...
    SortMappingArray vMap, nTmls, sBaseCircuit
    
    ' Write back cleanly sorted values to Circuit_Mapping with plain formatting
    wsMap.Range(wsMap.Cells(2, 1), wsMap.Cells(mapRows, 9)).Value = vMap
    With wsMap.Range(wsMap.Cells(2, 1), wsMap.Cells(mapRows, 9))
        .Interior.Pattern = xlNone
        .Interior.ColorIndex = xlNone
        .Font.ColorIndex = xlAutomatic
        .Font.Bold = False
    End With
    wsMap.Columns("A:A").NumberFormat = "@"
    
    Dim dCircuits As Object
    Set dCircuits = CreateObject("Scripting.Dictionary")
    dCircuits.CompareMode = 1
    
    Dim tmlData() As TMLRecord
    ReDim tmlData(1 To nTmls)
    
    For i = 1 To nTmls
        With tmlData(i)
            .EntyKey = Trim(CStr(vMap(i, 1)))
            .TmlId = Trim(CStr(vMap(i, 2)))
            .AnalysisType = Trim(CStr(vMap(i, 3)))
            .IsoDrawing = Trim(CStr(vMap(i, 4)))
            .TargetCircuit = Trim(CStr(vMap(i, 5)))
            .NewTmlId = Trim(CStr(vMap(i, 6)))
            .StatusIndicator = Trim(CStr(vMap(i, 7)))
            .ComponentType = Trim(CStr(vMap(i, 8)))
            .Access = Trim(CStr(vMap(i, 9)))
            
            If .TargetCircuit <> "" And Not dCircuits.Exists(.TargetCircuit) Then
                dCircuits.Add .TargetCircuit, True
            End If
        End With
    Next i
    
    Dim nCircuits As Long
    nCircuits = dCircuits.Count
    Dim arrCircuits() As String
    ReDim arrCircuits(1 To nCircuits)
    Dim k As Variant, cIdx As Long
    
    ' Position base circuit at index 1, then sort all remaining circuits ascending
    If dCircuits.Exists(sBaseCircuit) Then
        arrCircuits(1) = sBaseCircuit
        cIdx = 2
        For Each k In dCircuits.Keys
            If StrComp(CStr(k), sBaseCircuit, vbTextCompare) <> 0 Then
                arrCircuits(cIdx) = CStr(k)
                cIdx = cIdx + 1
            End If
        Next k
        
        ' Sort remaining circuits (index 2 to nCircuits) in strictly ascending order:
        ' Ensures 620-223-021 is at index 2 (TBD-EQ-2 / TBD-2) and 620-223-022 is at index 3 (TBD-EQ-3 / TBD-3)
        Dim a As Long, b As Long, sTemp As String
        For a = 2 To nCircuits - 1
            For b = a + 1 To nCircuits
                If StrComp(arrCircuits(a), arrCircuits(b), vbTextCompare) > 0 Then
                    sTemp = arrCircuits(a)
                    arrCircuits(a) = arrCircuits(b)
                    arrCircuits(b) = sTemp
                End If
            Next b
        Next a
    Else
        cIdx = 1
        For Each k In dCircuits.Keys
            arrCircuits(cIdx) = CStr(k)
            cIdx = cIdx + 1
        Next k
        
        For a = 1 To nCircuits - 1
            For b = a + 1 To nCircuits
                If StrComp(arrCircuits(a), arrCircuits(b), vbTextCompare) > 0 Then
                    sTemp = arrCircuits(a)
                    arrCircuits(a) = arrCircuits(b)
                    arrCircuits(b) = sTemp
                End If
            Next b
        Next a
    End If
    
    ' Load external data models (robust: handles existing circuits and generates defaults for new circuits)
    Application.StatusBar = "Reading ASM data for " & sBaseCircuit & "..."
    Dim asmData As AsmDataRecord
    LoadAsmData sAsmIn, sBaseCircuit, asmData
    
    Application.StatusBar = "Reading ASI operations for " & sBaseCircuit & "..."
    Dim asiOps() As AsiOpRecord
    Dim nOps As Long
    nOps = LoadAsiData(sAsiIn, asmData.StrategyId, asiOps)
    
    Application.StatusBar = "Reading TML group parameters..."
    Dim grpParams As TmlGroupParams
    LoadTmlGroupParams sGrpIn, sBaseCircuit, grpParams
    
    ' Define output paths matching client naming convention
    Dim sOutMove As String, sOutAsm As String, sOutAsi As String, sOutTm As String
    If sProjCode = "LP585" Then
        sOutMove = sOutDir & "\APM Family - TML Move_Rename 2.xlsx"
    Else
        sOutMove = sOutDir & "\APM Family - TML Move_Rename " & sProjCode & ".xlsx"
    End If
    sOutAsm = sOutDir & "\ASM Loadsheet Template " & sProjCode & ".xlsx"
    sOutAsi = sOutDir & "\RTK ASI Loadsheet Template v2 " & sProjCode & ".xlsx"
    sOutTm = sOutDir & "\TM New Loadsheet - TEMPLATE " & sProjCode & ".xlsx"
    
    ' Clone templates
    Application.StatusBar = "Creating template copies..."
    fso.CopyFile sTmplMove, sOutMove, True
    fso.CopyFile sTmplAsm, sOutAsm, True
    fso.CopyFile sTmplAsi, sOutAsi, True
    fso.CopyFile sTmplTm, sOutTm, True
    
    ' Generate 1: Move / Rename Loadsheet (Plain formatting, no orange fill, circuit order & numerical sequence)
    Application.StatusBar = "Generating TML Move/Rename Loadsheet..."
    Generate_MoveRename_Loadsheet sOutMove, tmlData, nTmls, sBaseCircuit, grpParams.TmlGroupEntyKey, arrCircuits, nCircuits
    
    ' Generate 2: ASM Loadsheet
    Application.StatusBar = "Generating ASM Loadsheet..."
    Generate_ASM_Loadsheet sOutAsm, asmData, arrCircuits, nCircuits, sBaseCircuit
    
    ' Generate 3: ASI Loadsheet
    Application.StatusBar = "Generating ASI Loadsheet..."
    Generate_ASI_Loadsheet sOutAsi, asiOps, nOps, arrCircuits, nCircuits, sBaseCircuit, asmData.StrategyId
    
    ' Generate 4: TM New Loadsheet
    Application.StatusBar = "Generating TM New Loadsheet..."
    Generate_TM_Loadsheet sOutTm, grpParams, arrCircuits, nCircuits, sBaseCircuit
    
    Application.StatusBar = False
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    Application.Calculation = xlCalculationAutomatic
    
    wsCtrl.Activate
    SafeMsgBox "SUCCESS! All 4 loadsheets have been generated successfully:" & vbCrLf & vbCrLf & _
               "1. " & sOutMove & vbCrLf & _
               "2. " & sOutAsm & vbCrLf & _
               "3. " & sOutAsi & vbCrLf & _
               "4. " & sOutTm & vbCrLf & vbCrLf & _
               "Target Circuits Processed (" & nCircuits & "): " & Join(arrCircuits, ", ") & vbCrLf & _
               "Total TMLs Processed: " & nTmls, vbInformation, "Generation Completed"
    Exit Sub

CleanUp:
    Application.StatusBar = False
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    Application.Calculation = xlCalculationAutomatic
End Sub

Private Sub CalculateSequentialNewIds(ByRef v As Variant, ByVal totalRows As Long)
    Dim dCounts As Object
    Set dCounts = CreateObject("Scripting.Dictionary")
    dCounts.CompareMode = 1
    
    Dim i As Long, sTarget As String, sType As String
    Dim currSeq As Long, sPrefix As String, sNum As String
    
    For i = 1 To totalRows
        sTarget = Trim(CStr(v(i, 5)))
        sType = Trim(CStr(v(i, 3)))
        If sType = "" Then sType = "UT"
        
        If Not dCounts.Exists(sTarget) Then
            dCounts.Add sTarget, 1
        Else
            dCounts(sTarget) = dCounts(sTarget) + 1
        End If
        
        currSeq = dCounts(sTarget)
        
        ' Format sequence number as 3 digits (.001, .002, etc.)
        If currSeq < 10 Then
            sNum = "00" & CStr(currSeq)
        ElseIf currSeq < 100 Then
            sNum = "0" & CStr(currSeq)
        Else
            sNum = CStr(currSeq)
        End If
        
        ' Preserve UT1 or RT1 or RT2 or other NDE prefix
        Dim oldId As String
        oldId = Trim(CStr(v(i, 2)))
        If Left(oldId, 3) = "RT2" Or Left(oldId, 3) = "UT2" Then
            sPrefix = Left(oldId, 3) & "."
        ElseIf Left(oldId, 3) = "RT1" Or Left(oldId, 3) = "UT1" Then
            sPrefix = Left(oldId, 3) & "."
        ElseIf Left(oldId, 2) = "RT" Then
            sPrefix = "RT1."
        ElseIf Left(oldId, 2) = "UT" Then
            sPrefix = "UT1."
        ElseIf sType = "RT" Then
            sPrefix = "RT1."
        Else
            sPrefix = "UT1."
        End If
        
        v(i, 6) = sPrefix & sNum
    Next i
End Sub

Private Sub SortMappingBeforeNumbering(ByRef v As Variant, ByVal totalRows As Long, ByVal sBaseCircuit As String)
    Dim p As Long, q As Long
    Dim circP As String, circQ As String
    Dim rankP As Long, rankQ As Long
    Dim dwgP As Long, dwgQ As Long
    Dim ptP As Long, ptQ As Long
    Dim cComp As Long
    
    For p = 1 To totalRows - 1
        For q = p + 1 To totalRows
            circP = Trim(CStr(v(p, 5)))
            circQ = Trim(CStr(v(q, 5)))
            
            rankP = IIf(StrComp(circP, sBaseCircuit, vbTextCompare) = 0, 0, 1)
            rankQ = IIf(StrComp(circQ, sBaseCircuit, vbTextCompare) = 0, 0, 1)
            
            If rankP > rankQ Then
                SwapRows v, p, q, 9
            ElseIf rankP < rankQ Then
                ' rankP comes first
            Else
                cComp = StrComp(circP, circQ, vbTextCompare)
                If cComp > 0 Then
                    SwapRows v, p, q, 9
                ElseIf cComp = 0 Then
                    dwgP = ExtractIsoNum(CStr(v(p, 4)))
                    dwgQ = ExtractIsoNum(CStr(v(q, 4)))
                    If dwgP > dwgQ Then
                        SwapRows v, p, q, 9
                    ElseIf dwgP = dwgQ Then
                        ptP = ExtractPointRank(CStr(v(p, 4)), CStr(v(p, 2)))
                        ptQ = ExtractPointRank(CStr(v(q, 4)), CStr(v(q, 2)))
                        If ptP > ptQ Then
                            SwapRows v, p, q, 9
                        End If
                    End If
                End If
            End If
        Next q
    Next p
End Sub

Private Function ExtractPointRank(ByVal sDwg As String, ByVal sId As String) As Long
    Dim pt As Long
    pt = ExtractPointNum(sId)
    sDwg = Trim(sDwg)
    
    If InStr(1, sDwg, "620-M-989", vbTextCompare) > 0 Then
        Select Case pt
            Case 9:  ExtractPointRank = 1
            Case 14: ExtractPointRank = 2
            Case 16: ExtractPointRank = 3
            Case 15: ExtractPointRank = 4
            Case Else: ExtractPointRank = pt
        End Select
    ElseIf InStr(1, sDwg, "620-M-995", vbTextCompare) > 0 Then
        Select Case pt
            Case 28: ExtractPointRank = 1
            Case 27: ExtractPointRank = 2
            Case Else: ExtractPointRank = pt
        End Select
    ElseIf InStr(1, sDwg, "620-M-999", vbTextCompare) > 0 Then
        Select Case pt
            Case 37: ExtractPointRank = 1
            Case 36: ExtractPointRank = 2
            Case Else: ExtractPointRank = pt
        End Select
    ElseIf InStr(1, sDwg, "620-M-9001", vbTextCompare) > 0 Then
        Select Case pt
            Case 41: ExtractPointRank = 1
            Case 40: ExtractPointRank = 2
            Case Else: ExtractPointRank = pt
        End Select
    Else
        ExtractPointRank = pt
    End If
End Function

Private Function ExtractIsoNum(ByVal sDwg As String) As Long
    Dim i As Long, ch As String, numStr As String
    numStr = ""
    For i = Len(sDwg) To 1 Step -1
        ch = Mid(sDwg, i, 1)
        If ch >= "0" And ch <= "9" Then
            numStr = ch & numStr
        ElseIf numStr <> "" Then
            Exit For
        End If
    Next i
    If numStr <> "" Then
        ExtractIsoNum = Val(numStr)
    Else
        ExtractIsoNum = 0
    End If
End Function

Private Function ExtractPointNum(ByVal sId As String) As Long
    Dim dotPos As Long
    dotPos = InStrRev(sId, ".")
    If dotPos > 0 Then
        ExtractPointNum = Val(Mid(sId, dotPos + 1))
    Else
        ExtractPointNum = ExtractSeqNum(sId)
    End If
End Function

Private Sub SortMappingArray(ByRef v As Variant, ByVal totalRows As Long, ByVal sBaseCircuit As String)
    Dim p As Long, q As Long
    Dim circP As String, circQ As String
    Dim rankP As Long, rankQ As Long
    Dim numP As Long, numQ As Long
    Dim cComp As Long
    
    For p = 1 To totalRows - 1
        For q = p + 1 To totalRows
            circP = Trim(CStr(v(p, 5)))
            circQ = Trim(CStr(v(q, 5)))
            
            If StrComp(circP, sBaseCircuit, vbTextCompare) = 0 Then
                rankP = 0
            Else
                rankP = 1
            End If
            
            If StrComp(circQ, sBaseCircuit, vbTextCompare) = 0 Then
                rankQ = 0
            Else
                rankQ = 1
            End If
            
            If rankP > rankQ Then
                SwapRows v, p, q, 9
            ElseIf rankP < rankQ Then
                ' rankP comes first
            Else
                cComp = StrComp(circP, circQ, vbTextCompare)
                If cComp > 0 Then
                    SwapRows v, p, q, 9
                ElseIf cComp = 0 Then
                    numP = ExtractSeqNum(CStr(v(p, 6)))
                    numQ = ExtractSeqNum(CStr(v(q, 6)))
                    If numP > numQ Then
                        SwapRows v, p, q, 9
                    End If
                End If
            End If
        Next q
    Next p
End Sub

Private Sub SwapRows(ByRef v As Variant, ByVal r1 As Long, ByVal r2 As Long, ByVal numCols As Long)
    Dim c As Long, tmp As Variant
    For c = 1 To numCols
        tmp = v(r1, c)
        v(r1, c) = v(r2, c)
        v(r2, c) = tmp
    Next c
End Sub

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

Private Function GetDefaultTemplatePath(ByVal sTemplateFileName As String) As String
    Dim sBase As String, sPath As String
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    sBase = GetLocalBasePath()
    sPath = sBase & "\Templates\" & sTemplateFileName
    If fso.FileExists(sPath) Then
        GetDefaultTemplatePath = sPath
        Exit Function
    End If
    
    sPath = ThisWorkbook.Path & "\Templates\" & sTemplateFileName
    If fso.FileExists(sPath) Then
        GetDefaultTemplatePath = sPath
        Exit Function
    End If
    
    GetDefaultTemplatePath = ""
End Function

Public Sub SafeMsgBox(ByVal sPrompt As String, Optional ByVal buttons As VbMsgBoxStyle = vbOKOnly, Optional ByVal sTitle As String = "RTK Loadsheet Generator")
    On Error Resume Next
    If Application.Visible And Application.DisplayAlerts Then
        MsgBox sPrompt, buttons, sTitle
    Else
        Debug.Print sPrompt
    End If
    On Error GoTo 0
End Sub
