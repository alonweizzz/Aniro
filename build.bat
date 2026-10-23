@echo off
setlocal
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1
py make_icon.py
if errorlevel 1 exit /b 1
py -m PyInstaller --noconfirm --clean --onefile --windowed --name Aniro --icon Aniro.ico --add-data "logo.png;." app.py
if errorlevel 1 exit /b 1
echo Built dist\Aniro.exe
pause
