"""Google Drive 연동 매니저 (OAuth 방식)"""
import os
import json
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io


class GoogleDriveManager:
    """Google Drive 파일 업로드 관리 (OAuth 방식)"""

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, folder_id: str, credentials_path: Optional[str] = None, credentials_dict: Optional[dict] = None):
        """
        Args:
            folder_id: Google Drive 루트 폴더 ID
            credentials_path: OAuth credentials JSON 파일 경로
            credentials_dict: Streamlit Cloud용 - credentials dict (미사용, 호환성 유지)
        """
        self.root_folder_id = folder_id
        self.service = None
        # 기존 홀짝 폴더 (하위 호환)
        self.odd_folder_id = None
        self.even_folder_id = None
        # 장르별 폴더 캐시: {"팝": {"홀수": "id", "짝수": "id"}, ...}
        self.genre_folders = {}

        # 프로젝트 루트 경로
        self.base_dir = Path(__file__).parent.parent
        self.token_path = self.base_dir / "token.json"
        self.oauth_credentials_path = self.base_dir / "oauth_credentials.json"

        # OAuth 인증
        try:
            creds = None

            # 저장된 토큰이 있으면 로드
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)

            # 토큰이 없거나 만료됐으면 새로 인증
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # 토큰 갱신
                    creds.refresh(Request())
                else:
                    # 새 인증 (브라우저 열림)
                    if not self.oauth_credentials_path.exists():
                        return

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.oauth_credentials_path), self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # 토큰 저장
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('drive', 'v3', credentials=creds)
            self._ensure_folder_structure()

        except Exception as e:
            print(f"Google Drive 인증 실패: {e}")
            self.service = None

    def is_connected(self) -> bool:
        """Drive 연결 상태 확인"""
        return self.service is not None

    def _ensure_folder_structure(self):
        """홀수/짝수 폴더 구조 확인"""
        if not self.service:
            return

        try:
            # 홀수 폴더 (검색만, 자동생성 안 함)
            self.odd_folder_id = self._find_or_create_folder("홀수", self.root_folder_id)
            # 짝수 폴더 (검색만, 자동생성 안 함)
            self.even_folder_id = self._find_or_create_folder("짝수", self.root_folder_id)
        except Exception as e:
            print(f"폴더 구조 확인 실패: {e}")

    def _get_genre_folder(self, genre: str, is_odd: bool) -> str:
        """장르별 홀짝 폴더 ID 가져오기 (없으면 생성)

        Args:
            genre: 장르 이름 (예: "팝", "발라드")
            is_odd: True면 홀수, False면 짝수

        Returns:
            폴더 ID
        """
        if not self.service:
            return ""

        odd_even = "홀수" if is_odd else "짝수"

        # 캐시 확인
        if genre in self.genre_folders:
            if odd_even in self.genre_folders[genre]:
                return self.genre_folders[genre][odd_even]

        # 장르 폴더 찾기/생성
        genre_folder_id = self._find_or_create_folder(genre, self.root_folder_id)
        if not genre_folder_id:
            return ""

        # 홀짝 폴더 찾기/생성
        odd_even_folder_id = self._find_or_create_folder(odd_even, genre_folder_id)

        # 캐시에 저장
        if genre not in self.genre_folders:
            self.genre_folders[genre] = {}
        self.genre_folders[genre][odd_even] = odd_even_folder_id

        return odd_even_folder_id

    def _find_or_create_folder(self, folder_name: str, parent_id: str) -> str:
        """폴더 검색, 없으면 생성"""
        if not self.service:
            return ""

        try:
            query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            items = results.get('files', [])

            if items:
                return items[0]['id']

            # OAuth는 본인 계정이므로 폴더 생성 가능!
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            return folder.get('id')

        except Exception as e:
            print(f"폴더 검색/생성 실패 ({folder_name}): {e}")
            return ""

    def upload_file(self, file_path: str = None, file_data: bytes = None, file_name: str = None, is_odd: bool = True, genre: str = None) -> bool:
        """
        파일을 Google Drive에 업로드

        Args:
            file_path: 업로드할 파일 경로 (선택)
            file_data: 업로드할 파일 데이터 bytes (선택)
            file_name: 파일 이름 (file_data 사용 시 필수)
            is_odd: True면 홀수 폴더, False면 짝수 폴더
            genre: 장르 (지정하면 장르별 폴더에 저장)

        Returns:
            성공 여부
        """
        if not self.service:
            return False

        try:
            # 장르가 지정되면 장르별 폴더 사용, 아니면 기존 홀짝 폴더 사용
            if genre:
                folder_id = self._get_genre_folder(genre, is_odd)
            else:
                folder_id = self.odd_folder_id if is_odd else self.even_folder_id

            if not folder_id:
                return False

            # 파일 경로 또는 데이터 중 하나는 필수
            if file_path:
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    return False
                file_name = file_path_obj.name
                mime_type = 'audio/mpeg' if file_name.endswith('.mp3') else 'application/octet-stream'
                media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
            elif file_data and file_name:
                mime_type = 'audio/mpeg' if file_name.endswith('.mp3') else 'application/octet-stream'
                media = MediaIoBaseUpload(io.BytesIO(file_data), mimetype=mime_type, resumable=True)
            else:
                return False

            # 기존 파일 검색 (덮어쓰기)
            query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id)'
            ).execute()

            items = results.get('files', [])

            if items:
                # 업데이트
                file_id = items[0]['id']
                self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
            else:
                # 새로 생성
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]
                }
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            return True

        except Exception as e:
            print(f"파일 업로드 실패 ({file_name or file_path}): {e}")
            return False

    def upload_metadata(self, metadata_path: str) -> bool:
        """
        metadata.json을 루트 폴더에 업로드

        Args:
            metadata_path: metadata.json 파일 경로

        Returns:
            성공 여부
        """
        if not self.service:
            return False

        try:
            metadata_path_obj = Path(metadata_path)
            if not metadata_path_obj.exists():
                return False

            file_name = metadata_path_obj.name

            # 기존 파일 검색
            query = f"name='{file_name}' and '{self.root_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id)'
            ).execute()

            items = results.get('files', [])

            media = MediaFileUpload(str(metadata_path), mimetype='application/json', resumable=True)

            if items:
                # 업데이트
                file_id = items[0]['id']
                self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
            else:
                # 새로 생성
                file_metadata = {
                    'name': file_name,
                    'parents': [self.root_folder_id]
                }
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            return True

        except Exception as e:
            print(f"metadata 업로드 실패: {e}")
            return False
