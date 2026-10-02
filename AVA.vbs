Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
If CreateObject("Scripting.FileSystemObject").FileExists(WshShell.CurrentDirectory & "\.venv\Scripts\pythonw.exe") Then
    WshShell.Run """" & WshShell.CurrentDirectory & "\.venv\Scripts\pythonw.exe"" """ & WshShell.CurrentDirectory & "\start_ava.py""", 0, False
Else
    WshShell.Run "pythonw """ & WshShell.CurrentDirectory & "\start_ava.py""", 0, False
End If
