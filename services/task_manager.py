"""
작업 큐 관리 - 동시 생성 및 새로고침 후 복구 지원
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import config


class TaskManager:
    """음악 생성 작업 큐 관리"""

    def __init__(self):
        self.tasks_file = config.PENDING_TASKS_FILE
        self._load_tasks()

    def _load_tasks(self):
        """작업 목록 로드"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = {"pending": [], "completed": []}
        else:
            self.tasks = {"pending": [], "completed": []}

    def _save_tasks(self):
        """작업 목록 저장"""
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def add_task(self, task_id: str, prompt_data: dict, genre: str) -> dict:
        """새 작업 추가

        Args:
            task_id: Suno API task ID
            prompt_data: 프롬프트 데이터
            genre: 장르

        Returns:
            추가된 작업 정보
        """
        task = {
            "task_id": task_id,
            "title": prompt_data.get("title", "Untitled"),
            "genre": genre,
            "prompt_data": prompt_data,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "clips": []
        }
        self.tasks["pending"].append(task)
        self._save_tasks()
        return task

    def get_pending_tasks(self) -> List[dict]:
        """진행 중인 작업 목록"""
        return self.tasks["pending"]

    def get_task(self, task_id: str) -> Optional[dict]:
        """특정 작업 조회"""
        for task in self.tasks["pending"]:
            if task["task_id"] == task_id:
                return task
        return None

    def complete_task(self, task_id: str, clips: List[dict]) -> Optional[dict]:
        """작업 완료 처리

        Args:
            task_id: 완료된 task ID
            clips: 생성된 클립 데이터 리스트

        Returns:
            완료된 작업 정보
        """
        task = None
        for i, t in enumerate(self.tasks["pending"]):
            if t["task_id"] == task_id:
                task = self.tasks["pending"].pop(i)
                break

        if task:
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["clips"] = clips
            self.tasks["completed"].append(task)
            self._save_tasks()

        return task

    def fail_task(self, task_id: str, error: str) -> Optional[dict]:
        """작업 실패 처리"""
        task = None
        for i, t in enumerate(self.tasks["pending"]):
            if t["task_id"] == task_id:
                task = self.tasks["pending"].pop(i)
                break

        if task:
            task["status"] = "failed"
            task["error"] = error
            task["completed_at"] = datetime.now().isoformat()
            self.tasks["completed"].append(task)
            self._save_tasks()

        return task

    def remove_task(self, task_id: str):
        """작업 제거"""
        self.tasks["pending"] = [
            t for t in self.tasks["pending"] if t["task_id"] != task_id
        ]
        self._save_tasks()

    def get_active_count(self) -> int:
        """현재 진행 중인 작업 수"""
        return len(self.tasks["pending"])

    def can_add_task(self) -> bool:
        """새 작업 추가 가능 여부"""
        return self.get_active_count() < config.MAX_PARALLEL_GENERATIONS

    def clear_old_completed(self, keep_days: int = 7):
        """오래된 완료 작업 정리"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=keep_days)

        self.tasks["completed"] = [
            t for t in self.tasks["completed"]
            if datetime.fromisoformat(t.get("completed_at", "2000-01-01")) > cutoff
        ]
        self._save_tasks()

    def get_recent_completed(self, count: int = 10) -> List[dict]:
        """최근 완료된 작업"""
        return sorted(
            self.tasks["completed"],
            key=lambda x: x.get("completed_at", ""),
            reverse=True
        )[:count]
