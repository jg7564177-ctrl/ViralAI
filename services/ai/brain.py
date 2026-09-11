from typing import Any, Dict, List

from services.ai.provider import AIProviderFactory


class AIBrain:
    def __init__(self):
        self.provider_factory = AIProviderFactory()

    def process(self, message: str, mode: str = "general") -> Dict[str, Any]:
        provider = self.provider_factory.get_provider()
        context = {"mode": mode, "description": message}
        result = provider.generate(message, context=context)

        story = self._build_storyboard(message, mode)
        scene_prompts = self._build_scene_prompts(message, mode, result)

        return {
            "mode": mode,
            "title": result["title"],
            "hook": result["hook"],
            "script": result["script"],
            "description": result["description"],
            "hashtags": result["hashtags"],
            "storyboard": story,
            "scenes": scene_prompts,
            "shots": result["shots"],
            "voice_over": result["voice_over"],
            "captions": result["captions"],
            "video_prompt": self._build_video_prompt(message, mode, result),
            "summary": self._summary_for(mode, message),
        }

    def _build_storyboard(self, message: str, mode: str) -> list[dict]:
        return [
            {"scene": 1, "time": "0-4s", "description": f"Hook visuel immédiat pour {message}", "visual": "Plan serré, mouvement rapide, lumière forte"},
            {"scene": 2, "time": "4-10s", "description": f"Développement du concept {mode}", "visual": "Plan moyen, cadrage dynamique, élément central visible"},
            {"scene": 3, "time": "10-16s", "description": "Mise en tension et intensité", "visual": "Transition rapide, contraste, rythme soutenu"},
            {"scene": 4, "time": "16-20s", "description": "Payoff final mémorable", "visual": "Dernier plan net, lumière, fin forte"},
        ]

    def _build_scene_prompts(self, message: str, mode: str, result: Dict[str, Any]) -> list[str]:
        return [
            f"Scene 1: {result['hook']} - {message}",
            f"Scene 2: Montrez le sujet principal dans un environnement {mode} riche et immersif.",
            f"Scene 3: Créez une transition rapide vers un point de tension visuelle fort.",
            f"Scene 4: Finnez sur un payoff net, dynamique et mémorable avec sous-titres lisibles."
        ]

    def _build_video_prompt(self, message: str, mode: str, result: Dict[str, Any]) -> str:
        return (
            f"Vidéo verticale, format 9:16, {mode}, ultra dynamique. "
            f"Prompt: {message}. Hook: {result['hook']}. "
            f"Structure: {result['script']}. Palette visuelle premium, lumière dramatique, mouvement fluide, sous-titres lisibles."
        )

    def _summary_for(self, mode: str, message: str) -> str:
        return (
            f"Concept {mode} préparé à partir de la demande suivante : {message}. "
            "Le plan met l’accent sur le hook, la structure, le montage et la fin pour améliorer la rétention."
        )
