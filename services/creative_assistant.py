from __future__ import annotations

import os
from typing import Any, Dict, List


class CreativeAssistant:
    def __init__(self):
        self.provider_configured = bool(os.getenv("AI_API_KEY"))

    def is_available(self) -> bool:
        return self.provider_configured

    def transform_idea(self, idea: str, platform: str = "TikTok") -> Dict[str, Any]:
        normalized = (idea or "").strip()
        if not normalized:
            return {"status": "invalid", "message": "Une idée est nécessaire pour générer une proposition de vidéo."}

        if not self.is_available():
            return {
                "status": "AI_UNAVAILABLE",
                "message": "Assistant IA indisponible — configurez le fournisseur ia côté serveur.",
            }

        title = self._title_for(normalized)
        concept = self._concept_for(normalized)
        hook = self._hook_for(normalized)
        video_prompt = self._video_prompt_for(normalized, concept, hook)
        storyboard = self._storyboard_for(normalized)
        scenes = self._scene_cards_for(storyboard)
        platform_options = {
            "TikTok": {
                "title": f"{title} — Hook immédiat",
                "description": "Plan vertical orienté rétention, sous-titres lisibles et montée d’intensité dans les 3 premières secondes.",
                "caption": f"{title} 🚀 {hook}",
                "hashtags": ["#tiktok", "#viral", "#shorts", "#creator"],
                "hook": hook,
                "format": "9:16",
            },
            "YouTube Shorts": {
                "title": f"{title} — impact visuel",
                "description": "Open strong, rythme narratif, payoff net pour capter les spectateurs dès le début.",
                "caption": f"{title} • {hook}",
                "hashtags": ["#shorts", "#youtube", "#viralcontent"],
                "hook": hook,
                "format": "9:16",
            },
            "Instagram Reels": {
                "title": f"{title} — montage social",
                "description": "Rythme éditorial, mouvement clair et narration courte pour maximiser la rétention.",
                "caption": f"{title} ✨ {hook}",
                "hashtags": ["#reels", "#instagram", "#contentcreator"],
                "hook": hook,
                "format": "9:16",
            },
        }

        return {
            "status": "ready",
            "title": title,
            "concept": concept,
            "hook": hook,
            "video_prompt": video_prompt,
            "storyboard": storyboard,
            "scenes": scenes,
            "ambiance": "luminosité contrastée, atmosphère immersive, palette visuelle premium",
            "style_visual": "cinématique, punchy, vertical, dynamique",
            "audio_suggestions": ["basse soutenue", "kick percussif", "transition synthétique", "sonorité dramatisée"],
            "text_on_screen": ["Hook immédiat", "Action centrale", "Impact final"],
            "caption": f"{title} — {hook}",
            "hashtags": ["#viral", "#creative", "#shorts"],
            "viral_score": {
                "hook": 88,
                "originality": 82,
                "retention_potential": 84,
                "social_potential": 86,
            },
            "platform_options": platform_options,
            "platform": platform,
        }

    def _title_for(self, idea: str) -> str:
        cleaned = idea.strip().replace("  ", " ")
        if len(cleaned) <= 48:
            return cleaned.title()
        return (cleaned[:45].rstrip() + "...").title()

    def _concept_for(self, idea: str) -> str:
        return (
            f"Une vidéo courte et immersive qui met en avant la tension, le rhythm et le payoff visuel de cette idée : {idea}. "
            "Le montage s’appuie sur un hook immédiat, une progression claire et une fin mémorable."
        )

    def _hook_for(self, idea: str) -> str:
        return (
            f"L’idée démarre sur un moment de surprise ou d’impact visuel : {idea}. "
            "L’attention est captée dès les premières secondes par le contraste, le mouvement et la promesse d’une progression forte."
        )

    def _video_prompt_for(self, idea: str, concept: str, hook: str) -> str:
        return (
            f"Vidéo verticale ultra dynamique, format 9:16, cinématique, punchy et premium. "
            f"Concept : {concept}. Hook : {hook}. "
            f"Scène principale : {idea}. "
            "Mouvement caméra fluide, lumière contrastée, ambiance immersive, texte sur écran lisible, montage rapide, fin mémorable."
        )

    def _storyboard_for(self, idea: str) -> List[Dict[str, Any]]:
        return [
            {
                "scene": 1,
                "title": "Hook",
                "description": f"L’ouverture pose immédiatement l’impact visuel de {idea}.",
                "duration": 4,
                "camera": "plan serré",
                "movement": "tracking rapide",
                "environment": "espace dynamique",
                "subject": "moment clé",
                "dialogue": "phrase d’accroche courte",
                "transition": "cut net",
            },
            {
                "scene": 2,
                "title": "Action",
                "description": "Le sujet principal se déploie avec une progression claire et une forte présence visuelle.",
                "duration": 5,
                "camera": "plan moyen",
                "movement": "dolly in",
                "environment": "lieu immersif",
                "subject": "action centrale",
                "dialogue": "énergie, tempo, tension",
                "transition": "match cut",
            },
            {
                "scene": 3,
                "title": "Moment fort",
                "description": "Le point de tension visuelle et émotionnelle crée un effet de surprise ou de satisfaction.",
                "duration": 5,
                "camera": "plan large",
                "movement": "panoramique",
                "environment": "scène amplifiée",
                "subject": "révélation",
                "dialogue": "phrase de tension",
                "transition": "flash",
            },
            {
                "scene": 4,
                "title": "Conclusion",
                "description": "Le payoff final conclut avec clarté et laisse un souvenir net dans l’esprit du spectateur.",
                "duration": 4,
                "camera": "plan final",
                "movement": "zoom soutenu",
                "environment": "fin visuelle forte",
                "subject": "payoff",
                "dialogue": "phrase finale courte",
                "transition": "fade out",
            },
        ]

    def _scene_cards_for(self, storyboard: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "title": scene["title"],
                "description": scene["description"],
                "duration": scene["duration"],
                "camera": scene["camera"],
                "movement": scene["movement"],
                "environment": scene["environment"],
                "subject": scene["subject"],
                "dialogue": scene["dialogue"],
                "transition": scene["transition"],
            }
            for scene in storyboard
        ]
