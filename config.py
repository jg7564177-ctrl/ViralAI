import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "jpg", "jpeg", "png"}
    VIDEO_PROVIDER = os.getenv("VIDEO_PROVIDER", "disabled")
    ALLOW_PAID_VIDEO = os.getenv("ALLOW_PAID_VIDEO", "false").strip().lower() in {"1", "true", "yes", "on"}
    PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "not_configured")
    OAUTH_PROVIDERS = {
        "tiktok": {
            "enabled": bool(os.getenv("TIKTOK_CLIENT_ID")),
            "name": "TikTok",
            "message": "Connexion OAuth sécurisée prête à brancher le client Id depuis les variables d’environnement.",
        },
        "youtube": {
            "enabled": bool(os.getenv("YOUTUBE_CLIENT_ID")),
            "name": "YouTube",
            "message": "Connexion OAuth sécurisée prête à brancher le client Id depuis les variables d’environnement.",
        },
    }


os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
