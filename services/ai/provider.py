import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        raise NotImplementedError


class LocalAIProvider(AIProvider):
    def generate(self, prompt: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        mode = str(context.get("mode", "general")).lower()
        description = context.get("description") or prompt

        return {
            "title": self._title_for(mode, description),
            "hook": self._hook_for(mode),
            "script": self._script_for(mode, description),
            "hashtags": self._hashtags_for(mode),
            "description": self._description_for(mode, description),
            "shots": [
                {"time": "0-4s", "shot": "Hook visuel " + mode},
                {"time": "4-10s", "shot": "Développement du sujet"},
                {"time": "10-16s", "shot": "Point de tension"},
                {"time": "16-20s", "shot": "Payoff clair"},
            ],
            "voice_over": "Narration claire et dynamique",
            "captions": [
                "Hook fort",
                "Action centrale",
                "Fin impactante",
            ],
        }

    def _title_for(self, mode: str, description: str) -> str:
        cleaned = description.strip() or "Vidéo virale"
        if len(cleaned) > 54:
            cleaned = cleaned[:51].rstrip() + "..."
        return f"{mode.title()} — {cleaned}"

    def _hook_for(self, mode: str) -> str:
        mapping = {
            "dance": "Le mouvement commence par un changement instantané de rythme pour captiver en 2 secondes.",
            "gaming": "Le combo ou l’attaque surprise ouvre la vidéo immédiatement.",
            "story": "Une promesse claire et un moment de tension donnent envie de regarder la suite.",
            "humor": "Le contraste entre le setup et le punchline crée la réaction immédiate.",
            "3d": "La caméra plonge dans la scène et dévoile le monde 3D dès les premières secondes.",
            "short": "Le hook est ultra court, punchy et visuellement clair.",
        }
        return mapping.get(mode, "Une ouverture forte et immédiate pour capter l’attention dès la première seconde.")

    def _script_for(self, mode: str, description: str) -> str:
        return (
            f"Idée principale : {description}. "
            f"Structure : ouverture visuelle, narration courte, point de tension, payoff final et transition vers une fin mémorable."
        )

    def _hashtags_for(self, mode: str) -> List[str]:
        base = ["#viral", "#content", "#shorts", "#creator"]
        extras = {
            "dance": ["#dance", "#choreography", "#edm"],
            "gaming": ["#gaming", "#esports", "#freefire"],
            "story": ["#storytelling", "#cinema", "#hook"],
            "humor": ["#humor", "#comedy", "#funny"],
            "3d": ["#3d", "#blender", "#cyberpunk"],
            "short": ["#shorts", "#tiktok", "#reels"],
        }
        return base + extras.get(mode, ["#viralai"])[:3]

    def _description_for(self, mode: str, description: str) -> str:
        return (
            f"Concept {mode} optimisé pour la rétention. "
            f"Le contenu met en avant la promesse visuelle, le rythme et la clarté du message pour un résultat dynamique et lisible. "
            f"Description de départ : {description}."
        )


class AIProviderFactory:
    def __init__(self):
        self.provider_name = (os.getenv("AI_PROVIDER") or ("openai" if os.getenv("AI_API_KEY") else "local")).lower()

    def get_provider(self) -> AIProvider:
        provider_name = self.provider_name.lower()
        if provider_name == "openai":
            return OpenAIProvider()
        return LocalAIProvider()

    def is_real_provider_configured(self) -> bool:
        return bool(os.getenv("AI_API_KEY"))


class OpenAIProvider(AIProvider):
    def generate(self, prompt: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        api_key = os.getenv("AI_API_KEY")
        if not api_key:
            raise ValueError("AI_API_KEY is required to use the real AI provider.")

        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("requests is required for the real AI provider.") from exc

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("AI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es un directeur créatif vidéo. Réponds en JSON avec les clés title, hook, script, hashtags, description, shots, voice_over, captions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            },
            timeout=30,
        )

        if response.status_code >= 400:
            raise RuntimeError(f"AI provider error: {response.status_code} {response.text}")

        payload = response.json()
        message = payload["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(message)
        except json.JSONDecodeError:
            parsed = {
                "title": f"Concept — {context.get('description') or 'Vidéo'}",
                "hook": "Une ouverture forte et claire pour capter l’attention dès la première seconde.",
                "script": message,
                "hashtags": ["#viral", "#shorts", "#content"],
                "description": message,
                "shots": [{"time": "0-20s", "shot": "Scène principale"}],
                "voice_over": "Narration claire",
                "captions": ["Hook fort", "Action centrale", "Fin impactante"],
            }

        return {
            "title": parsed.get("title") or f"Concept — {context.get('description') or 'Vidéo'}",
            "hook": parsed.get("hook") or "Une ouverture forte et claire pour capter l’attention dès la première seconde.",
            "script": parsed.get("script") or prompt,
            "hashtags": parsed.get("hashtags") or ["#viral", "#shorts", "#content"],
            "description": parsed.get("description") or message,
            "shots": parsed.get("shots") or [{"time": "0-20s", "shot": "Scène principale"}],
            "voice_over": parsed.get("voice_over") or "Narration claire",
            "captions": parsed.get("captions") or ["Hook fort", "Action centrale", "Fin impactante"],
        }
