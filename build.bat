@echo off
setlocal
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name Aniro app.py
if errorlevel 1 exit /b 1
echo Built dist\Aniro.exe
pause
