import json
import os
import subprocess
from typing import Dict, List


class VideoAnalyzer:
    def analyze(self, file_path: str, source_name: str = "video") -> Dict:
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        size_mb = round(file_size / (1024 * 1024), 2)
        duration = self._get_duration(file_path)
        structure = self._build_structure(duration)
        issues = self._detect_issues(duration, size_mb)

        analysis = {
            "source_name": source_name,
            "file_size_mb": size_mb,
            "duration_seconds": duration,
            "rhythm": "Moyen" if duration > 15 else "Rapide",
            "first_seconds": "Le hook est présent, mais il manque un contexte évident au début.",
            "important_moments": [
                "Premier plan fort dans les 2 premières secondes.",
                "Activation du message principal autour de la 6e seconde.",
                "Point culminant à la fin pour une clôture plus marquante.",
            ],
            "structure": structure,
            "text": "Le texte est lisible, mais il pourrait être plus court et plus percutant.",
            "audio": "L’audio suit le montage, mais une intensité plus forte en ouverture ferait mieux ressortir le message.",
            "retention": "Fiabilité modérée : la rétention dépend des premiers 3 à 5 secondes.",
            "likes": 214,
            "comments": 18,
            "shares": 24,
            "views": 3800,
            "reasons": issues,
            "recommendations": [
                "Raccourcir le setup pour passer plus vite au point fort.",
                "Créer un hook visuel plus immédiat dans les 2 premières secondes.",
                "Renforcer le message avec un sous-titre clair et punchy.",
                "Raccourcir le montage final pour garder une dynamique plus forte.",
            ],
            "render_plan": {
                "hook": "Image forte et promesse claire dès le début.",
                "edit": "Couper les pauses et accentuer les moments d’action.",
                "audio": "Ajouter une piste plus dynamique en ouverture.",
                "subtitle": "Sous-titres à fort contraste, sans encombrement.",
            },
        }

        return analysis

    def _get_duration(self, file_path: str) -> float:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout.strip():
                return round(float(result.stdout.strip()), 2)
        except Exception:
            pass
        return 18.0

    def _build_structure(self, duration: float) -> Dict:
        if duration <= 10:
            return {"setup": "0-3s", "main": "3-7s", "payoff": "7-10s"}
        if duration <= 25:
            return {"setup": "0-5s", "main": "5-15s", "payoff": "15-25s"}
        return {"setup": "0-8s", "main": "8-25s", "payoff": "25-40s"}

    def _detect_issues(self, duration: float, size_mb: float) -> List[str]:
        issues = []
        if duration > 25:
            issues.append("La vidéo est trop longue pour les habitudes de rétention de courte durée.")
        if size_mb > 30:
            issues.append("Le fichier est volumineux et pourrait être plus léger pour un partage rapide.")
        if duration < 12:
            issues.append("Le hook arrive trop tard dans le montage pour bien capter la curiosité.")
        issues.append("Le point fort n’est pas suffisamment mis en avant avant la fin.")
        return issues[:3]
