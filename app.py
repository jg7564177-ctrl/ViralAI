from __future__ import annotations

import os
import time
from collections import defaultdict

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

load_dotenv()

from config import Config
from services.account_service import AccountService
from services.ai.brain import AIBrain
from services.ai_service import AIChatService, ScenarioGenerator
from services.chat_service import ChatConversationService
from services.creative_assistant import CreativeAssistant
from services.job_manager import JobManager
from services.project_service import ProjectService
from services.render_pipeline import RenderPipeline
from services.social_oauth import SocialOAuthService
from services.video_analysis import VideoAnalyzer
from services.video_provider import VideoProviderFactory

app = Flask(__name__)


@app.after_request
def add_header(response):
    if 'service-worker.js' in response.headers.get('Content-Type', '') or 'service-worker.js' in str(getattr(response, 'location', '')):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


app.config.from_object(Config)

chat_service = AIChatService()
conversation_service = ChatConversationService()
scenario_service = ScenarioGenerator()
project_service = ProjectService()
analyzer = VideoAnalyzer()
render_pipeline = RenderPipeline()
social_oauth = SocialOAuthService()
ai_brain_service = AIBrain()
job_manager = JobManager()
account_service = AccountService()
video_provider = VideoProviderFactory.build()
creative_assistant = CreativeAssistant()
ADMIN_ATTEMPTS = defaultdict(list)


def get_request_user_id() -> str:
    return (request.headers.get("X-User-Id") or request.args.get("user_id") or "").strip()


def reject_admin_access():
    user_id = get_request_user_id() or request.remote_addr or "unknown"
    now = time.time()
    bucket = ADMIN_ATTEMPTS[user_id]
    bucket[:] = [stamp for stamp in bucket if now - stamp < 300]
    bucket.append(now)
    if len(bucket) >= 5:
        return jsonify({"error": "Access denied."}), 403
    return jsonify({"error": "Access denied."}), 403


@app.route("/kill-sw")
def kill_sw():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Reset ViralAI</title>
<style>body{background:#0a0a12;color:#e8e8f0;font-family:system-ui;padding:40px 20px;text-align:center}
h1{color:#a855f7;font-size:20px} p{margin:20px 0;font-size:14px;line-height:1.6}
button{background:linear-gradient(135deg,#a855f7,#ec4899);color:#fff;border:0;padding:16px 32px;border-radius:12px;font-size:16px;font-weight:700;cursor:pointer}
.ok{color:#22c55e;font-weight:700}</style></head>
<body><h1>Reset ViralAI</h1>
<p id="msg">Suppression du cache et du service worker...</p>
<button onclick="location.href='/studio'">Aller au Studio</button>
<script>
(async()=>{
  try{
    const regs = await navigator.serviceWorker.getRegistrations();
    for(const r of regs) await r.unregister();
    const keys = await caches.keys();
    await Promise.all(keys.map(k=>caches.delete(k)));
    document.getElementById('msg').innerHTML = '<span class="ok">OK</span> Cache supprime. Clique ci-dessous.';
  }catch(e){document.getElementById('msg').textContent='Erreur: '+e.message;}
})();
</script></body></html>"""


@app.route("/studio")
def studio():
    return render_template("studio.html")


@app.route("/")
def home():
    return render_template(
        "index.html",
        title="ViralAI",
        app_name="ViralAI",
        home_prompt="Que veux-tu créer aujourd'hui ?",
    )


@app.route("/landing")
def landing():
    return render_template(
        "landing.html",
        title="ViralAI | Studio IA",
        app_name="ViralAI",
        cta_text="Essayer ViralAI",
    )


@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")


@app.route("/service-worker.js")
def service_worker():
    return send_from_directory(app.static_folder, "service-worker.js", mimetype="application/javascript")


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message vide."}), 400

    conversation_id = payload.get("conversation_id")
    context = []
    if conversation_id:
        requester_id = get_request_user_id()
        if not requester_id:
            return jsonify({"error": "Access denied."}), 403
        conversation = conversation_service.get_conversation(conversation_id, requester_id)
        if conversation is None:
            return jsonify({"error": "Conversation introuvable."}), 404
        context = conversation.get("messages", [])[-8:]

    result = chat_service.reply_with_metadata(message, context=context)
    return jsonify(result)


@app.route("/api/chat/conversations", methods=["POST"])
def create_chat_conversation():
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "Nouvelle conversation").strip() or "Nouvelle conversation"
    conversation = conversation_service.create_conversation(requester_id, title=title)
    return jsonify({"conversation": conversation})


@app.route("/api/chat/conversations")
def list_chat_conversations():
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403
    return jsonify({"conversations": conversation_service.list_conversations(requester_id)})


@app.route("/api/chat/conversations/<conversation_id>")
def get_chat_conversation(conversation_id: str):
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    conversation = conversation_service.get_conversation(conversation_id, requester_id)
    if conversation is None:
        return jsonify({"error": "Conversation introuvable."}), 404
    return jsonify({"conversation": conversation})


@app.route("/api/chat/conversations/<conversation_id>", methods=["DELETE"])
def delete_chat_conversation(conversation_id: str):
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    deleted = conversation_service.delete_conversation(conversation_id, requester_id)
    if not deleted:
        return jsonify({"error": "Access denied."}), 403
    return jsonify({"status": "deleted"})


@app.route("/api/chat/conversations/<conversation_id>/messages", methods=["POST"])
def create_chat_message(conversation_id: str):
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    conversation = conversation_service.get_conversation(conversation_id, requester_id)
    if conversation is None:
        return jsonify({"error": "Conversation introuvable."}), 404

    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "user").strip().lower()
    content = (payload.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Message vide."}), 400

    try:
        message = conversation_service.add_message(conversation_id, requester_id, role, content, payload.get("timestamp"))
    except ValueError:
        return jsonify({"error": "Message vide."}), 400

    ai_reply = None
    if role == "user":
        context = conversation_service.get_context(conversation_id, requester_id, limit=8)
        ai_reply = chat_service.reply_with_metadata(content, context=context)["response"]
        conversation_service.add_message(conversation_id, requester_id, "assistant", ai_reply)

    return jsonify({"message": message, "assistant_reply": ai_reply})


@app.route("/api/generate-scenario", methods=["POST"])
def generate_scenario():
    payload = request.get_json(silent=True) or {}
    description = payload.get("description") or "Vidéo virale"
    duration = int(payload.get("duration") or 20)
    format_type = payload.get("format") or "9:16"
    style = payload.get("style") or "énergétique"
    music = payload.get("music") or "énergétique"
    voice = payload.get("voice") or "voix claire"
    subtitles = bool(payload.get("subtitles", True))
    quality = payload.get("quality") or "HD"

    scenario = scenario_service.build_scenario(
        description=description,
        duration=duration,
        format=format_type,
        style=style,
        music=music,
        voice=voice,
        subtitles=subtitles,
        quality=quality,
    )
    return jsonify(scenario)


@app.route("/api/ai/brain", methods=["POST"])
def ai_brain_route():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip() or "Crée une idée de vidéo virale."
    mode = (payload.get("mode") or "general").lower()
    result = ai_brain_service.process(message, mode=mode)
    return jsonify(result)


@app.route("/api/video/jobs", methods=["POST"])
def create_video_job():
    payload = request.get_json(silent=True) or {}
    description = payload.get("description") or "Vidéo courte"
    mode = payload.get("mode") or "general"

    job = job_manager.create_job("video_generation", {
        "description": description,
        "duration": int(payload.get("duration") or 10),
        "format": payload.get("format") or "9:16",
        "style": payload.get("style") or "énergétique",
        "mode": mode,
    })

    provider_result = video_provider.submit_generation(
        prompt=description,
        payload=job["payload"],
    )

    job["provider_job_id"] = provider_result.get("job_id")
    job["render_url"] = provider_result.get("render_url")

    if provider_result.get("status") == "VIDEO_PROVIDER_NOT_CONFIGURED":
        job_manager.update_status(
            job["id"], "FAILED", 0,
            provider_result["message"],
            error=provider_result["message"],
            output_url=None,
        )
        return jsonify({
            "job_id": job["id"],
            "status": "VIDEO_PROVIDER_NOT_CONFIGURED",
            "message": provider_result["message"],
            "engine": "not_configured",
            "progress": 0,
        })

    if provider_result.get("status") == "FAILED":
        job_manager.update_status(
            job["id"], "FAILED", 0,
            provider_result["message"],
            error=provider_result["message"],
            output_url=None,
        )
        return jsonify({
            "job_id": job["id"],
            "status": "FAILED",
            "message": provider_result["message"],
            "engine": "failed",
            "progress": 0,
        })

    job_manager.update_status(
        job["id"], "QUEUED", 10,
        provider_result.get("message", "Job créé."),
        output_url=provider_result.get("render_url"),
    )
    return jsonify({
        "job_id": job["id"],
        "status": "QUEUED",
        "message": provider_result.get("message", "Job créé."),
        "engine": "configured",
        "render_url": provider_result.get("render_url"),
        "progress": 10,
        "provider_job_id": provider_result.get("job_id"),
    })


@app.route("/api/video/jobs")
def list_video_jobs():
    return jsonify({"jobs": job_manager.list_jobs()})


@app.route("/api/video/jobs/<job_id>")
def get_video_job(job_id):
    job = job_manager.get_job(job_id)
    if not job:
        return jsonify({"error": "Job introuvable."}), 404

    provider_job_id = job.get("provider_job_id")
    if provider_job_id:
        # Cache : on n'interroge Agnes que toutes les 20 secondes pour éviter le rate limit
        now = time.time()
        last_check = job.get("_last_check", 0)
        cached = job.get("_cached_state")
        if cached and (now - last_check) < 20:
            provider_state = cached
        else:
            provider_state = video_provider.get_prediction_status(provider_job_id)
            job["_last_check"] = now
            job["_cached_state"] = provider_state

        if provider_state["status"] == "COMPLETED":
            job_manager.update_status(
                job_id, "COMPLETED", 100,
                "Vidéo générée et récupérable.",
                output_url=provider_state.get("output"),
            )
            job = job_manager.get_job(job_id)
        elif provider_state["status"] == "PROCESSING":
            real_progress = provider_state.get("progress", 50)
            try:
                real_progress = int(real_progress)
            except (TypeError, ValueError):
                real_progress = 50
            if real_progress < 10:
                real_progress = 10
            job_manager.update_status(
                job_id, "PROCESSING", real_progress,
                provider_state.get("message", "Génération en cours."),
            )
            job = job_manager.get_job(job_id)
        elif provider_state["status"] == "FAILED":
            job_manager.update_status(
                job_id, "FAILED", 0,
                provider_state.get("message", "La génération a échoué."),
                error=provider_state.get("message", "La génération a échoué."),
            )
            job = job_manager.get_job(job_id)

    return jsonify(job)


@app.route("/api/video/jobs/<job_id>/result")
def get_video_job_result(job_id):
    job = job_manager.get_job(job_id)
    if not job:
        return jsonify({"error": "Job introuvable."}), 404

    if job.get("status") != "COMPLETED":
        return jsonify({"status": job.get("status"), "message": "La vidéo n'est pas encore prête."})

    output_url = job.get("output_url")
    if not output_url:
        return jsonify({"status": "FAILED", "message": "La vidéo n'a pas été récupérée du fournisseur."})

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    target_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}.mp4")
    stored = video_provider.download_video(output_url, target_path)
    if not stored:
        return jsonify({"status": "FAILED", "message": "La vidéo a été générée mais n'a pas pu être récupérée."})

    return jsonify({
        "status": "COMPLETED",
        "message": "Vidéo récupérée et stockée avec succès.",
        "file_path": stored,
        "url": "/uploads/" + os.path.basename(stored),
    })


@app.route("/api/analyze-video", methods=["POST"])
def analyze_video():
    if "video" not in request.files:
        return jsonify({"error": "Aucune vidéo fournie."}), 400

    video_file = request.files["video"]
    if not video_file or video_file.filename == "":
        return jsonify({"error": "Aucun fichier sélectionné."}), 400

    filename = video_file.filename
    safe_name = os.path.basename(filename)
    upload_folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, safe_name)
    video_file.save(file_path)

    analysis = analyzer.analyze(file_path=file_path, source_name=safe_name)
    return jsonify(analysis)


@app.route("/api/register", methods=["POST"])
def register_account():
    payload = request.get_json(silent=True) or {}
    user_id = (payload.get("user_id") or payload.get("username") or "").strip()
    name = (payload.get("name") or user_id or "Nouvel utilisateur").strip()

    if not user_id:
        return jsonify({"error": "Invalid account."}), 400

    if account_service.get_account(user_id):
        return jsonify({"error": "Account already exists."}), 409

    role = payload.get("role", "USER")
    if str(role).upper() not in {"USER"}:
        role = "USER"

    account = account_service.create_user(user_id, name, role=role)
    return jsonify({"account": account.to_safe_dict()})


@app.route("/api/projects")
def get_projects():
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    if account_service.is_admin(requester_id):
        return jsonify({"projects": project_service.list_projects()})

    return jsonify({"projects": project_service.list_projects(requester_id)})


@app.route("/api/projects", methods=["POST"])
def create_project():
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    payload = request.get_json(silent=True) or {}
    project = project_service.create_project(requester_id, payload)
    return jsonify({"project": project})


@app.route("/api/projects/<project_id>")
def get_project(project_id: str):
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    project = project_service.get_project(project_id)
    if project is None:
        return jsonify({"error": "Access denied."}), 403

    if account_service.is_admin(requester_id):
        return jsonify({"project": project})

    if project["user_id"] != requester_id:
        return jsonify({"error": "Access denied."}), 403

    return jsonify({"project": project})


@app.route("/api/projects/<project_id>/generate", methods=["POST"])
def generate_project(project_id: str):
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    project = project_service.get_project(project_id)
    if project is None:
        return jsonify({"error": "Access denied."}), 403

    if not account_service.is_admin(requester_id) and project["user_id"] != requester_id:
        return jsonify({"error": "Access denied."}), 403

    return jsonify(project_service.generate_project(project_id, requester_id))


@app.route("/api/creative/transform", methods=["POST"])
def creative_transform():
    payload = request.get_json(silent=True) or {}
    idea = (payload.get("idea") or "").strip()
    platform = payload.get("platform") or "TikTok"
    if not idea:
        return jsonify({"status": "invalid", "message": "Une idée est nécessaire pour générer une proposition de vidéo."})
    result = creative_assistant.transform_idea(idea, platform=platform)
    return jsonify(result)


@app.route("/api/chat/video-prompt", methods=["POST"])
def chat_video_prompt():
    payload = request.get_json(silent=True) or {}
    idea = (payload.get("idea") or payload.get("message") or "").strip()
    if not idea:
        return jsonify({"error": "Message vide."}), 400

    idea_result = creative_assistant.transform_idea(idea, platform=payload.get("platform") or "TikTok")
    if idea_result.get("status") == "AI_UNAVAILABLE":
        return jsonify({
            "status": "AI_UNAVAILABLE",
            "message": "Assistant IA indisponible — configurez le fournisseur IA côté serveur.",
            "prompt": None,
        })

    output = {
        "title": idea_result.get("title") or "Concept vidéo",
        "hook": idea_result.get("hook") or "Hook d'ouverture",
        "prompt": idea_result.get("video_prompt") or idea,
        "style": idea_result.get("style_visual") or "cinématique",
        "camera": "tracking shot",
        "scenes": idea_result.get("storyboard") or [],
    }
    return jsonify(output)


@app.route("/api/chat/projects/from-message", methods=["POST"])
def create_project_from_chat_message():
    requester_id = get_request_user_id()
    if not requester_id:
        return jsonify({"error": "Access denied."}), 403

    payload = request.get_json(silent=True) or {}
    idea = (payload.get("idea") or payload.get("message") or "").strip()
    conversation_id = payload.get("conversation_id")
    if not idea:
        return jsonify({"error": "Message vide."}), 400

    creative = creative_assistant.transform_idea(idea, platform=payload.get("platform") or "TikTok")
    if creative.get("status") == "AI_UNAVAILABLE":
        return jsonify({"status": "AI_UNAVAILABLE", "message": "Assistant IA indisponible — configurez le fournisseur IA côté serveur."})

    p
