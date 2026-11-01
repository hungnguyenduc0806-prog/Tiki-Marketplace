@echo off

set PROJECT_DIR=C:\Users\Lenovo\Documents\Tiki project

set PYTHON=C:\Users\Lenovo\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe

set CATEGORY=1591

REM ------------------------------------------------------------

cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo KHONG VAO DUOC THU MUC %PROJECT_DIR%
    pause
    exit /b 1
)

if not exist logs mkdir logs

REM Ten file log theo ngay: logs\crawl_20261031.log
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "NGAY=%%a"
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format HHmmss"') do set "GIO=%%a"
echo. >> "logs\crawl_%NGAY%.log"
echo ===== Bat dau %NGAY% %GIO% ===== >> "logs\crawl_%NGAY%.log"

"%PYTHON%" crawl_tiki.py %CATEGORY% >> "logs\crawl_%NGAY%.log" 2>&1

if errorlevel 1 (
    echo ===== LOI, ma thoat %errorlevel% ===== >> "logs\crawl_%NGAY%.log"
) else (
    echo ===== Xong =====                      >> "logs\crawl_%NGAY%.log"
)

REM Bo dau REM o dong duoi neu muon cua so dung lai de doc ket qua khi chay tay
pause