# Google Drive API 설정 가이드

## 1. Google Cloud Console에서 프로젝트 생성

1. https://console.cloud.google.com 접속
2. 새 프로젝트 생성 (또는 기존 프로젝트 사용)
3. 프로젝트 이름: `suno-automation` (원하는 이름)

## 2. Google Drive API 활성화

1. 왼쪽 메뉴 → **API 및 서비스** → **라이브러리**
2. "Google Drive API" 검색
3. **사용 설정** 클릭

## 3. 서비스 계정 만들기

1. 왼쪽 메뉴 → **API 및 서비스** → **사용자 인증 정보**
2. 상단 **+ 사용자 인증 정보 만들기** → **서비스 계정** 선택
3. 서비스 계정 이름: `suno-drive-uploader`
4. **만들고 계속하기** → **완료**

## 4. JSON 키 다운로드

1. 생성된 서비스 계정 클릭
2. **키** 탭으로 이동
3. **키 추가** → **새 키 만들기** → **JSON** 선택
4. JSON 파일 다운로드됨 → **프로젝트 폴더에 `google-credentials.json`으로 저장**

## 5. Google Drive에서 폴더 생성 및 공유

1. Google Drive 접속 (본인 계정)
2. 새 폴더 생성: `Suno Music`
3. 폴더 우클릭 → **공유** → **사용자 및 그룹 추가**
4. **서비스 계정 이메일 주소** 입력 (JSON 파일에서 `client_email` 값)
   - 예: `suno-drive-uploader@프로젝트ID.iam.gserviceaccount.com`
5. 권한: **편집자** 선택
6. **공유** 클릭

## 6. 폴더 ID 확인

1. Google Drive에서 `Suno Music` 폴더 열기
2. 브라우저 주소창 URL 확인:
   ```
   https://drive.google.com/drive/folders/1Abc123XYZ...
                                          ↑ 이 부분이 폴더 ID
   ```
3. 폴더 ID 복사

## 7. 환경 변수 설정

### 로컬 개발 시 (`.env` 파일):
```env
GOOGLE_DRIVE_FOLDER_ID=1Abc123XYZ...
GOOGLE_CREDENTIALS_PATH=google-credentials.json
```

### Streamlit Cloud 배포 시 (`.streamlit/secrets.toml`):
```toml
GOOGLE_DRIVE_FOLDER_ID = "1Abc123XYZ..."

[google_credentials]
# google-credentials.json 내용을 아래에 붙여넣기
type = "service_account"
project_id = "프로젝트ID"
private_key_id = "키ID"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "서비스계정@프로젝트ID.iam.gserviceaccount.com"
client_id = "클라이언트ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

## 완료!

설정이 완료되면 앱에서 자동으로 Google Drive에 곡이 업로드됩니다.
