from __future__ import annotations

from threading import Lock
from typing import Dict, List


VALID_JOB_STATUSES = {
    "QUEUED",
    "PROCESSING",
    "GENERATING",
    "RENDERING",
    "COMPLETED",
    "FAILED",
    "VIDEO_PROVIDER_NOT_CONFIGURED",
}


class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self._lock = Lock()

    def create_job(self, job_type: str, payload: Dict) -> Dict:
        job_id = f"job-{len(self.jobs) + 1}"
        job = {
            "id": job_id,
            "type": job_type,
            "status": "QUEUED",
            "progress": 0,
            "payload": payload,
            "message": "La génération est en attente de traitement.",
            "error": None,
            "output_url": None,
        }
        with self._lock:
            self.jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Dict | None:
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[Dict]:
        return list(self.jobs.values())

    def update_status(
        self,
        job_id: str,
        status: str,
        progress: int,
        message: str,
        *,
        error: str | None = None,
        output_url: str | None = None,
    ) -> Dict | None:
        job = self.jobs.get(job_id)
        if not job:
            return None
        if status not in VALID_JOB_STATUSES:
            raise ValueError(f"Statut de job invalide : {status}")
        job["status"] = status
        job["progress"] = progress
        job["message"] = message
        if error is not None:
            job["error"] = error
        if output_url is not None:
            job["output_url"] = output_url
        if error is None and "error" in job:
            job["error"] = None
        return job
