@echo off
chcp 65001 > nul
echo ========================================
echo    Suno Automation 실행
echo ========================================
echo.

:: 가상환경 확인 및 생성
if not exist "venv" (
    echo [1/3] 가상환경 생성 중...
    python -m venv venv
)

:: 가상환경 활성화
echo [2/3] 가상환경 활성화...
call venv\Scripts\activate.bat

:: 패키지 설치
echo [3/3] 패키지 확인...
pip install -r requirements.txt -q

echo.
echo ========================================
echo    브라우저에서 열기: http://localhost:8501
echo    종료: Ctrl+C
echo ========================================
echo.

:: Streamlit 실행 (포트 8501 고정)
streamlit run app.py --server.port 8501

pause
