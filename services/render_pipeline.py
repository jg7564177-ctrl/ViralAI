class RenderPipeline:
    def get_pipeline(self, mode: str = "video") -> dict:
        if mode == "3d":
            return {
                "title": "Pipeline 3D Blender",
                "steps": [
                    "Créer la scène Blender côté serveur",
                    "Générer les caméras et lumières",
                    "Rendre la séquence en vidéo",
                    "Exporter le rendu final avec sous-titres",
                ],
            }

        return {
            "title": "Pipeline de création vidéo",
            "steps": [
                "Générer le script et la structure",
                "Analyser les métriques de performance",
                "Réaliser le montage adapté à la plateforme",
                "Préparer la version finale pour TikTok ou YouTube",
            ],
        }
