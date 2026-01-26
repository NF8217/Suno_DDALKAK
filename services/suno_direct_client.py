"""
Suno Direct API Client - 사용자 라이브러리 조회용
studio-api.suno.ai 직접 연결 (Clerk 인증)
"""
import json
import base64
import requests
from typing import Optional
import config


class SunoDirectClient:
    """Suno 직접 API 클라이언트 (라이브러리 조회 전용)"""

    CLERK_BASE_URL = "https://clerk.suno.com"

    def __init__(self, cookie: Optional[str] = None, session_token: Optional[str] = None):
        self.cookie = cookie or config.SUNO_COOKIE
        self.session_token = session_token or config.SUNO_SESSION

        if not self.cookie:
            raise ValueError("SUNO_COOKIE가 설정되지 않았습니다. (.env 파일 확인)")

        self.base_url = config.SUNO_BASE_URL
        self.session = requests.Session()
        self._session_id = self._extract_session_id()

        # 토큰 갱신 시도
        self._refresh_token()

    def _extract_session_id(self) -> str:
        """SUNO_SESSION JWT에서 session ID 추출"""
        if self.session_token:
            try:
                payload = self.session_token.split(".")[1]
                # Base64 패딩 추가
                payload += "=" * (4 - len(payload) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload))
                sid = decoded.get("sid", "")
                if sid:
                    return sid
            except Exception:
                pass

        # cookie에서 client 정보로 세션 조회 시도
        return ""

    def _refresh_token(self):
        """Clerk를 통해 새 액세스 토큰 발급"""
        if not self._session_id:
            # session ID 없으면 client sessions 조회
            self._session_id = self._get_session_id_from_client()

        if not self._session_id:
            raise ValueError(
                "세션 ID를 찾을 수 없습니다. SUNO_SESSION 토큰을 갱신해주세요."
            )

        try:
            url = f"{self.CLERK_BASE_URL}/v1/client/sessions/{self._session_id}/tokens?_clerk_js_version=5.56.0"
            response = requests.post(
                url,
                headers={
                    "Cookie": f"__client={self.cookie}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Origin": "https://suno.com",
                    "Referer": "https://suno.com/",
                },
                timeout=15
            )

            if response.status_code != 200:
                raise Exception(f"토큰 갱신 실패: HTTP {response.status_code}")

            data = response.json()
            new_token = data.get("jwt", "")
            if not new_token:
                raise Exception("JWT 토큰을 받지 못했습니다")

            self.session_token = new_token
            self._update_session_headers()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Clerk 서버 연결 실패: {e}")

    def _get_session_id_from_client(self) -> str:
        """Cookie를 사용해 활성 세션 ID 조회"""
        try:
            url = f"{self.CLERK_BASE_URL}/v1/client?_clerk_js_version=5.56.0"
            response = requests.get(
                url,
                headers={
                    "Cookie": f"__client={self.cookie}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                },
                timeout=15
            )

            if response.status_code != 200:
                return ""

            data = response.json()
            # Clerk response에서 활성 세션 찾기
            client_data = data.get("response", data)
            sessions = client_data.get("sessions", [])
            for sess in sessions:
                if sess.get("status") == "active":
                    return sess.get("id", "")

            # 첫 번째 세션이라도 사용
            if sessions:
                return sessions[0].get("id", "")

        except Exception:
            pass

        return ""

    def _update_session_headers(self):
        """세션 헤더 업데이트"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Origin": "https://suno.com",
            "Referer": "https://suno.com/",
            "Accept": "*/*",
        })

    def _request(self, method: str, endpoint: str, retry_auth: bool = True, **kwargs):
        """API 요청 실행 (토큰 만료 시 자동 갱신)"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Suno API 연결 실패: {e}")

        if response.status_code in (401, 403) and retry_auth:
            # 토큰 만료 → 갱신 후 재시도
            self._refresh_token()
            return self._request(method, endpoint, retry_auth=False, **kwargs)

        if response.status_code == 401:
            raise PermissionError(
                "세션 토큰이 만료되었습니다. Suno 웹에서 새 쿠키를 발급받아 "
                ".env의 SUNO_COOKIE를 갱신해주세요."
            )
        if response.status_code == 403:
            raise PermissionError("Suno API 접근 거부됨. 쿠키를 확인해주세요.")
        if response.status_code == 503:
            raise Exception(
                "Suno API 서비스가 일시 중단되었습니다. 잠시 후 다시 시도해주세요."
            )
        if response.status_code != 200:
            raise Exception(f"Suno API 오류: {response.status_code} - {response.text[:200]}")

        return response.json()

    def get_feed(self, page: int = 0) -> list:
        """
        사용자 라이브러리 조회 (페이지네이션)

        Args:
            page: 페이지 번호 (0부터 시작)

        Returns:
            곡 정보 리스트 (페이지당 약 20곡)
        """
        data = self._request("GET", f"/api/feed/?page={page}")

        if isinstance(data, list):
            return data
        return data.get("clips", data.get("data", []))

    def get_clip(self, clip_id: str) -> dict:
        """특정 클립 상세 정보 조회"""
        return self._request("GET", f"/api/clip/{clip_id}")

    def download_audio(self, audio_url: str, save_path: str) -> str:
        """오디오 파일 다운로드"""
        response = requests.get(audio_url, stream=True, timeout=60)

        if response.status_code != 200:
            raise Exception(f"다운로드 실패: HTTP {response.status_code}")

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return save_path
