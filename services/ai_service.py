import re
from typing import Dict, List


class AIChatService:
    def reply(self, message: str, context: list[dict] | None = None) -> str:
        text = (message or "").strip()
        lowered = text.lower()

        if not text:
            return "Peux-tu préciser ce que tu veux créer ?"

        prior_context = ""
        if context:
            recent = [item.get("content", "") for item in context[-4:] if item.get("content")]
            if recent:
                prior_context = " Contexte récent : " + " | ".join(recent)

        if "danse" in lowered:
            return (
                "J’ai un concept de danse de 20 secondes, très punchy : ouverture sur un mouvement de tête dans un environnement futuriste, "
                "puis un hook visuel sur le rythme, suivi d’un changement de costume et d’un dernier mouvement qui marque la fin. "
                "Le plan est pensé pour capter l’attention dans les 2 premières secondes et garder le rythme jusqu’à la fin." + prior_context
            )

        if "analyse" in lowered or "march" in lowered or "n'a pas" in lowered or "retention" in lowered:
            return (
                "Je regarderais d’abord le hook des 2 premières secondes, la durée de la scène de setup, puis la tension avant le point culminant. "
                "Une vidéo qui n’a pas marché a souvent un début lent, trop de texte au début ou un message trop diffus. "
                "Je peux te donner une version plus directe avec un meilleur hook, des sous-titres plus lisibles et un montage plus rapide." + prior_context
            )

        if "short" in lowered or "tiktok" in lowered or "youtube" in lowered:
            return (
                "Pour un Short, je te recommande : 0-2 s = hook fort, 2-6 s = action claire, 6-12 s = intensité, 12-20 s = payoff. "
                "Le format vertical, les sous-titres nets et une fin surprenante améliorent la rétention." + prior_context
            )

        if "idée" in lowered or "idee" in lowered:
            return (
                "Voici 5 idées : 1) une transformation avant/après en 10 secondes, 2) un challenge de mouvement viral, "
                "3) un montage de gameplay ultra-rapide avec hook sonore, 4) une scène 3D futuriste avec rotation caméra, 5) une réaction humoristique sur une tendance." + prior_context
            )

        if "gaming" in lowered or "jeu" in lowered:
            return (
                "Je peux te préparer une vidéo gaming avec un hook de gameplay, un montage ultra rapide, une voix off dynamique et une fin qui pousse à la suite. "
                "Le style visuel : nettet, mouvement, lumière, écart de plan sur les moments de boss ou de combo." + prior_context
            )

        if "3d" in lowered or "blender" in lowered or "scene" in lowered:
            return (
                "Pour une scène 3D, je te conseille une ouverture drone, des éléments dynamiques en mouvement, une lumière contrastée et un plan final qui met en valeur le sujet. "
                "Cela donne de la profondeur et un rendu premium avant même d’ajouter la musique." + prior_context
            )

        if "transforme" in lowered or "recr" in lowered or "ameli" in lowered:
            return (
                "Je peux transformer l’ancienne vidéo en une version plus forte : meilleur hook, rythmique plus intense, sous-titres plus lisibles, coupe plus précise, et CTA plus claire. "
                "La nouvelle version cible la rétention sur les premières secondes et un message plus net avant 8 secondes." + prior_context
            )

        return (
            "J’ai bien compris la direction. Je peux te proposer un concept, un plan de tournage, une structure de montage et des recommandations pour maximiser la rétention. "
            "Donne-moi le thème, la durée et le format et je te prépare une version prête à utiliser." + prior_context
        )


class ScenarioGenerator:
    def build_scenario(self, description: str, duration: int, format: str, style: str, music: str = "énergétique", voice: str = "voix claire", subtitles: bool = True, quality: str = "HD") -> Dict:
        title = self._title_from_description(description)
        shots = [
            {
                "time": "0-3s",
                "shot": "Hook visuel immédiat : cadrage serré, mouvement rapide, phrase de mise en tension.",
            },
            {
                "time": "3-8s",
                "shot": "Présenter le sujet avec un plan large et un message clair en 1 phrase.",
            },
            {
                "time": "8-14s",
                "shot": "Montage dynamique, accélération du rythme et mise en avant de l’action principale.",
            },
            {
                "time": "14-20s",
                "shot": "Payoff visuel, objet de surprise ou fin avec appel à l’action.",
            },
        ]

        return {
            "title": title,
            "format": format,
            "duration": duration,
            "style": style,
            "music": music,
            "voice": voice,
            "subtitles": subtitles,
            "quality": quality,
            "hook": "Commence par une scène qui pose immédiatement la promesse de la vidéo.",
            "narrative": f"Une structure {duration} secondes pensée pour attirer l’attention, maintenir l’intérêt et finir fort.",
            "shots": shots,
            "cta": "Laisse un dernier mot fort ou une fin ouverte pour inciter au replay.",
            "platform_note": "Optimisé pour des formats verticaux avec un équilibre entre mouvement, texte lisible et rythme de montage.",
        }

    def _title_from_description(self, description: str) -> str:
        cleaned = re.sub(r"\s+", " ", (description or "Vidéo virale").strip())
        if len(cleaned) > 60:
            cleaned = cleaned[:57].rstrip() + "..."
        return cleaned
