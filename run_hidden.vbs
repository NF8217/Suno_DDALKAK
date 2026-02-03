Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\Purplewing8217_LJK\Desktop\suno-automation"
WshShell.Run "cmd /c .\venv\Scripts\streamlit.exe run app.py", 0, False
