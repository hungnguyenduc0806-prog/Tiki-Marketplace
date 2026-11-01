@echo off
REM ----------------------------------------------------------------
REM Chay crawl hang ngay. Dat lich bang Windows Task Scheduler.
REM
REM Khong ghi duong dan tuyet doi: %~dp0 la thu muc chua file .bat nay,
REM nen project di dau cung chay duoc, va khong lo ten user ra GitHub.
REM ----------------------------------------------------------------

cd /d "%~dp0\.."
if errorlevel 1 (
    echo KHONG VAO DUOC THU MUC PROJECT
    pause
    exit /b 1
)

if not exist logs mkdir logs

for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "NGAY=%%a"
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format HHmmss"') do set "GIO=%%a"

echo. >> "logs\crawl_%NGAY%.log"
echo ===== Bat dau %NGAY% %GIO% ===== >> "logs\crawl_%NGAY%.log"

REM Buoc 1: crawl -> data/raw/*.json + data/processed/*.csv
python -m src.crawl >> "logs\crawl_%NGAY%.log" 2>&1
if errorlevel 1 (
    echo ===== LOI O BUOC CRAWL ===== >> "logs\crawl_%NGAY%.log"
    exit /b 1
)

REM Buoc 2: do vao PostgreSQL (bo dong nay neu chua dung database)
python -m src.load >> "logs\crawl_%NGAY%.log" 2>&1
if errorlevel 1 (
    echo ===== LOI O BUOC LOAD DB ===== >> "logs\crawl_%NGAY%.log"
    exit /b 1
)

echo ===== Xong ===== >> "logs\crawl_%NGAY%.log"

REM Bo dau REM o dong duoi neu muon cua so dung lai khi chay tay
REM pause
