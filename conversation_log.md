# Suno Automation - Google Drive 연결 수정 기록

## 문제 상황
- Streamlit Cloud에서 음악 생성 후 Google Drive에 파일이 업로드되지 않음
- 로컬(PC)에서 실행 시 "Google Drive 연결 실패" 표시

## 원인 분석

### 1. Streamlit Cloud 업로드 실패
- Streamlit Cloud는 **임시(ephemeral) 파일 시스템** 사용
- 파일을 디스크에 저장해도 바로 사라짐
- `MediaFileUpload`가 파일 경로로 업로드하려 할 때 파일이 존재하지 않음

### 2. 로컬 연결 실패
- `st.secrets` 접근 시 `secrets.toml` 파일이 없으면 에러 발생
- 에러가 전체 초기화 블록을 실패시킴
- `google-credentials.json` 경로가 상대 경로여서 파일을 못 찾음

## 해결 방법

### 1. 메모리 기반 업로드 지원 (Streamlit Cloud용)

**services/google_drive_manager.py**
```python
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io

def upload_file(self, file_path: str = None, file_data: bytes = None, file_name: str = None, is_odd: bool = True):
    # file_data가 있으면 메모리에서 직접 업로드
    if file_data and file_name:
        media = MediaIoBaseUpload(io.BytesIO(file_data), mimetype=mime_type, resumable=True)
    else:
        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
```

**services/suno_client.py**
```python
def download_audio(self, audio_url: str, save_path: str) -> tuple:
    # 파일 저장 + bytes 데이터 반환
    audio_data = b''
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            audio_data += chunk
    return save_path, audio_data  # tuple 반환
```

**services/music_manager.py**
```python
def save_song(self, clip_data, prompt_data, audio_path, audio_data=None):
    # audio_data가 있으면 메모리에서 직접 업로드
    if audio_data:
        self.drive_manager.upload_file(file_data=audio_data, file_name=file_name, is_odd=is_odd)
    else:
        self.drive_manager.upload_file(str(audio_path), is_odd=is_odd)
```

**app.py**
```python
save_path, audio_data = st.session_state.suno_client.download_audio(audio_url, str(save_path))
st.session_state.music_manager.save_song(
    clip_data=clip,
    prompt_data=prompt_data,
    audio_path=str(save_path),
    audio_data=audio_data  # bytes 데이터 전달
)
```

### 2. 로컬 credentials 경로 수정

**config.py**
```python
# 상대 경로 → 절대 경로로 변경
GOOGLE_CREDENTIALS_PATH = str(BASE_DIR / os.getenv("GOOGLE_CREDENTIALS_PATH", "google-credentials.json"))
```

### 3. secrets.toml 없을 때 에러 처리

**app.py**
```python
# secrets 접근 시 에러 방지
use_secrets = False
try:
    if hasattr(st, 'secrets') and 'google_credentials' in st.secrets:
        use_secrets = True
except:
    pass  # secrets.toml 없으면 로컬 모드 사용

if use_secrets:
    # Streamlit Cloud 모드
    credentials_dict = dict(st.secrets['google_credentials'])
else:
    # 로컬 모드 - JSON 파일 사용
    st.session_state.drive_manager = GoogleDriveManager(
        folder_id=config.GOOGLE_DRIVE_FOLDER_ID,
        credentials_path=config.GOOGLE_CREDENTIALS_PATH
    )
```

### 4. Google API 라이브러리 설치
```bash
pip install google-auth google-api-python-client google-auth-httplib2
```

## 결과
- **로컬(PC)**: Google Drive 연결 성공
- **Streamlit Cloud**: 메모리 기반 업로드로 Drive 업로드 가능

## 실행 방법

### 로컬 실행
```bash
python -m streamlit run app.py
```

### Streamlit Cloud
- URL: https://suno-ddal-kak-mg9uvenqnkz5nhateh3rep.streamlit.app/
- GitHub에 push하면 자동 배포

## 필요 파일
- `.env` - API 키, Google Drive 폴더 ID
- `google-credentials.json` - Google 서비스 계정 인증 정보
- Streamlit Cloud: Secrets에 `google_credentials` 설정 필요
