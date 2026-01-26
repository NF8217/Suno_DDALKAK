# Suno Automation 🎵

AI 기반 음악 자동 생성 및 관리 시스템

## 주요 기능

- 🎼 AI 프롬프트 자동 생성 (Anthropic Claude / OpenAI GPT)
- 🎵 Suno API를 통한 음악 생성
- 📚 라이브러리 관리 (홀수/짝수 폴더 자동 분류)
- ☁️ Google Drive 자동 백업 및 동기화
- 🎨 Artlist 스타일 UI
- 📱 웹/모바일 접근 가능 (Streamlit Cloud 배포)

## 설치 및 실행

### 1. 로컬 실행

```bash
# 저장소 클론
git clone <your-repo-url>
cd suno-automation

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력

# 실행
streamlit run app.py
```

### 2. Streamlit Cloud 배포

1. GitHub에 코드 푸시
2. [Streamlit Cloud](https://streamlit.io/cloud) 접속
3. "New app" → GitHub 저장소 연결
4. Settings → Secrets에 `.streamlit/secrets.toml.example` 내용 입력
5. Deploy 클릭

## 필수 API 키

- **SUNOAPI_KEY**: [sunoapi.org](https://sunoapi.org)에서 발급
- **ANTHROPIC_API_KEY** 또는 **OPENAI_API_KEY**: 프롬프트 생성용
- **GOOGLE_DRIVE_FOLDER_ID** (선택): 클라우드 자동 백업

## Google Drive 연동 (선택)

Google Drive와 연동하면 생성된 곡이 자동으로 클라우드에 백업됩니다.

자세한 설정 방법은 [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md)를 참고하세요.

## 폴더 구조

```
suno-automation/
├── app.py                 # Streamlit UI
├── config.py             # 설정 파일
├── services/
│   ├── suno_client.py    # Suno API 클라이언트
│   ├── prompt_generator.py  # AI 프롬프트 생성
│   ├── music_manager.py  # 음악 파일 관리
│   └── google_drive_manager.py  # Google Drive 업로드
├── outputs/
│   ├── output1/          # 홀수 곡 (첫 번째 생성)
│   ├── output2/          # 짝수 곡 (두 번째 생성)
│   └── metadata.json     # 곡 메타데이터
└── library/              # 다운로드한 곡 라이브러리
```

## 사용 방법

1. **API 연결**: 사이드바에서 "🔌 API 연결" 버튼 클릭
2. **곡 생성**:
   - 테마/스타일 입력
   - "🎵 음악 생성" 클릭
   - 자동으로 홀수/짝수 폴더 및 Google Drive에 저장됨
3. **라이브러리 관리**: "📚 라이브러리" 탭에서 생성된 곡 재생/다운로드

## 라이선스

MIT License

## 문의

이슈나 개선 제안은 GitHub Issues를 이용해주세요.
