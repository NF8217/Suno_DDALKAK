"""
Suno Automation 설정 파일
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 경로 설정
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT1_DIR = BASE_DIR / "output1"  # 첫 번째 곡 저장
OUTPUT2_DIR = BASE_DIR / "output2"  # 두 번째 곡 저장
LIBRARY_DIR = BASE_DIR / "library"  # 라이브러리 다운로드 저장
TEMP_DIR = BASE_DIR / "temp"

# 폴더 생성
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT1_DIR.mkdir(exist_ok=True)
OUTPUT2_DIR.mkdir(exist_ok=True)
LIBRARY_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# API 키
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUNOAPI_KEY = os.getenv("SUNOAPI_KEY", "")

# Suno Direct API (오디오 URL 갱신용 - clip 조회)
SUNO_COOKIE = os.getenv("SUNO_COOKIE", "")
SUNO_SESSION = os.getenv("SUNO_SESSION", "")

# SunoAPI.org 설정
SUNOAPI_BASE_URL = "https://api.sunoapi.org"

# Suno Direct API (라이브러리 조회용)
SUNO_BASE_URL = "https://studio-api.suno.ai"

# 기본 음악 설정
DEFAULT_MUSIC_DURATION = 60  # 초 (30, 60, 120 등)
DEFAULT_INSTRUMENTAL = False  # True면 가사 없는 인스트루멘탈

# 생성 설정
MAX_CONCURRENT_GENERATIONS = 2  # 동시 생성 개수 (Suno 제한)
GENERATION_WAIT_TIME = 10  # 상태 확인 간격 (초)
MAX_WAIT_TIME = 300  # 최대 대기 시간 (초)

# Google Drive 설정
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")  # Drive 루트 폴더 ID
GOOGLE_CREDENTIALS_PATH = str(BASE_DIR / os.getenv("GOOGLE_CREDENTIALS_PATH", "google-credentials.json"))  # 로컬용 JSON 파일 (절대 경로)
GOOGLE_DRIVE_ENABLED = bool(GOOGLE_DRIVE_FOLDER_ID)  # 폴더 ID가 있으면 활성화
