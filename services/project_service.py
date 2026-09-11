from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


class ProjectService:
    def __init__(self):
        self.projects: List[Dict[str, Any]] = []

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _format_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": project["id"],
            "user_id": project["user_id"],
            "name": project["name"],
            "prompt": project.get("prompt", ""),
            "type": project.get("type", project.get("name", "Vidéo")),
            "status": project.get("status", "draft"),
            "progress": project.get("progress", 0),
            "format": project.get("parameters", {}).get("format", "9:16"),
            "duration": project.get("parameters", {}).get("duration", 10),
            "style": project.get("parameters", {}).get("style", "cinematic"),
            "quality": project.get("parameters", {}).get("quality", "Standard"),
            "parameters": project.get("parameters", {}),
            "storyboard": project.get("storyboard", []),
            "created_at": project.get("created_at", self._utc_now()),
            "updated_at": project.get("updated_at", self._utc_now()),
        }

    def list_projects(self, user_id: str | None = None) -> List[Dict[str, Any]]:
        if user_id is None:
            return [self._format_project(project) for project in self.projects]
        return [self._format_project(project) for project in self.projects if project.get("user_id") == user_id]

    def get_project(self, project_id: str) -> Dict[str, Any] | None:
        for project in self.projects:
            if project["id"] == project_id:
                return self._format_project(project)
        return None

    def create_project(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = self._utc_now()
        parameters = {
            "format": payload.get("format") or "9:16",
            "duration": int(payload.get("duration") or 10),
            "style": payload.get("style") or "cinematic",
            "quality": payload.get("quality") or "Standard",
            "camera": payload.get("camera") or "tracking",
            "camera_motion": payload.get("camera_motion") or "smooth",
            "lighting": payload.get("lighting") or "neon",
            "mood": payload.get("mood") or "cinematic",
            "angle": payload.get("angle") or "medium",
            "fps": payload.get("fps") or 24,
            "resolution": payload.get("resolution") or "1080p",
            "seed": payload.get("seed") or None,
            "negative_prompt": payload.get("negative_prompt") or "",
        }

        storyboard = payload.get("storyboard") or [
            {
                "scene": 1,
                "description": payload.get("prompt") or "Scène ouverte",
                "duration": max(1, int(parameters["duration"]) // 2),
                "camera_motion": parameters["camera_motion"],
                "transition": "cut",
            }
        ]

        project = {
            "id": f"proj-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "name": payload.get("name") or "Nouvelle création",
            "prompt": payload.get("prompt") or "",
            "type": payload.get("type") or "Vidéo",
            "status": payload.get("status") or "draft",
            "progress": int(payload.get("progress") or 0),
            "parameters": parameters,
            "storyboard": storyboard,
            "created_at": now,
            "updated_at": now,
        }
        self.projects.insert(0, project)
        return self._format_project(project)

    def update_project(self, project_id: str, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        project = next((p for p in self.projects if p["id"] == project_id and p["user_id"] == user_id), None)
        if project is None:
            raise ValueError("PROJECT_NOT_FOUND")

        project["name"] = payload.get("name") or project.get("name")
        project["prompt"] = payload.get("prompt") or project.get("prompt") or ""
        project["original_idea"] = payload.get("original_idea") or project.get("original_idea") or project.get("prompt") or ""
        project["improved_idea"] = payload.get("improved_idea") or project.get("improved_idea") or project.get("prompt") or ""
        project["storyboard"] = payload.get("storyboard") or project.get("storyboard") or []
        project["parameters"] = {**project.get("parameters", {}), **(payload.get("parameters") or {})}
        project["status"] = payload.get("status") or project.get("status") or "draft"
        project["progress"] = int(payload.get("progress") or project.get("progress") or 0)
        project["ai_analysis"] = payload.get("ai_analysis") or project.get("ai_analysis") or {}
        project["updated_at"] = self._utc_now()
        return self._format_project(project)

    def generate_project(self, project_id: str, user_id: str) -> Dict[str, Any]:
        project = next((p for p in self.projects if p["id"] == project_id and p["user_id"] == user_id), None)
        if project is None:
            raise ValueError("PROJECT_NOT_FOUND")
        return {
            "status": "VIDEO_GENERATION_DISABLED",
            "message": "La génération vidéo est actuellement désactivée. Activez un moteur vidéo dans un environnement sécurisé pour lancer les rendus.",
            "project_id": project_id,
            "user_id": user_id,
            "progress": project.get("progress", 0),
        }
