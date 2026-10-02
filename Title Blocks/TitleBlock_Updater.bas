Attribute VB_Name = "TitleBlock_Updater"
' =========================================================================================
' CHEVRON ISOMETRIC TITLE BLOCK & NOTES AUTOMATION TOOL (V2 - ROBUST MATCHING)
' Designed for: Pinnacle Reliability / Chevron PSD (14t Red Bluff Tank Farm)
' Automates: Title Block & Notes population in AutoCAD DWGs from CADmine Excel Export
' =========================================================================================
Option Explicit

Public Const DEFAULT_CADMINE_PATH As String = "C:\Users\musthaque.mayalankot\OneDrive - Pinnacle\Desktop\My Works\Title Blocks\CADmine\PSD014t_CADmine_20260921.xlsx"
Public Const DEFAULT_DWG_FOLDER As String = "C:\Users\musthaque.mayalankot\OneDrive - Pinnacle\Desktop\My Works\Title Blocks\"

' -----------------------------------------------------------------------------------------
' MACRO 1: Update Title Block in the CURRENT ACTIVE DRAWING
' Use this to test and verify on the drawing currently open in AutoCAD!
' -----------------------------------------------------------------------------------------
Public Sub Update_Active_Drawing()
    Dim dwgName As String
    Dim cadminePath As String
    Dim dictBorder As Object, dictPlant As Object
    Dim dwgKey As String
    Dim updatedCount As Long
    Dim blocksScanned As Long
    Dim diagMsg As String
    
    cadminePath = DEFAULT_CADMINE_PATH
    If Dir(cadminePath) = "" Then
        MsgBox "CADmine Excel file not found at:" & vbCrLf & cadminePath, vbCritical, "File Not Found"
        Exit Sub
    End If
    
    dwgName = ThisDrawing.Name
    dwgKey = LCase(dwgName)
    
    ThisDrawing.Utility.Prompt vbCrLf & ">>> [Title Block Tool] Loading CADmine data for: " & dwgName & " ..." & vbCrLf
    
    Set dictBorder = CreateObject("Scripting.Dictionary")
    Set dictPlant = CreateObject("Scripting.Dictionary")
    
    LoadCADmineData cadminePath, dictBorder, dictPlant
    
    If Not dictBorder.Exists(dwgKey) And Not dictPlant.Exists(dwgKey) Then
        MsgBox "Warning: Drawing '" & dwgName & "' was not found in CADmine Excel!" & vbCrLf & vbCrLf & _
               "Total drawings loaded from Excel: " & dictBorder.Count, vbExclamation, "No CADmine Record"
        Exit Sub
    End If
    
    blocksScanned = 0
    updatedCount = 0
    
    ' Scan ModelSpace, PaperSpace, and all Layouts
    updatedCount = UpdateAllSpaces(ThisDrawing, dwgKey, dictBorder, dictPlant, blocksScanned)
    
    ThisDrawing.Regen acAllViewports
    
    diagMsg = "Active Drawing: " & dwgName & vbCrLf & _
              "Blocks Inspected: " & blocksScanned & vbCrLf & _
              "Attributes Populated: " & updatedCount
              
    If updatedCount > 0 Then
        MsgBox "Success!" & vbCrLf & vbCrLf & diagMsg, vbInformation, "Title Block Updated"
    Else
        MsgBox "Finished scan, but 0 attributes were modified." & vbCrLf & vbCrLf & diagMsg & vbCrLf & vbCrLf & _
               "Please check if the title block attributes are already filled or locked.", vbExclamation, "Scan Finished"
    End If
End Sub

' -----------------------------------------------------------------------------------------
' MACRO 2: Batch Update ALL 113 DWG Drawings in the Folder
' Automatically iterates all DWGs, fills Title Blocks & Notes, saves and closes.
' -----------------------------------------------------------------------------------------
Public Sub Batch_Update_All_DWGs()
    Dim fso As Object, folder As Object, file As Object
    Dim dwgFolder As String, cadminePath As String
    Dim dwgDoc As Object, fileName As String, dwgKey As String
    Dim totalProcessed As Long, totalUpdated As Long, currentUpdated As Long, blocksScanned As Long
    Dim startTime As Double, userResp As VbMsgBoxResult
    
    dwgFolder = DEFAULT_DWG_FOLDER
    cadminePath = DEFAULT_CADMINE_PATH
    
    If Dir(cadminePath) = "" Then
        MsgBox "CADmine Excel file not found at:" & vbCrLf & cadminePath, vbCritical, "File Not Found"
        Exit Sub
    End If
    
    userResp = MsgBox("Ready to batch update Title Blocks for all DWGs in:" & vbCrLf & _
                      dwgFolder & vbCrLf & vbCrLf & _
                      "Using CADmine data from:" & vbCrLf & Dir(cadminePath), _
                      vbQuestion + vbYesNo, "Confirm Batch Update")
    If userResp <> vbYes Then Exit Sub
    
    startTime = Timer
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set folder = fso.GetFolder(dwgFolder)
    
    Dim dictBorder As Object, dictPlant As Object
    Set dictBorder = CreateObject("Scripting.Dictionary")
    Set dictPlant = CreateObject("Scripting.Dictionary")
    
    ThisDrawing.Utility.Prompt vbCrLf & ">>> Loading CADmine Excel data..." & vbCrLf
    LoadCADmineData cadminePath, dictBorder, dictPlant
    
    totalProcessed = 0
    totalUpdated = 0
    
    For Each file In folder.Files
        fileName = file.Name
        dwgKey = LCase(fileName)
        If Right(dwgKey, 4) = ".dwg" Then
            totalProcessed = totalProcessed + 1
            ThisDrawing.Utility.Prompt "Processing (" & totalProcessed & "): " & fileName & " ... "
            
            If LCase(ThisDrawing.FullName) = LCase(file.Path) Then
                currentUpdated = UpdateAllSpaces(ThisDrawing, dwgKey, dictBorder, dictPlant, blocksScanned)
                ThisDrawing.Save
                totalUpdated = totalUpdated + currentUpdated
                ThisDrawing.Utility.Prompt "Updated " & currentUpdated & " attrs." & vbCrLf
            Else
                On Error Resume Next
                Set dwgDoc = Application.Documents.Open(file.Path)
                If Err.Number = 0 And Not dwgDoc Is Nothing Then
                    currentUpdated = UpdateAllSpaces(dwgDoc, dwgKey, dictBorder, dictPlant, blocksScanned)
                    dwgDoc.Close True ' Save and close
                    totalUpdated = totalUpdated + currentUpdated
                    ThisDrawing.Utility.Prompt "Updated " & currentUpdated & " attrs." & vbCrLf
                Else
                    ThisDrawing.Utility.Prompt "SKIPPED (Locked/Error)" & vbCrLf
                    Err.Clear
                End If
                On Error GoTo 0
            End If
        End If
    Next file
    
    ThisDrawing.Regen acAllViewports
    
    MsgBox "Batch Process Complete!" & vbCrLf & vbCrLf & _
           "Total DWGs Processed: " & totalProcessed & vbCrLf & _
           "Total Attributes Populated: " & totalUpdated & vbCrLf & _
           "Elapsed Time: " & Format(Timer - startTime, "0.0") & " seconds", _
           vbInformation, "Batch Update Successful"
End Sub

' -----------------------------------------------------------------------------------------
' SCAN BOTH MODELSPACE AND PAPERSPACE LAYOUTS
' -----------------------------------------------------------------------------------------
Private Function UpdateAllSpaces(ByVal doc As Object, ByVal dwgKey As String, _
                                ByVal dictBorder As Object, ByVal dictPlant As Object, _
                                ByRef blocksScanned As Long) As Long
    Dim totalUpdates As Long
    Dim layoutObj As Object
    
    totalUpdates = 0
    
    ' 1. Check ModelSpace
    totalUpdates = totalUpdates + ScanEntityBlock(doc.ModelSpace, dwgKey, dictBorder, dictPlant, blocksScanned)
    
    ' 2. Check PaperSpace
    totalUpdates = totalUpdates + ScanEntityBlock(doc.PaperSpace, dwgKey, dictBorder, dictPlant, blocksScanned)
    
    ' 3. Check all Layout blocks
    On Error Resume Next
    For Each layoutObj In doc.Layouts
        If UCase(layoutObj.Name) <> "MODEL" Then
            totalUpdates = totalUpdates + ScanEntityBlock(layoutObj.Block, dwgKey, dictBorder, dictPlant, blocksScanned)
        End If
    Next layoutObj
    On Error GoTo 0
    
    UpdateAllSpaces = totalUpdates
End Function

' -----------------------------------------------------------------------------------------
' SCAN A SPECIFIC BLOCK/SPACE FOR BLOCK REFERENCES AND ATTRIBUTES
' -----------------------------------------------------------------------------------------
Private Function ScanEntityBlock(ByVal spaceObj As Object, ByVal dwgKey As String, _
                                ByVal dictBorder As Object, ByVal dictPlant As Object, _
                                ByRef blocksScanned As Long) As Long
    Dim entity As Object
    Dim blockRef As Object
    Dim attrs As Variant
    Dim i As Long
    Dim att As Object
    Dim normTag As String
    Dim newVal As String
    Dim updateCount As Long
    Dim subDictBorder As Object
    Dim subDictPlant As Object
    
    updateCount = 0
    If spaceObj Is Nothing Then Exit Function
    
    If dictBorder.Exists(dwgKey) Then Set subDictBorder = dictBorder(dwgKey)
    If dictPlant.Exists(dwgKey) Then Set subDictPlant = dictPlant(dwgKey)
    
    For Each entity In spaceObj
        If entity.ObjectName = "AcDbBlockReference" Then
            blocksScanned = blocksScanned + 1
            Set blockRef = entity
            
            If blockRef.HasAttributes Then
                attrs = blockRef.GetAttributes
                For i = LBound(attrs) To UBound(attrs)
                    Set att = attrs(i)
                    normTag = NormalizeTag(att.TagString)
                    newVal = ""
                    
                    ' 1. Look in Plant Info Dictionary (SYSTEMNAME, PLANTNAME, ZONE, DWGTYPE)
                    If Not subDictPlant Is Nothing Then
                        If subDictPlant.Exists(normTag) Then
                            newVal = subDictPlant(normTag)
                        End If
                    End If
                    
                    ' 2. Look in Border Text Dictionary (APIPIPECLASS, CVXPIPESPEC, OPTEMP, FROM, TO, MATERIAL...)
                    If newVal = "" And Not subDictBorder Is Nothing Then
                        If subDictBorder.Exists(normTag) Then
                            newVal = subDictBorder(normTag)
                        End If
                    End If
                    
                    ' Apply value if match found
                    If newVal <> "" Then
                        If Trim(att.TextString) <> Trim(newVal) Then
                            att.TextString = newVal
                            att.Update
                            updateCount = updateCount + 1
                        End If
                    End If
                Next i
            End If
        End If
    Next entity
    
    ScanEntityBlock = updateCount
End Function

' -----------------------------------------------------------------------------------------
' TAG NORMALIZER: Strips leading index prefix and all punctuation/spaces
' Examples:
'   "01_SYSTEMNAME"   -> "SYSTEMNAME"
'   "SYSTEM_NAME"     -> "SYSTEMNAME"
'   "21_APIPIPECLASS" -> "APIPIPECLASS"
'   "API PIPE CLASS"  -> "APIPIPECLASS"
' -----------------------------------------------------------------------------------------
Public Function NormalizeTag(ByVal rawTag As String) As String
    Dim s As String, ch As String, i As Long, res As String
    Dim pos As Long
    
    s = UCase(Trim(rawTag))
    
    ' Strip leading number prefix like "01_", "21_"
    pos = InStr(s, "_")
    If pos > 1 And pos <= 4 Then
        If IsNumeric(Left(s, pos - 1)) Then
            s = Mid(s, pos + 1)
        End If
    End If
    
    ' Keep only uppercase letters A-Z and digits 0-9
    res = ""
    For i = 1 To Len(s)
        ch = Mid(s, i, 1)
        If (ch >= "A" And ch <= "Z") Or (ch >= "0" And ch <= "9") Then
            res = res & ch
        End If
    Next i
    
    NormalizeTag = res
End Function

' -----------------------------------------------------------------------------------------
' LOAD CADMINE EXCEL DATA WITH FULL NORMALIZATION
' -----------------------------------------------------------------------------------------
Private Sub LoadCADmineData(ByVal excelPath As String, ByRef dictBorder As Object, ByRef dictPlant As Object)
    Dim xlApp As Object, xlWb As Object, wsBorder As Object, wsPlant As Object
    Dim r As Long, c As Long, maxCol As Long, maxRow As Long
    Dim filePathVal As String, dwgKey As String
    Dim tagHeader As String, normHeader As String, cellVal As String
    Dim subDict As Object
    
    Set xlApp = CreateObject("Excel.Application")
    xlApp.Visible = False
    xlApp.DisplayAlerts = False
    Set xlWb = xlApp.Workbooks.Open(excelPath, ReadOnly:=True)
    
    ' 1. Load blk_BORDER TEXT
    On Error Resume Next
    Set wsBorder = xlWb.Sheets("blk_BORDER TEXT")
    On Error GoTo 0
    If Not wsBorder Is Nothing Then
        maxRow = wsBorder.Cells(wsBorder.Rows.Count, 1).End(-4162).Row ' xlUp
        maxCol = wsBorder.Cells(1, wsBorder.Columns.Count).End(-4159).Column ' xlToLeft
        
        For r = 2 To maxRow
            filePathVal = Trim(CStr(wsBorder.Cells(r, 1).Value))
            If filePathVal <> "" Then
                dwgKey = LCase(GetFileNameFromPath(filePathVal))
                If Not dictBorder.Exists(dwgKey) Then
                    Set subDict = CreateObject("Scripting.Dictionary")
                    Set dictBorder(dwgKey) = subDict
                Else
                    Set subDict = dictBorder(dwgKey)
                End If
                
                For c = 14 To maxCol
                    tagHeader = CStr(wsBorder.Cells(1, c).Value)
                    normHeader = NormalizeTag(tagHeader)
                    cellVal = Trim(CStr(wsBorder.Cells(r, c).Value))
                    If normHeader <> "" Then
                        subDict(normHeader) = cellVal
                    End If
                Next c
            End If
        Next r
    End If
    
    ' 2. Load blk_Plant Info
    On Error Resume Next
    Set wsPlant = xlWb.Sheets("blk_Plant Info")
    On Error GoTo 0
    If Not wsPlant Is Nothing Then
        maxRow = wsPlant.Cells(wsPlant.Rows.Count, 1).End(-4162).Row
        maxCol = wsPlant.Cells(1, wsPlant.Columns.Count).End(-4159).Column
        
        For r = 2 To maxRow
            filePathVal = Trim(CStr(wsPlant.Cells(r, 1).Value))
            If filePathVal <> "" Then
                dwgKey = LCase(GetFileNameFromPath(filePathVal))
                If Not dictPlant.Exists(dwgKey) Then
                    Set subDict = CreateObject("Scripting.Dictionary")
                    Set dictPlant(dwgKey) = subDict
                Else
                    Set subDict = dictPlant(dwgKey)
                End If
                
                For c = 14 To maxCol
                    tagHeader = CStr(wsPlant.Cells(1, c).Value)
                    normHeader = NormalizeTag(tagHeader)
                    cellVal = Trim(CStr(wsPlant.Cells(r, c).Value))
                    If normHeader <> "" Then
                        subDict(normHeader) = cellVal
                    End If
                Next c
            End If
        Next r
    End If
    
    xlWb.Close False
    xlApp.Quit
End Sub

Private Function GetFileNameFromPath(ByVal fullPath As String) As String
    Dim pos As Long
    pos = InStrRev(fullPath, "\")
    If pos > 0 Then GetFileNameFromPath = Mid(fullPath, pos + 1) Else GetFileNameFromPath = fullPath
End Function
