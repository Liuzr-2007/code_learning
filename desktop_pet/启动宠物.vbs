' 无窗口启动桌面宠物(用 pythonw.exe，不显示控制台)
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = dir
ws.Run "pythonw.exe """ & dir & "\pet.py""", 0, False
