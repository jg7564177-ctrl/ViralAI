import os


class SocialOAuthService:
    def status(self):
        return {
            "tiktok": {
                "enabled": bool(os.getenv("TIKTOK_CLIENT_ID")),
                "label": "TikTok",
                "message": "Connexion OAuth sécurisée prête à être activée une fois les identifiants ajoutés.",
            },
            "youtube": {
                "enabled": bool(os.getenv("YOUTUBE_CLIENT_ID")),
                "label": "YouTube",
                "message": "Connexion OAuth sécurisée prête à être activée une fois les identifiants ajoutés.",
            },
        }
