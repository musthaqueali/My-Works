Attribute VB_Name = "Excel_To_AutoCAD_Updater"
' =========================================================================================
' CHEVRON ISOMETRIC TITLE BLOCK UPDATER (EXCEL TO AUTOCAD AUTOMATION)
' Run directly from Excel! Connects to AutoCAD via COM, iterates all DWGs,
' and updates Title Block + Notes attributes from CADmine sheets.
' =========================================================================================
Option Explicit

Public Sub Run_Update_Title_Blocks_From_Excel()
    Dim acadApp As Object
    Dim acadDoc As Object
    Dim wb As Workbook
    Dim wsBorder As Worksheet
    Dim wsPlant As Worksheet
    Dim dwgFolder As String
    Dim fso As Object
    Dim folder As Object
    Dim file As Object
    Dim fileName As String
    Dim dwgPath As String
    Dim totalDWGs As Long
    Dim updatedDWGs As Long
    Dim totalAttrs As Long
    Dim currentAttrs As Long
    Dim startTime As Double
    Dim resp As VbMsgBoxResult
    
    ' Set DWG folder path
    dwgFolder = "C:\Users\musthaque.mayalankot\OneDrive - Pinnacle\Desktop\My Works\Title Blocks\"
    If Right(dwgFolder, 1) <> "\" Then dwgFolder = dwgFolder & "\"
    
    Set wb = ThisWorkbook
    On Error Resume Next
    Set wsBorder = wb.Sheets("blk_BORDER TEXT")
    Set wsPlant = wb.Sheets("blk_Plant Info")
    On Error GoTo 0
    
    If wsBorder Is Nothing Or wsPlant Is Nothing Then
        MsgBox "Could not find sheets 'blk_BORDER TEXT' or 'blk_Plant Info' in this workbook!" & vbCrLf & _
               "Please ensure this macro is running inside the CADmine workbook.", vbCritical, "Sheets Missing"
        Exit Sub
    End If
    
    resp = MsgBox("Ready to update Title Blocks in all DWGs in:" & vbCrLf & _
                  dwgFolder & vbCrLf & vbCrLf & _
                  "This macro will connect to AutoCAD, open each drawing, fill the title block and notes attributes, and save changes.", _
                  vbQuestion + vbYesNo, "Confirm Batch Update")
    If resp <> vbYes Then Exit Sub
    
    startTime = Timer
    
    ' Connect to active AutoCAD or launch a new instance
    On Error Resume Next
    Set acadApp = GetObject(, "AutoCAD.Application")
    If acadApp Is Nothing Then
        Set acadApp = CreateObject("AutoCAD.Application")
        If acadApp Is Nothing Then
            MsgBox "Failed to connect to AutoCAD! Please make sure AutoCAD is running.", vbCritical, "AutoCAD Error"
            Exit Sub
        End If
    End If
    acadApp.Visible = True
    On Error GoTo 0
    
    ' Build fast in-memory lookup dictionaries from Excel sheets
    Dim dictBorder As Object
    Dim dictPlant As Object
    Set dictBorder = CreateObject("Scripting.Dictionary")
    Set dictPlant = CreateObject("Scripting.Dictionary")
    
    BuildDictionaryFromSheet wsBorder, dictBorder
    BuildDictionaryFromSheet wsPlant, dictPlant
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set folder = fso.GetFolder(dwgFolder)
    
    totalDWGs = 0
    updatedDWGs = 0
    totalAttrs = 0
    
    Application.StatusBar = "Starting AutoCAD Title Block automation..."
    
    For Each file In folder.Files
        fileName = LCase(file.Name)
        If Right(fileName, 4) = ".dwg" Then
            totalDWGs = totalDWGs + 1
            dwgPath = file.Path
            Application.StatusBar = "Processing (" & totalDWGs & "): " & file.Name & " ..."
            
            On Error Resume Next
            Set acadDoc = acadApp.Documents.Open(dwgPath)
            If Err.Number = 0 And Not acadDoc Is Nothing Then
                currentAttrs = UpdateDocBlockAttributes(acadDoc, fileName, dictBorder, dictPlant)
                acadDoc.Close True ' Save and Close
                If currentAttrs > 0 Then
                    updatedDWGs = updatedDWGs + 1
                    totalAttrs = totalAttrs + currentAttrs
                End If
            Else
                Err.Clear
            End If
            On Error GoTo 0
        End If
    Next file
    
    Application.StatusBar = False
    
    MsgBox "Batch Title Block Automation Finished!" & vbCrLf & vbCrLf & _
           "Total DWGs checked: " & totalDWGs & vbCrLf & _
           "DWGs updated: " & updatedDWGs & vbCrLf & _
           "Total attributes populated: " & totalAttrs & vbCrLf & _
           "Elapsed Time: " & Format(Timer - startTime, "0.0") & " seconds", _
           vbInformation, "Update Complete"
End Sub

Private Sub BuildDictionaryFromSheet(ByVal ws As Worksheet, ByRef dict As Object)
    Dim r As Long, c As Long, maxRow As Long, maxCol As Long
    Dim fp As String, dwgKey As String
    Dim tag As String, val As String
    Dim subDict As Object
    
    maxRow = ws.UsedRange.Rows.Count
    maxCol = ws.UsedRange.Columns.Count
    
    For r = 2 To maxRow
        fp = Trim(CStr(ws.Cells(r, 1).Value))
        If fp <> "" Then
            dwgKey = LCase(GetFileName(fp))
            Set subDict = CreateObject("Scripting.Dictionary")
            For c = 14 To maxCol
                tag = UCase(Trim(CStr(ws.Cells(1, c).Value)))
                val = Trim(CStr(ws.Cells(r, c).Value))
                If tag <> "" Then subDict(tag) = val
            Next c
            Set dict(dwgKey) = subDict
        End If
    Next r
End Sub

Private Function UpdateDocBlockAttributes(ByVal doc As Object, ByVal dwgKey As String, _
                                         ByVal dictBorder As Object, ByVal dictPlant As Object) As Long
    Dim entity As Object
    Dim blockRef As Object
    Dim attrs As Variant
    Dim i As Long
    Dim att As Object
    Dim rawTag As String
    Dim cleanTag As String
    Dim updateCount As Long
    Dim subDictBorder As Object
    Dim subDictPlant As Object
    Dim newVal As String
    
    updateCount = 0
    If dictBorder.Exists(dwgKey) Then Set subDictBorder = dictBorder(dwgKey)
    If dictPlant.Exists(dwgKey) Then Set subDictPlant = dictPlant(dwgKey)
    
    For Each entity In doc.ModelSpace
        If entity.ObjectName = "AcDbBlockReference" Then
            Set blockRef = entity
            If blockRef.HasAttributes Then
                attrs = blockRef.GetAttributes
                For i = LBound(attrs) To UBound(attrs)
                    Set att = attrs(i)
                    rawTag = UCase(Trim(att.TagString))
                    cleanTag = StripPrefix(rawTag)
                    newVal = ""
                    
                    ' 1. Check in Plant Info (SYSTEMNAME, PLANTNAME, ZONE...)
                    If Not subDictPlant Is Nothing Then
                        If subDictPlant.Exists(rawTag) Then
                            newVal = subDictPlant(rawTag)
                        ElseIf subDictPlant.Exists(cleanTag) Then
                            newVal = subDictPlant(cleanTag)
                        End If
                    End If
                    
                    ' 2. Check in Border Text (APIPIPECLASS, CVXPIPESPEC, OPTEMP, FROM, TO...)
                    If newVal = "" And Not subDictBorder Is Nothing Then
                        If subDictBorder.Exists(rawTag) Then
                            newVal = subDictBorder(rawTag)
                        ElseIf subDictBorder.Exists(cleanTag) Then
                            newVal = subDictBorder(cleanTag)
                        End If
                    End If
                    
                    If newVal <> "" Then
                        If att.TextString <> newVal Then
                            att.TextString = newVal
                            att.Update
                            updateCount = updateCount + 1
                        End If
                    End If
                Next i
            End If
        End If
    Next entity
    
    UpdateDocBlockAttributes = updateCount
End Function

Private Function StripPrefix(ByVal tag As String) As String
    Dim pos As Long
    pos = InStr(tag, "_")
    If pos > 1 And pos <= 4 Then
        If IsNumeric(Left(tag, pos - 1)) Then
            StripPrefix = Mid(tag, pos + 1)
            Exit Function
        End If
    End If
    StripPrefix = tag
End Function

Private Function GetFileName(ByVal p As String) As String
    Dim pos As Long
    pos = InStrRev(p, "\")
    If pos > 0 Then GetFileName = Mid(p, pos + 1) Else GetFileName = p
End Function
