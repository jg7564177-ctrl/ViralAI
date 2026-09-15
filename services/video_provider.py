import os
from typing import Any, Dict

import requests


class BaseVideoProvider:
    name = "base"

    def __init__(self):
        self.api_key = os.getenv("VIDEO_PROVIDER_API_KEY")
        self.model = os.getenv("VIDEO_PROVIDER_MODEL", "minimax/video-01")
        self.base_url = "https://api.replicate.com/v1"
        self.timeout = 30

    def is_configured(self) -> bool:
        return False

    def submit_generation(self, prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "VIDEO_PROVIDER_NOT_CONFIGURED",
            "message": "Aucun moteur vidéo n’est configuré pour le moment. Ajoutez une clé et activez un fournisseur vidéo plus tard.",
            "job_id": None,
            "render_url": None,
        }

    def get_prediction_status(self, prediction_id: str) -> Dict[str, Any]:
        return {
            "status": "VIDEO_PROVIDER_NOT_CONFIGURED",
            "message": "Le fournisseur vidéo n’est pas activé.",
            "output": None,
        }

    def download_video(self, video_url: str, destination: str) -> str | None:
        return None


class DisabledVideoProvider(BaseVideoProvider):
    name = "disabled"

    def is_configured(self) -> bool:
        return False

    def submit_generation(self, prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "VIDEO_PROVIDER_NOT_CONFIGURED",
            "message": "VIDEO_PROVIDER_NOT_CONFIGURED: aucun moteur vidéo n’est activé pour le moment. L’API payante est temporairement désactivée.",
            "job_id": None,
            "render_url": None,
        }


class ReplicateVideoProvider(BaseVideoProvider):
    name = "replicate"

    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.model)

    def _aspect_ratio_for(self, format_value: str) -> str:
        mapping = {"9:16": "9:16", "16:9": "16:9", "1:1": "1:1"}
        return mapping.get((format_value or "9:16").strip(), "9:16")

    def _duration_for(self, duration: Any) -> int:
        try:
            value = int(duration or 10)
        except (TypeError, ValueError):
            value = 10
        if value < 5:
            return 5
        if value > 10:
            return 10
        return value

    def submit_generation(self, prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "VIDEO_PROVIDER_NOT_CONFIGURED",
                "message": "VIDEO_PROVIDER_NOT_CONFIGURED: configure VIDEO_PROVIDER_API_KEY et VIDEO_PROVIDER_MODEL pour appeler un fournisseur vidéo réel.",
                "job_id": None,
                "render_url": None,
            }

        try:
            response = requests.post(
                f"{self.base_url}/models/{self.model}/predictions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": {
                        "prompt": prompt,
                        "aspect_ratio": self._aspect_ratio_for(payload.get("format")),
                        "duration": self._duration_for(payload.get("duration")),
                        "style": payload.get("style") or "cinematic",
                        "mode": payload.get("mode") or "general",
                    }
                },
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                body = response.json() if response.content else {}
                message = body.get("error") or body.get("detail") or response.text
                return {"status": "FAILED", "message": f"Erreur fournisseur vidéo: {message}", "job_id": None, "render_url": None}

            prediction = response.json()
            job_id = prediction.get("id")
            if not job_id:
                return {"status": "FAILED", "message": "Erreur fournisseur vidéo: la réponse ne contient pas d'identifiant de génération.", "job_id": None, "render_url": None}

            return {"status": "QUEUED", "message": "La génération vidéo a été soumise au fournisseur officiel Replicate.", "job_id": job_id, "render_url": None}
        except requests.RequestException as exc:
            return {"status": "FAILED", "message": f"Erreur fournisseur vidéo: {exc}", "job_id": None, "render_url": None}

    def get_prediction_status(self, prediction_id: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {"status": "VIDEO_PROVIDER_NOT_CONFIGURED", "message": "VIDEO_PROVIDER_NOT_CONFIGURED: configure VIDEO_PROVIDER_API_KEY pour suivre le job.", "output": None}

        try:
            response = requests.get(
                f"{self.base_url}/predictions/{prediction_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                body = response.json() if response.content else {}
                message = body.get("error") or body.get("detail") or response.text
                return {"status": "FAILED", "message": f"Erreur fournisseur vidéo: {message}", "output": None}

            prediction = response.json()
            status = (prediction.get("status") or "unknown").upper()
            output = prediction.get("output")
            render_url = None
            if isinstance(output, list) and output:
                render_url = output[0]
            elif isinstance(output, str):
                render_url = output

            if status in {"SUCCEEDED", "COMPLETED"}:
                return {"status": "COMPLETED", "message": "Vidéo générée et prête à être récupérée.", "output": render_url}
            if status in {"FAILED", "CANCELED", "CANCELLED"}:
                error = prediction.get("error") or prediction.get("detail") or "La génération a échoué sans message détaillé."
                return {"status": "FAILED", "message": f"La génération a échoué: {error}", "output": None}
            if status in {"QUEUED", "PROCESSING", "STARTING"}:
                return {"status": "PROCESSING", "message": "Génération en cours sur le fournisseur vidéo.", "output": None}
            return {"status": "PROCESSING", "message": "Statut non finalisé pour le moment.", "output": None}
        except requests.RequestException as exc:
            return {"status": "FAILED", "message": f"Erreur fournisseur vidéo: {exc}", "output": None}

    def download_video(self, video_url: str, destination: str) -> str | None:
        if not video_url:
            return None
        try:
            response = requests.get(video_url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            with open(destination, "wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_handle.write(chunk)
            return destination
        except requests.RequestException:
            return None


class VideoProviderFactory:
    @staticmethod
    def build() -> BaseVideoProvider:
        provider_flag = os.getenv("VIDEO_PROVIDER_ENABLED", "false").strip().lower()
        api_key = os.getenv("VIDEO_PROVIDER_API_KEY") or os.getenv("AGNES_API_KEY")
        if provider_flag not in {"1", "true", "yes", "on"} or not api_key:
            return DisabledVideoProvider()
        provider_name = os.getenv("VIDEO_PROVIDER", "replicate").strip().lower()
        if provider_name == "agnes":
            return AgnesVideoProvider()
        return ReplicateVideoProvider()


class VideoProvider(DisabledVideoProvider):
    pass


class AgnesVideoProvider(BaseVideoProvider):
    """Fournisseur vidéo Agnes AI (tier gratuit, modèle agnes-video-v2.0)."""

    name = "agnes"
    API_BASE = "https://apihub.agnes-ai.com/v1/videos"

    def __init__(self) -> None:
        self.api_key = os.getenv("VIDEO_PROVIDER_API_KEY") or os.getenv("AGNES_API_KEY")
        self.model = os.getenv("VIDEO_PROVIDER_MODEL", "agnes-video-v2.0")
        self.timeout = int(os.getenv("VIDEO_PROVIDER_TIMEOUT", "120"))

    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.model)

    def _ratio_for(self, format_value: str) -> str:
        mapping = {"9:16": "9:16", "16:9": "16:9", "1:1": "1:1", "4:3": "4:3", "3:4": "3:4"}
        return mapping.get(str(format_value or "9:16"), "9:16")

    def _num_frames_for(self, duration) -> int:
        try:
            seconds = float(duration or 5)
        except (TypeError, ValueError):
            seconds = 5.0
        seconds = max(1.0, min(seconds, 60.0))
        target = int(round(seconds * 24))
        n = max(1, round((target - 1) / 8))
        return 8 * n + 1

    def submit_generation(self, prompt: str, payload):
        if not self.is_configured():
            return {
                "status": "VIDEO_PROVIDER_NOT_CONFIGURED",
                "message": "VIDEO_PROVIDER_NOT_CONFIGURED : aucune clé API vidéo disponible.",
                "job_id": None,
                "render_url": None,
            }
        try:
            body = {
                "model": self.model,
                "prompt": prompt,
                "num_frames": self._num_frames_for(payload.get("duration")),
                "frame_rate": 24,
                "ratio": self._ratio_for(payload.get("format")),
            }
            response = requests.post(
                self.API_BASE,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                try:
                    err = response.json()
                except Exception:
                    err = {}
                message = err.get("message") or err.get("error") or response.text
                return {"status": "FAILED", "message": f"Erreur fournisseur vidéo: {message}", "job_id": None, "render_url": None}
            data = response.json()
            job_id = data.get("id") or data.get("task_id")
            if not job_id:
                return {"status": "FAILED", "message": "Erreur fournisseur vidéo: identifiant de génération manquant.", "job_id": None, "render_url": None}
            return {
                "status": "QUEUED",
                "message": "La génération vidéo a été soumise au fournisseur Agnes AI.",
                "job_id": job_id,
                "render_url": None,
            }
        except requests.RequestException as exc:
            return {"status": "FAILED", "message": f"Erreur fournisseur vidéo: {exc}", "job_id": None, "render_url": None}

    def get_prediction_status(self, prediction_id: str):
        if not self.is_configured():
            return {
                "status": "VIDEO_PROVIDER_NOT_CONFIGURED",
                "message": "VIDEO_PROVIDER_NOT_CONFIGURED : aucune clé API vidéo disponible.",
                "output": None,
            }
        try:
            response = requests.get(
                f"{self.API_BASE}/{prediction_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                return {"status": "FAILED", "message": "La génération a échoué: tâche introuvable.", "output": None}
            data = response.json()
            status = str(data.get("status") or "").lower()
            if status in {"queued", "processing", "starting"}:
                return {"status": "PROCESSING", "message": "Génération en cours sur le fournisseur vidéo.", "output": None}
            if status in {"completed", "succeeded", "success"}:
                output_url = data.get("url") or data.get("video_url") or data.get("output")
                return {"status": "COMPLETED", "message": "Génération terminée.", "output": output_url}
            if status in {"failed", "error", "cancelled"}:
                err = data.get("error") or "Génération échouée"
                return {"status": "FAILED", "message": f"La génération a échoué: {err}", "output": None}
            return {"status": "PROCESSING", "message": "Statut non finalisé pour le moment.", "output": None}
        except requests.RequestException as exc:
            return {"status": "FAILED", "message": f"Erreur fournisseur vidéo: {exc}", "output": None}

    def download_video(self, video_url: str, destination: str):
        if not video_url:
            return None
        try:
            response = requests.get(video_url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            with open(destination, "wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_handle.write(chunk)
            return destination
        except requests.RequestException:
            return None
