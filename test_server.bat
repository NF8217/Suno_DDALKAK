@echo off
chcp 65001 > nul
echo ========================================
echo    SunoAPI 서버 상태 확인
echo ========================================
echo.

if exist "venv" (
    call venv\Scripts\activate.bat
)

python test_api.py

echo.
pause
