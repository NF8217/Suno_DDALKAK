"""Google Drive 연동 매니저"""
import os
import json
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import streamlit as st
import io


class GoogleDriveManager:
    """Google Drive 파일 업로드 관리"""

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, folder_id: str, credentials_path: Optional[str] = None, credentials_dict: Optional[dict] = None):
        """
        Args:
            folder_id: Google Drive 루트 폴더 ID
            credentials_path: 로컬용 - JSON 파일 경로
            credentials_dict: Streamlit Cloud용 - credentials dict
        """
        self.root_folder_id = folder_id
        self.service = None
        self.odd_folder_id = None
        self.even_folder_id = None

        # 인증
        try:
            if credentials_dict:
                # Streamlit secrets에서 받은 dict
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=self.SCOPES
                )
            elif credentials_path and os.path.exists(credentials_path):
                # 로컬 JSON 파일
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=self.SCOPES
                )
            else:
                raise ValueError("credentials_path 또는 credentials_dict 중 하나는 필수입니다")

            self.service = build('drive', 'v3', credentials=credentials)
            self._ensure_folder_structure()

        except Exception as e:
            print(f"Google Drive 인증 실패: {e}")
            self.service = None

    def is_connected(self) -> bool:
        """Drive 연결 상태 확인"""
        return self.service is not None

    def _ensure_folder_structure(self):
        """홀수/짝수 폴더 구조 생성"""
        if not self.service:
            return

        try:
            # odd 폴더
            self.odd_folder_id = self._get_or_create_folder("odd", self.root_folder_id)
            # even 폴더
            self.even_folder_id = self._get_or_create_folder("even", self.root_folder_id)
        except Exception as e:
            print(f"폴더 구조 생성 실패: {e}")

    def _get_or_create_folder(self, folder_name: str, parent_id: str) -> str:
        """폴더가 없으면 생성, 있으면 ID 반환"""
        if not self.service:
            return ""

        try:
            # 기존 폴더 검색
            query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            items = results.get('files', [])

            if items:
                return items[0]['id']

            # 폴더 생성
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
            print(f"폴더 생성/조회 실패 ({folder_name}): {e}")
            return ""

    def upload_file(self, file_path: str = None, file_data: bytes = None, file_name: str = None, is_odd: bool = True) -> bool:
        """
        파일을 Google Drive에 업로드

        Args:
            file_path: 업로드할 파일 경로 (선택)
            file_data: 업로드할 파일 데이터 bytes (선택)
            file_name: 파일 이름 (file_data 사용 시 필수)
            is_odd: True면 odd 폴더, False면 even 폴더

        Returns:
            성공 여부
        """
        if not self.service:
            return False

        try:
            folder_id = self.odd_folder_id if is_odd else self.even_folder_id
            if not folder_id:
                return False

            # 파일 경로 또는 데이터 중 하나는 필수
            if file_path:
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    # 파일이 없으면 스킵 (에러는 출력)
                    print(f"파일이 존재하지 않음: {file_path}")
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

            print(f"✓ Google Drive 업로드 성공: {file_name} ({'odd' if is_odd else 'even'})")
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
