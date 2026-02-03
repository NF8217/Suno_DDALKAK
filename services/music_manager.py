"""
음악 파일 관리 및 메타데이터 처리
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import config

if TYPE_CHECKING:
    from services.google_drive_manager import GoogleDriveManager


class MusicManager:
    """생성된 음악 파일 및 메타데이터 관리"""

    def __init__(self, output_dir: Optional[Path] = None, drive_manager: Optional["GoogleDriveManager"] = None):
        self.output_dir = output_dir or config.OUTPUT_DIR
        self.metadata_file = self.output_dir / "metadata.json"
        self.drive_manager = drive_manager
        self._ensure_dirs()
        self._load_metadata()

    def _ensure_dirs(self):
        """필요한 디렉토리 생성"""
        self.output_dir.mkdir(exist_ok=True)

    def _load_metadata(self):
        """메타데이터 파일 로드"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"songs": [], "stats": {"total_generated": 0}}

    def _save_metadata(self):
        """메타데이터 파일 저장 (로컬 + Google Drive)"""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        # Google Drive에도 업로드
        if self.drive_manager and self.drive_manager.is_connected():
            self.drive_manager.upload_metadata(str(self.metadata_file))

    def save_song(
        self,
        clip_data: dict,
        prompt_data: dict,
        audio_path: str,
        audio_data: bytes = None,
        genre: str = None
    ) -> dict:
        """
        생성된 곡 정보 저장

        Args:
            clip_data: Suno API에서 받은 클립 데이터
            prompt_data: 프롬프트 생성기에서 받은 데이터
            audio_path: 저장된 오디오 파일 경로
            audio_data: 오디오 파일 bytes 데이터 (Streamlit Cloud용)
            genre: 장르 (Drive 장르별 폴더 저장용)

        Returns:
            저장된 곡 정보
        """
        song_info = {
            "id": clip_data.get("id", ""),
            "task_id": clip_data.get("task_id", ""),
            "title": prompt_data.get("title", clip_data.get("title", "Untitled")),
            "style": prompt_data.get("style", ""),
            "lyrics": prompt_data.get("lyrics", ""),
            "theme": prompt_data.get("theme", ""),
            "genre": genre or "",
            "audio_url": clip_data.get("audio_url", ""),
            "audio_path": str(audio_path),
            "image_url": clip_data.get("image_url", ""),
            "duration": clip_data.get("duration", 0),
            "created_at": datetime.now().isoformat(),
            "suno_data": {
                "model": clip_data.get("model_name", ""),
                "status": clip_data.get("status", ""),
            }
        }

        self.metadata["songs"].append(song_info)
        self.metadata["stats"]["total_generated"] += 1
        self._save_metadata()

        # Google Drive에 mp3 업로드
        upload_success = False
        upload_error = None
        if self.drive_manager and self.drive_manager.is_connected():
            try:
                # audio_path에서 output1/output2 판단 (output1=odd, output2=even)
                audio_path_obj = Path(audio_path)
                is_odd = "output1" in str(audio_path_obj.parent)  # output1 폴더면 홀수(odd)

                # audio_data가 있으면 메모리에서 직접 업로드 (Streamlit Cloud용)
                if audio_data:
                    file_name = audio_path_obj.name
                    upload_success = self.drive_manager.upload_file(file_data=audio_data, file_name=file_name, is_odd=is_odd, genre=genre)
                else:
                    # 로컬 파일에서 업로드
                    upload_success = self.drive_manager.upload_file(str(audio_path), is_odd=is_odd, genre=genre)
            except Exception as e:
                upload_error = str(e)

        song_info["drive_upload"] = upload_success
        song_info["drive_error"] = upload_error
        return song_info

    def get_song(self, song_id: str) -> Optional[dict]:
        """ID로 곡 정보 조회"""
        for song in self.metadata["songs"]:
            if song["id"] == song_id:
                return song
        return None

    def get_all_songs(self) -> list:
        """모든 곡 정보 조회"""
        return self.metadata["songs"]

    def get_recent_songs(self, count: int = 10) -> list:
        """최근 생성된 곡 조회"""
        return sorted(
            self.metadata["songs"],
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:count]

    def get_songs_by_date(self, date: str) -> list:
        """특정 날짜에 생성된 곡 조회 (YYYY-MM-DD 형식)"""
        return [
            song for song in self.metadata["songs"]
            if song.get("created_at", "").startswith(date)
        ]

    def get_stats(self) -> dict:
        """통계 정보 조회"""
        songs = self.metadata["songs"]

        # 오늘 생성된 곡 수
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = len([s for s in songs if s.get("created_at", "").startswith(today)])

        # 장르별 통계
        style_counts = {}
        for song in songs:
            style = song.get("style", "Unknown")
            # 첫 번째 태그를 장르로 사용
            genre = style.split(",")[0].strip() if style else "Unknown"
            style_counts[genre] = style_counts.get(genre, 0) + 1

        return {
            "total_generated": self.metadata["stats"]["total_generated"],
            "total_saved": len(songs),
            "today_count": today_count,
            "genres": style_counts
        }

    def generate_filename(self, title: str, song_id: str) -> str:
        """안전한 파일명 생성"""
        # 특수문자 제거 및 공백 처리
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        safe_title = safe_title.replace(" ", "_")[:50]  # 최대 50자

        if not safe_title:
            safe_title = "song"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_id = song_id[:8] if song_id else "unknown"

        return f"{safe_title}_{timestamp}_{short_id}.mp3"

    def get_audio_path(self, title: str, song_id: str, clip_index: int = 0) -> Path:
        """오디오 파일 저장 경로 생성

        Args:
            title: 곡 제목
            song_id: 곡 ID
            clip_index: 클립 인덱스 (0=output1, 1=output2)
        """
        filename = self.generate_filename(title, song_id)

        # 클립 인덱스에 따라 폴더 결정
        if clip_index == 0:
            output_folder = config.OUTPUT1_DIR
        else:
            output_folder = config.OUTPUT2_DIR

        output_folder.mkdir(exist_ok=True)
        return output_folder / filename

    def delete_song(self, song_id: str) -> bool:
        """곡 정보 및 파일 삭제"""
        song = self.get_song(song_id)
        if not song:
            return False

        # 파일 삭제
        audio_path = Path(song.get("audio_path", ""))
        if audio_path.exists():
            audio_path.unlink()

        # 메타데이터에서 제거
        self.metadata["songs"] = [
            s for s in self.metadata["songs"] if s["id"] != song_id
        ]
        self._save_metadata()

        return True

    def export_for_youtube(self, song_id: str) -> dict:
        """유튜브 업로드용 정보 추출"""
        song = self.get_song(song_id)
        if not song:
            return {}

        return {
            "title": song.get("title", ""),
            "description": f"""🎵 {song.get('title', '')}

Theme: {song.get('theme', '')}
Style: {song.get('style', '')}

{song.get('lyrics', '')}

---
Generated with Suno AI
""",
            "tags": [
                tag.strip()
                for tag in song.get("style", "").split(",")
            ] + ["AI Music", "Suno AI", "AI Generated"],
            "audio_path": song.get("audio_path", ""),
        }
