from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


AGNES_CHAT_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODELS = (
    "groq/compound-mini",
    "groq/compound",
)


class AgnesChatError(RuntimeError):
    """A safe, user-facing Agnes failure without exposing credentials."""


@dataclass(frozen=True)
class AgnesReply:
    content: str
    model: str


class AgnesChatClient:
    """Small OpenAI-compatible client for Agnes AI chat completions."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip() or os.getenv("AGNES_API_KEY", "").strip()
        self.endpoint = os.getenv("AGNES_CHAT_ENDPOINT", AGNES_CHAT_ENDPOINT).strip()
        try:
            configured_timeout = int(os.getenv("AGNES_CHAT_TIMEOUT", "30"))
        except (TypeError, ValueError):
            configured_timeout = 30
        self.timeout = max(5, min(60, configured_timeout))
        self.session = session or requests.Session()
        configured_model = os.getenv("AGNES_CHAT_MODEL", "").strip()
        configured_fallbacks = [
            model.strip()
            for model in os.getenv("AGNES_CHAT_FALLBACK_MODELS", "").split(",")
            if model.strip()
        ]
        self.models = tuple(dict.fromkeys([
            *([configured_model] if configured_model else []),
            *configured_fallbacks,
            *DEFAULT_MODELS,
        ]))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def complete(
        self,
        message: str,
        context: list[dict[str, Any]] | None = None,
    ) -> AgnesReply:
        if not self.configured:
            raise AgnesChatError("AGNES_API_KEY is not configured.")

        messages = [{"role": "system", "content": self._system_prompt()}]
        for item in (context or [])[-8:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                messages.append({"role": role, "content": content.strip()[:4000]})
        messages.append({"role": "user", "content": message.strip()[:4000]})

        last_status = None
        for model in self.models:
            try:
                response = self.session.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 900,
                    },
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise AgnesChatError("Agnes AI est momentanément indisponible.") from exc

            last_status = response.status_code
            if response.status_code in {401, 403}:
                raise AgnesChatError("La clé Agnes AI est refusée ou expirée.")
            if response.status_code in {400, 404, 422}:
                # Agnes-compatible gateways can expose different model IDs.
                # Try the next configured candidate without logging the body.
                continue
            if response.status_code == 429 or response.status_code >= 500:
                # A gateway outage is not a model mismatch. Still probe the
                # remaining configured models before entering local fallback.
                continue
            if not response.ok:
                raise AgnesChatError("Agnes AI n'a pas pu traiter la demande.")

            content = self._extract_content(response.json())
            if content:
                return AgnesReply(content=content, model=model)

            raise AgnesChatError("Réponse vide reçue d'Agnes AI.")

        if last_status == 429 or (last_status is not None and last_status >= 500):
            raise AgnesChatError("Agnes AI est momentanément indisponible.")
        raise AgnesChatError(
            f"Aucun modèle Agnes compatible n'est disponible (dernier statut: {last_status})."
        )

    @staticmethod
    def _extract_content(payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content", first.get("text", ""))
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ]
            return "".join(parts).strip()
        return ""

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Tu es ViralAI, un assistant créatif spécialisé dans TikTok, YouTube Shorts "
            "et les vidéos verticales. Réponds en français, avec des conseils concrets, "
            "une structure claire et un ton direct mais chaleureux. Ne prétends jamais "
            "avoir vu une vidéo ou des statistiques qui ne t'ont pas été fournies."
        )