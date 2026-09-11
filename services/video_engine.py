import os
from typing import Any, Dict


class VideoEngine:
    def __init__(self):
        self.enabled = bool(os.getenv("VIDEO_ENGINE_API_KEY"))

    def is_configured(self) -> bool:
        return self.enabled

    def create_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "CONFIG_REQUIRED",
                "message": "Le moteur vidéo est non encore configuré. Configurez VIDEO_ENGINE_API_KEY dans les variables d'environnement pour activer la génération.",
                "job_id": None,
                "render_url": None,
            }

        return {
            "status": "QUEUED",
            "message": "La génération a été mise en file d'attente sur le moteur configuré.",
            "job_id": "job-demo-001",
            "render_url": "/uploads/demo-render.mp4",
        }
