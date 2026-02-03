"""
SunoAPI.org 클라이언트
"""
import time
import requests
from typing import Optional
import config


class SunoClient:
    """SunoAPI.org 음악 생성 클라이언트"""

    # 더미 콜백 URL (sunoapi.org는 콜백이 필수이지만 폴링으로 결과 확인)
    CALLBACK_URL = "https://webhook.site/dummy"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.SUNOAPI_KEY
        if not self.api_key:
            raise Exception("SUNOAPI_KEY가 설정되지 않았습니다.")

        self.base_url = config.SUNOAPI_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _api_request(self, method: str, endpoint: str, max_retries: int = 3, **kwargs) -> dict:
        """API 요청 (재시도 로직 포함)"""
        url = f"{self.base_url}{endpoint}"
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, timeout=120, **kwargs)

                if response.status_code == 524:
                    # Cloudflare 타임아웃 - 재시도
                    last_error = "서버 타임아웃 (524)"
                    time.sleep(5 * (attempt + 1))
                    continue

                if response.status_code != 200:
                    raise Exception(f"API 오류: {response.status_code} - {response.text[:200]}")

                data = response.json()

                if data.get("code") != 200:
                    raise Exception(f"API 오류: {data.get('msg', 'Unknown error')}")

                return data.get("data")

            except requests.exceptions.Timeout:
                last_error = "요청 타임아웃"
                time.sleep(5 * (attempt + 1))
            except requests.exceptions.ConnectionError:
                last_error = "연결 오류"
                time.sleep(5 * (attempt + 1))

        raise Exception(f"API 요청 실패 ({max_retries}회 재시도 후): {last_error}")

    def get_credits(self) -> dict:
        """크레딧 정보 조회"""
        credits = self._api_request("GET", "/api/v1/generate/credit")
        return {
            "total_credits": credits,
            "monthly_limit": 0,
            "monthly_usage": 0,
        }

    def generate(
        self,
        prompt: str,
        style: str = "",
        title: str = "",
        instrumental: bool = False,
        wait_for_completion: bool = True,
        model: str = "V4"
    ) -> list:
        """
        음악 생성

        Args:
            prompt: 가사 또는 음악 설명
            style: 음악 스타일 (예: "K-pop, energetic, female vocal")
            title: 곡 제목
            instrumental: True면 인스트루멘탈 (가사 없음)
            wait_for_completion: True면 완료될 때까지 대기
            model: 모델 선택 (V3_5, V4, V4_5, V4_5PLUS, V4_5ALL, V5)

        Returns:
            생성된 음악 정보 리스트
        """
        # Custom mode 사용 (가사/스타일/제목 직접 지정)
        payload = {
            "customMode": True,
            "instrumental": instrumental,
            "model": model,
            "callBackUrl": self.CALLBACK_URL,
            "prompt": prompt,
            "style": style or "pop, catchy",
            "title": title or "Untitled",
        }

        task_id = self._api_request("POST", "/api/v1/generate", json=payload)

        if isinstance(task_id, dict):
            task_id = task_id.get("taskId")

        if not task_id:
            raise Exception("음악 생성 실패: taskId를 받지 못했습니다")

        if wait_for_completion:
            return self._wait_for_task(task_id)

        return [{"task_id": task_id, "status": "pending"}]

    def generate_with_description(
        self,
        description: str,
        instrumental: bool = False,
        wait_for_completion: bool = True,
        model: str = "V4"
    ) -> list:
        """
        설명으로 음악 생성 (Suno가 자동으로 가사/스타일 생성)

        Args:
            description: 음악 설명 (예: "신나는 여름 파티 노래")
            instrumental: True면 인스트루멘탈
            wait_for_completion: True면 완료될 때까지 대기
            model: 모델 선택
        """
        # Non-custom mode (description만 제공)
        payload = {
            "customMode": False,
            "instrumental": instrumental,
            "model": model,
            "callBackUrl": self.CALLBACK_URL,
            "prompt": description,
        }

        task_id = self._api_request("POST", "/api/v1/generate", json=payload)

        if isinstance(task_id, dict):
            task_id = task_id.get("taskId")

        if not task_id:
            raise Exception("음악 생성 실패: taskId를 받지 못했습니다")

        if wait_for_completion:
            return self._wait_for_task(task_id)

        return [{"task_id": task_id, "status": "pending"}]

    def _wait_for_task(self, task_id: str) -> list:
        """태스크 완료 대기"""
        start_time = time.time()

        while True:
            if time.time() - start_time > config.MAX_WAIT_TIME:
                raise Exception("생성 시간 초과")

            status_data = self._get_task_status(task_id)
            status = status_data.get("status")

            if status == "SUCCESS":
                response = status_data.get("response", {})
                suno_data = response.get("sunoData", [])

                # 결과를 기존 포맷에 맞게 변환
                clips = []
                for item in suno_data:
                    clips.append({
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "audio_url": item.get("audioUrl") or item.get("sourceAudioUrl"),
                        "image_url": item.get("imageUrl") or item.get("sourceImageUrl"),
                        "duration": item.get("duration"),
                        "status": "complete",
                        "tags": item.get("tags"),
                        "prompt": item.get("prompt"),
                        "task_id": task_id,
                    })
                return clips

            elif status == "FAILED":
                error_msg = status_data.get("errorMessage", "Unknown error")
                raise Exception(f"생성 실패: {error_msg}")

            time.sleep(config.GENERATION_WAIT_TIME)

    def _get_task_status(self, task_id: str, max_retries: int = 3) -> dict:
        """태스크 상태 조회 (재시도 로직 포함)"""
        url = f"{self.base_url}/api/v1/generate/record-info?taskId={task_id}"
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=60)

                if response.status_code == 524:
                    last_error = "서버 타임아웃 (524)"
                    time.sleep(5 * (attempt + 1))
                    continue

                if response.status_code != 200:
                    raise Exception(f"상태 조회 실패: {response.status_code}")

                data = response.json()
                if data.get("code") != 200:
                    raise Exception(f"상태 조회 오류: {data.get('msg')}")

                return data.get("data", {})

            except requests.exceptions.Timeout:
                last_error = "요청 타임아웃"
                time.sleep(5 * (attempt + 1))
            except requests.exceptions.ConnectionError:
                last_error = "연결 오류"
                time.sleep(5 * (attempt + 1))

        raise Exception(f"상태 조회 실패 ({max_retries}회 재시도 후): {last_error}")

    def get_clips(self, clip_ids: list) -> list:
        """클립 정보 조회 (호환성 유지)"""
        # sunoapi.org에서는 task 기반이라 직접 clip 조회 불가
        # 빈 리스트 반환
        return []

    def get_clip_info(self, clip_id: str) -> dict:
        """단일 클립 정보 조회 (호환성 유지)"""
        return {}

    def download_audio(self, audio_url: str, save_path: str) -> tuple:
        """오디오 파일 다운로드 (파일 + bytes 데이터 반환)"""
        response = requests.get(audio_url, stream=True)

        if response.status_code != 200:
            raise Exception(f"다운로드 실패: {response.status_code}")

        # 메모리에 데이터 저장
        audio_data = b''

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                audio_data += chunk

        return save_path, audio_data

    def generate_async(
        self,
        prompt: str,
        style: str = "",
        title: str = "",
        instrumental: bool = False,
        model: str = "V4"
    ) -> str:
        """
        음악 생성 요청 (비동기 - task_id만 반환)

        Args:
            prompt: 가사 또는 음악 설명
            style: 음악 스타일
            title: 곡 제목
            instrumental: 인스트루멘탈 여부
            model: 모델 선택

        Returns:
            task_id
        """
        payload = {
            "customMode": True,
            "instrumental": instrumental,
            "model": model,
            "callBackUrl": self.CALLBACK_URL,
            "prompt": prompt,
            "style": style or "pop, catchy",
            "title": title or "Untitled",
        }

        task_id = self._api_request("POST", "/api/v1/generate", json=payload)

        if isinstance(task_id, dict):
            task_id = task_id.get("taskId")

        if not task_id:
            raise Exception("음악 생성 실패: taskId를 받지 못했습니다")

        return task_id

    def wait_for_completion(self, task_id: str) -> list:
        """
        태스크 완료 대기 및 결과 반환

        Args:
            task_id: Suno task ID

        Returns:
            생성된 음악 정보 리스트
        """
        return self._wait_for_task(task_id)
