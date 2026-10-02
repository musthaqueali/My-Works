Attribute VB_Name = "modFilePicker"
Option Explicit

' ==============================================================================
' Module: modFilePicker
' Purpose: Provides robust file dialogs, OneDrive-safe path resolving, and 
'          visual "✓ Uploaded" status badges in green.
' ==============================================================================

Public Function SafeFileExists(ByVal sPath As String) As Boolean
    SafeFileExists = False
    If Trim(sPath) = "" Then Exit Function
    On Error Resume Next
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    SafeFileExists = fso.FileExists(sPath)
    On Error GoTo 0
End Function

Public Function SafeFolderExists(ByVal sPath As String) As Boolean
    SafeFolderExists = False
    If Trim(sPath) = "" Then Exit Function
    On Error Resume Next
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    SafeFolderExists = fso.FolderExists(sPath)
    On Error GoTo 0
End Function

Public Function BrowseForFile(ByVal sTitle As String, ByVal sFilterDesc As String, ByVal sFilterExt As String, Optional ByVal sInitialPath As String = "") As String
    Dim fd As Object
    On Error Resume Next
    Set fd = Application.FileDialog(3) ' 3 = msoFileDialogFilePicker
    On Error GoTo 0
    
    If fd Is Nothing Then
        BrowseForFile = ""
        Exit Function
    End If
    
    Dim sStartDir As String
    sStartDir = GetLocalBasePath()
    
    If sInitialPath <> "" Then
        If SafeFolderExists(sInitialPath) Then
            sStartDir = sInitialPath
        ElseIf SafeFileExists(sInitialPath) Then
            Dim fso As Object
            Set fso = CreateObject("Scripting.FileSystemObject")
            sStartDir = fso.GetParentFolderName(sInitialPath)
        End If
    End If
    
    With fd
        .Title = sTitle
        .AllowMultiSelect = False
        .Filters.Clear
        .Filters.Add sFilterDesc, sFilterExt
        .Filters.Add "All Files (*.*)", "*.*"
        .FilterIndex = 1
        If sStartDir <> "" Then
            If Right(sStartDir, 1) <> "\" Then sStartDir = sStartDir & "\"
            .InitialFileName = sStartDir
        End If
        
        If .Show = -1 Then
            BrowseForFile = .SelectedItems(1)
        Else
            BrowseForFile = ""
        End If
    End With
End Function

Public Function BrowseForFolder(ByVal sTitle As String, Optional ByVal sInitialPath As String = "") As String
    Dim fd As Object
    On Error Resume Next
    Set fd = Application.FileDialog(4) ' 4 = msoFileDialogFolderPicker
    On Error GoTo 0
    
    If fd Is Nothing Then
        BrowseForFolder = ""
        Exit Function
    End If
    
    Dim sStartDir As String
    sStartDir = GetLocalBasePath()
    If sInitialPath <> "" And SafeFolderExists(sInitialPath) Then
        sStartDir = sInitialPath
    End If
    
    With fd
        .Title = sTitle
        .AllowMultiSelect = False
        If sStartDir <> "" Then
            If Right(sStartDir, 1) <> "\" Then sStartDir = sStartDir & "\"
            .InitialFileName = sStartDir
        End If
        
        If .Show = -1 Then
            BrowseForFolder = .SelectedItems(1)
        Else
            BrowseForFolder = ""
        End If
    End With
End Function

' --- Button Handlers for Control Panel with Visual Feedback ---

Public Sub Browse_Input_ASI()
    Dim s As String
    s = BrowseForFile("Select ASI Export File", "Excel Files (*.xlsx; *.xlsm; *.xls)", "*.xlsx;*.xlsm;*.xls", Sheets("Control Panel").Range("D7").Value)
    If s <> "" Then
        Sheets("Control Panel").Range("D7").Value = s
        UpdateFileStatusBadges
    End If
End Sub

Public Sub Browse_Input_ASM()
    Dim s As String
    s = BrowseForFile("Select ASM Export File", "Excel Files (*.xlsx; *.xlsm; *.xls)", "*.xlsx;*.xlsm;*.xls", Sheets("Control Panel").Range("D8").Value)
    If s <> "" Then
        Sheets("Control Panel").Range("D8").Value = s
        UpdateFileStatusBadges
    End If
End Sub

Public Sub Browse_Input_TML()
    Dim s As String
    s = BrowseForFile("Select TML Export File", "Excel Files (*.xlsx; *.xlsm; *.xls)", "*.xlsx;*.xlsm;*.xls", Sheets("Control Panel").Range("D9").Value)
    If s <> "" Then
        Sheets("Control Panel").Range("D9").Value = s
        UpdateFileStatusBadges
    End If
End Sub

Public Sub Browse_Input_TMLGroup()
    Dim s As String
    s = BrowseForFile("Select RTK TML Group Data File", "Excel Files (*.xlsx; *.xlsm; *.xls)", "*.xlsx;*.xlsm;*.xls", Sheets("Control Panel").Range("D10").Value)
    If s <> "" Then
        Sheets("Control Panel").Range("D10").Value = s
        UpdateFileStatusBadges
    End If
End Sub

Public Sub Browse_Input_Cadmine()
    Dim s As String
    s = BrowseForFile("Select CADmine Export File", "Excel Files (*.xlsx; *.xlsm; *.xls)", "*.xlsx;*.xlsm;*.xls", Sheets("Control Panel").Range("D11").Value)
    If s <> "" Then
        Dim wsCtrl As Worksheet
        Set wsCtrl = Sheets("Control Panel")
        wsCtrl.Range("D11").Value = s
        
        ' Auto-detect Project Code and Source Circuit ID for this LP item
        Dim autoProj As String, autoCirc As String, dDwg As Object
        If DetectCadmineProjectAndCircuit(s, autoProj, autoCirc, dDwg) Then
            If autoProj <> "" Then wsCtrl.Range("D15").Value = autoProj
            If autoCirc <> "" Then wsCtrl.Range("D16").Value = autoCirc
        End If
        
        UpdateFileStatusBadges
    End If
End Sub

Public Sub Browse_OutputDir()
    Dim s As String
    s = BrowseForFolder("Select Output Destination Folder", Sheets("Control Panel").Range("D14").Value)
    If s <> "" Then
        Sheets("Control Panel").Range("D14").Value = s
        UpdateFileStatusBadges
    End If
End Sub

Public Sub SetDefaultPaths()
    Dim ws As Worksheet
    Dim basePath As String
    
    Set ws = ThisWorkbook.Sheets("Control Panel")
    basePath = GetLocalBasePath()
    
    ' Default input paths if files exist
    If SafeFileExists(basePath & "\Inputs recieved\4002 ASI Export.xlsx") Then
        ws.Range("D7").Value = basePath & "\Inputs recieved\4002 ASI Export.xlsx"
    End If
    If SafeFileExists(basePath & "\Inputs recieved\4002 ASM Export.xlsx") Then
        ws.Range("D8").Value = basePath & "\Inputs recieved\4002 ASM Export.xlsx"
    End If
    If SafeFileExists(basePath & "\Inputs recieved\4002 TML Export.xlsx") Then
        ws.Range("D9").Value = basePath & "\Inputs recieved\4002 TML Export.xlsx"
    End If
    If SafeFileExists(basePath & "\Inputs recieved\RTK TML Group Data.xlsx") Then
        ws.Range("D10").Value = basePath & "\Inputs recieved\RTK TML Group Data.xlsx"
    End If
    If SafeFileExists(basePath & "\Cadmine\DM585.xlsx") Then
        ws.Range("D11").Value = basePath & "\Cadmine\DM585.xlsx"
    End If
    
    ' Default output directory & configuration
    If ws.Range("D14").Value = "" Or Not SafeFolderExists(ws.Range("D14").Value) Then
        ws.Range("D14").Value = basePath & "\Output_Loadsheets"
    End If
    
    If ws.Range("D15").Value = "" Then ws.Range("D15").Value = "LP585"
    If ws.Range("D16").Value = "" Then ws.Range("D16").Value = "620-223-020"
    
    UpdateFileStatusBadges
End Sub

' ==============================================================================
' Sub: UpdateFileStatusBadges
' Purpose: Evaluates all file inputs and displays bright GREEN "✓ Uploaded" badges
' ==============================================================================
Public Sub UpdateFileStatusBadges()
    Dim ws As Worksheet
    Dim r As Long, fPath As String
    
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Control Panel")
    If ws Is Nothing Then Exit Sub
    
    Application.ScreenUpdating = False
    
    ' Rows 7 to 11 (Source Input Files)
    For r = 7 To 11
        fPath = Trim(CStr(ws.Range("D" & r).Value))
        If fPath <> "" And SafeFileExists(fPath) Then
            With ws.Range("C" & r)
                .Value = ChrW(&H2713) & " Uploaded"
                .Font.Name = "Calibri"
                .Font.Size = 10
                .Font.Bold = True
                .Font.Color = RGB(0, 102, 0)         ' Deep Dark Green
                .Interior.Color = RGB(198, 239, 206) ' Soft Emerald Green
                .HorizontalAlignment = xlCenter
                .VerticalAlignment = xlCenter
                .Borders.Color = RGB(150, 200, 150)
            End With
        Else
            With ws.Range("C" & r)
                .Value = "Not Uploaded"
                .Font.Name = "Calibri"
                .Font.Size = 9
                .Font.Bold = False
                .Font.Color = RGB(156, 0, 6)         ' Red
                .Interior.Color = RGB(255, 220, 220) ' Soft Red Tint
                .HorizontalAlignment = xlCenter
                .VerticalAlignment = xlCenter
                .Borders.Color = RGB(230, 180, 180)
            End With
        End If
    Next r
    
    ' Row 14: Output Directory
    fPath = Trim(CStr(ws.Range("D14").Value))
    If fPath <> "" And SafeFolderExists(fPath) Then
        With ws.Range("C14")
            .Value = ChrW(&H2713) & " Ready"
            .Font.Name = "Calibri"
            .Font.Size = 10
            .Font.Bold = True
            .Font.Color = RGB(0, 102, 0)
            .Interior.Color = RGB(198, 239, 206)
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
            .Borders.Color = RGB(150, 200, 150)
        End With
    Else
        With ws.Range("C14")
            .Value = "Select Folder"
            .Font.Name = "Calibri"
            .Font.Size = 9
            .Font.Bold = False
            .Font.Color = RGB(156, 0, 6)
            .Interior.Color = RGB(255, 220, 220)
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
            .Borders.Color = RGB(230, 180, 180)
        End With
    End If
    
    Application.ScreenUpdating = True
    On Error GoTo 0
End Sub

Public Function GetLocalBasePath() As String
    Dim sPath As String
    sPath = ThisWorkbook.Path
    
    ' If opened via SharePoint / OneDrive URL (starts with http: or https:)
    If Left(sPath, 5) = "http:" Or Left(sPath, 6) = "https:" Then
        Dim userProfile As String
        userProfile = Environ("USERPROFILE")
        If userProfile <> "" Then
            Dim testPath As String
            testPath = userProfile & "\OneDrive - Pinnacle\Desktop\My Works\RTK Loadsheet"
            If SafeFolderExists(testPath) Then
                GetLocalBasePath = testPath
                Exit Function
            End If
            testPath = userProfile & "\Desktop\My Works\RTK Loadsheet"
            If SafeFolderExists(testPath) Then
                GetLocalBasePath = testPath
                Exit Function
            End If
        End If
    End If
    
    If sPath = "" Then
        sPath = "c:\Users\musthaque.mayalankot\OneDrive - Pinnacle\Desktop\My Works\RTK Loadsheet"
    End If
    
    GetLocalBasePath = sPath
End Function

