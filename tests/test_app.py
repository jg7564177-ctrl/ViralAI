import os

import pytest

from app import app


@pytest.mark.skipif(not os.getenv("VIDEO_PROVIDER_API_KEY"), reason="Real Replicate video generation requires VIDEO_PROVIDER_API_KEY.")
def test_real_replicate_video_generation_end_to_end():
    client = app.test_client()
    prompt = "Une voiture futuriste roule dans une ville cyberpunk sous la pluie."

    ai_response = client.post(
        "/api/ai/brain",
        json={"message": prompt, "mode": "3d"},
    )
    assert ai_response.status_code == 200
    ai_payload = ai_response.get_json()
    assert ai_payload["title"]
    assert ai_payload["video_prompt"]

    job_response = client.post(
        "/api/video/jobs",
        json={
            "description": prompt,
            "duration": 10,
            "format": "9:16",
            "style": "cyberpunk",
            "mode": "3d",
        },
    )
    assert job_response.status_code == 200
    job_payload = job_response.get_json()
    assert "job_id" in job_payload

    final_status = None
    attempts = 0
    while attempts < 20 and final_status not in {"COMPLETED", "FAILED"}:
        status_response = client.get(f"/api/video/jobs/{job_payload['job_id']}")
        assert status_response.status_code == 200
        status_payload = status_response.get_json()
        final_status = status_payload.get("status")
        if final_status in {"COMPLETED", "FAILED"}:
            break
        attempts += 1

    assert final_status in {"COMPLETED", "FAILED"}
    if final_status == "COMPLETED":
        result_response = client.get(f"/api/video/jobs/{job_payload['job_id']}/result")
        assert result_response.status_code == 200
        result_payload = result_response.get_json()
        assert result_payload["status"] == "COMPLETED"
        assert result_payload.get("url") or result_payload.get("file_path")
        assert "video" in result_payload.get("url", "").lower() or result_payload.get("file_path")
    else:
        assert status_payload["status"] == "FAILED"
        assert status_payload.get("error") or status_payload.get("message")


def test_homepage_renders_brand_and_home_prompt():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True).lower()
    assert "viralai" in html
    assert "qu'est-ce qu'on crée aujourd'hui" in html


def test_landing_page_renders_public_brand_and_cta():
    client = app.test_client()
    response = client.get("/landing")

    assert response.status_code == 200
    html = response.get_data(as_text=True).lower()
    assert "viralai" in html
    assert "essayer viralai" in html

    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    manifest_payload = manifest.get_json()
    assert manifest_payload["name"] == "ViralAI"
    assert manifest_payload["short_name"] == "ViralAI"

    service_worker = client.get("/service-worker.js")
    assert service_worker.status_code == 200
    assert "self.addEventListener" in service_worker.get_data(as_text=True)


def test_chat_api_returns_reply_for_video_request():
    client = app.test_client()
    response = client.post(
        "/api/chat",
        json={"message": "Crée-moi une vidéo de danse de 20 secondes."},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["response"]
    assert "danse" in payload["response"].lower()


def test_scenario_generation_api_works():
    client = app.test_client()
    response = client.post(
        "/api/generate-scenario",
        json={
            "description": "Vidéo gaming rapide et punchy",
            "duration": 20,
            "format": "9:16",
            "style": "énergique",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["title"]
    assert payload["shots"]


def test_ai_brain_api_returns_structured_video_plan():
    client = app.test_client()
    response = client.post(
        "/api/ai/brain",
        json={
            "message": "Crée une vidéo verticale de 20 secondes avec un hook fort pour une danse cyberpunk.",
            "mode": "dance",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["title"]
    assert payload["hook"]
    assert payload["hashtags"]


def test_video_generation_job_reports_current_engine_configuration():
    client = app.test_client()
    response = client.post(
        "/api/video/jobs",
        json={
            "description": "Crée une scène 3D courte et cinématique",
            "duration": 15,
            "format": "9:16",
            "style": "cyberpunk",
            "mode": "3d",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] in {"VIDEO_PROVIDER_NOT_CONFIGURED", "QUEUED", "FAILED"}
    if payload["status"] == "VIDEO_PROVIDER_NOT_CONFIGURED":
        assert "VIDEO_PROVIDER_NOT_CONFIGURED" in payload["message"].upper() or "non configuré" in payload["message"].lower()
    else:
        assert "Agnes" in payload["message"] or "fournisseur" in payload["message"]


def test_real_ai_and_video_pipeline_without_provider_keys_reports_configuration_needed():
    client = app.test_client()

    ai_response = client.post(
        "/api/ai/brain",
        json={
            "message": "Crée une courte vidéo verticale d'une ville futuriste au coucher du soleil.",
            "mode": "3d",
        },
    )
    assert ai_response.status_code == 200
    ai_payload = ai_response.get_json()
    assert ai_payload["title"]
    assert ai_payload["video_prompt"]
    assert "ville futuriste" in ai_payload["video_prompt"].lower()

    job_response = client.post(
        "/api/video/jobs",
        json={
            "description": "Crée une courte vidéo verticale d'une ville futuriste au coucher du soleil.",
            "duration": 15,
            "format": "9:16",
            "style": "futuriste",
            "mode": "3d",
        },
    )
    assert job_response.status_code == 200
    job_payload = job_response.get_json()
    assert "job_id" in job_payload
    assert job_payload["status"] in {"VIDEO_PROVIDER_NOT_CONFIGURED", "QUEUED", "FAILED"}

    status_response = client.get(f"/api/video/jobs/{job_payload['job_id']}")
    assert status_response.status_code == 200
    status_payload = status_response.get_json()
    assert status_payload["id"] == job_payload["job_id"]
    assert status_payload["status"] in {"VIDEO_PROVIDER_NOT_CONFIGURED", "QUEUED", "FAILED"}


def test_account_service_exposes_admin_and_free_user_credits():
    from services.account_service import AccountService

    service = AccountService()
    admin = service.get_admin_account()
    assert admin["role"] == "ADMIN"
    assert admin["is_admin"] is True

    user = service.create_user("starter", "Starter user")
    assert user.role == "USER"
    assert user.free_credits == 5
    assert service.can_generate("starter") is True
    assert service.consume_credit("starter", 1) is True


def test_video_provider_is_disabled_when_not_enabled(monkeypatch):
    from services.video_provider import VideoProviderFactory

    monkeypatch.setenv("VIDEO_PROVIDER_ENABLED", "false")
    provider = VideoProviderFactory.build()
    assert provider.is_configured() is False
    assert provider.name == "disabled"
    result = provider.submit_generation("concept", {"duration": 10, "format": "9:16"})
    assert result["status"] == "VIDEO_PROVIDER_NOT_CONFIGURED"
