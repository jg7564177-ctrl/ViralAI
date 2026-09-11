from services.account_service import AccountService


def test_user_creation_and_initial_free_credits():
    service = AccountService()
    user = service.create_user("alice", "Alice")

    assert user.user_id == "alice"
    assert user.role == "USER"
    assert user.free_credits == 5
    assert service.get_balance("alice") == 5


def test_admin_gets_free_access_without_credit_loss():
    service = AccountService()
    admin = service.get_admin_account()

    assert admin["role"] == "ADMIN"
    assert admin["is_admin"] is True
    assert service.is_admin("admin") is True

    assert service.consume_credit_for_generation("admin", 1) is True
    assert service.get_balance("admin") == 0


def test_user_credit_consumption_and_failure_refund():
    service = AccountService()
    service.create_user("bob", "Bob")

    assert service.consume_credit_for_generation("bob", 1) is True
    assert service.get_balance("bob") == 4

    service.refund_credit_after_failure("bob", 1)
    assert service.get_balance("bob") == 5


def test_user_cannot_consume_more_than_available():
    service = AccountService()
    service.create_user("charlie", "Charlie")

    assert service.consume_credit_for_generation("charlie", 10) is False
    assert service.get_balance("charlie") == 5


def test_admin_permission_check():
    service = AccountService()
    assert service.require_admin("admin") is True
    service.create_user("guest", "Guest")
    assert service.require_admin("guest") is False


def test_user_cannot_access_admin_panel_logic():
    service = AccountService()
    service.create_user("dave", "Dave")
    assert service.require_admin("dave") is False
    assert service.admin_summary()["users"]


def test_user_does_not_see_any_admin_interface():
    from app import app

    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True).lower()
    assert "admin" not in html
    assert "panneau admin" not in html


def test_user_cannot_access_admin_routes_or_admin_data():
    from app import app

    client = app.test_client()

    denied_summary = client.get("/api/admin/summary", headers={"X-User-Id": "guest"})
    assert denied_summary.status_code == 403
    assert denied_summary.get_json()["error"] == "Access denied."

    denied_admin_account = client.get("/api/accounts/admin", headers={"X-User-Id": "guest"})
    assert denied_admin_account.status_code == 403

    denied_credit_update = client.post(
        "/api/admin/accounts/guest/credits",
        headers={"X-User-Id": "guest"},
        json={"amount": 99},
    )
    assert denied_credit_update.status_code == 403

    denied_role_update = client.post(
        "/api/admin/accounts/guest/role",
        headers={"X-User-Id": "guest"},
        json={"role": "ADMIN"},
    )
    assert denied_role_update.status_code == 403


def test_admin_can_access_secret_admin_functions():
    from app import app

    client = app.test_client()
    response = client.get("/api/admin/summary", headers={"X-User-Id": "admin"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["users"]
    assert any(user["user_id"] == "admin" for user in payload["users"])

    credit_response = client.post(
        "/api/admin/accounts/demo/credits",
        headers={"X-User-Id": "admin"},
        json={"amount": 10, "reason": "manual_test"},
    )
    assert credit_response.status_code == 200
    assert credit_response.get_json()["balance"] >= 10


def test_user_no_sensitive_admin_data_reaches_frontend():
    from app import app

    client = app.test_client()
    response = client.get("/api/settings")
    assert response.status_code == 200
    payload = response.get_data(as_text=True).lower()
    assert "admin" not in payload

    user_response = client.get("/api/accounts", headers={"X-User-Id": "demo"})
    assert user_response.status_code == 200
    user_payload = user_response.get_json()
    assert user_payload.get("accounts") or user_payload.get("account")
    assert "admin" not in str(user_payload).lower()


def test_project_creation_and_self_retrieval():
    from app import app

    client = app.test_client()
    response = client.post(
        "/api/projects",
        headers={"X-User-Id": "demo"},
        json={
            "name": "Projet test",
            "prompt": "Un personnage futuriste marche dans une ville cyberpunk.",
            "format": "9:16",
            "duration": 15,
            "style": "cyberpunk",
            "storyboard": [{"scene": 1, "description": "intro", "duration": 5, "camera_motion": "tracking"}],
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["project"]["name"] == "Projet test"
    assert payload["project"]["user_id"] == "demo"

    list_response = client.get("/api/projects", headers={"X-User-Id": "demo"})
    assert list_response.status_code == 200
    list_payload = list_response.get_json()
    assert any(project["name"] == "Projet test" for project in list_payload["projects"])


def test_user_cannot_access_other_users_project():
    from app import app

    client = app.test_client()
    created = client.post(
        "/api/projects",
        headers={"X-User-Id": "demo"},
        json={"name": "Projet secret", "prompt": "Secret prompt", "format": "16:9", "duration": 10},
    )
    project_id = created.get_json()["project"]["id"]

    response = client.get(f"/api/projects/{project_id}", headers={"X-User-Id": "guest"})
    assert response.status_code == 403


def test_project_generation_is_disabled_and_consumes_no_credit():
    from app import app
    from services.account_service import AccountService

    client = app.test_client()
    account_service = AccountService()
    account_service.create_user("project-user", "Project user")
    created = client.post(
        "/api/projects",
        headers={"X-User-Id": "project-user"},
        json={"name": "Disable generation", "prompt": "test prompt", "format": "9:16", "duration": 10},
    )
    project_id = created.get_json()["project"]["id"]

    before = account_service.get_balance("project-user")
    response = client.post(f"/api/projects/{project_id}/generate", headers={"X-User-Id": "project-user"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "VIDEO_GENERATION_DISABLED"
    assert account_service.get_balance("project-user") == before


def test_project_route_requires_authenticated_user():
    from app import app

    client = app.test_client()
    response = client.get("/api/projects")
    assert response.status_code == 403


def test_project_parameters_and_storyboard_are_saved():
    from app import app

    client = app.test_client()
    response = client.post(
        "/api/projects",
        headers={"X-User-Id": "demo"},
        json={
            "name": "Storyboard test",
            "prompt": "Futuristic skyline.",
            "format": "1:1",
            "duration": 30,
            "style": "cinematic",
            "quality": "Ultra",
            "storyboard": [
                {"scene": 1, "description": "intro", "duration": 8, "camera_motion": "slow push", "transition": "fade"},
                {"scene": 2, "description": "main action", "duration": 12, "camera_motion": "tracking", "transition": "cut"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    project = payload["project"]
    assert project["parameters"]["format"] == "1:1"
    assert project["parameters"]["quality"] == "Ultra"
    assert len(project["storyboard"]) == 2
    assert project["storyboard"][0]["scene"] == 1


def test_creative_assistant_transforms_idea_into_video_structure():
    from app import app

    client = app.test_client()
    response = client.post(
        "/api/creative/transform",
        json={"idea": "Un joueur gagne une partie de Free Fire", "platform": "TikTok"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] in {"ready", "AI_UNAVAILABLE"}
    if payload["status"] == "ready":
        assert payload["title"]
        assert payload["hook"]
        assert payload["video_prompt"]
        assert payload["storyboard"]
        assert payload["platform_options"]["TikTok"]["title"]


def test_creative_storyboard_and_project_update_are_saved():
    from app import app

    client = app.test_client()
    created = client.post(
        "/api/projects",
        headers={"X-User-Id": "demo"},
        json={
            "name": "Projet IA",
            "prompt": "Un joueur gagne une partie de Free Fire.",
            "format": "9:16",
            "duration": 15,
            "style": "gaming",
        },
    )
    project_id = created.get_json()["project"]["id"]

    story_response = client.post(
        f"/api/projects/{project_id}/ai",
        headers={"X-User-Id": "demo"},
        json={
            "original_idea": "Un joueur gagne une partie de Free Fire.",
            "storyboard": [{"scene": 1, "description": "hook", "duration": 4, "camera": "close-up"}],
            "prompt": "Prompt final optimisé pour la génération future.",
            "ai_analysis": {"hook": 88, "originality": 90},
        },
    )
    assert story_response.status_code == 200
    project_response = client.get(f"/api/projects/{project_id}", headers={"X-User-Id": "demo"})
    assert project_response.status_code == 200
    project_data = project_response.get_json()["project"]
    assert project_data["storyboard"]
    assert project_data["prompt"]


def test_ai_unavailable_message_is_safe_and_no_secret_is_exposed():
    import os
    from app import app

    previous_provider = os.environ.get("AI_PROVIDER")
    previous_key = os.environ.get("AI_API_KEY")
    os.environ.pop("AI_PROVIDER", None)
    os.environ.pop("AI_API_KEY", None)

    try:
        response = app.test_client().post(
            "/api/creative/transform",
            json={"idea": "Un joueur gagne une partie de Free Fire"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "AI_UNAVAILABLE"
        assert "configurez le fournisseur ia" in payload["message"].lower()
        assert "sk-" not in str(payload).lower()
    finally:
        if previous_provider is not None:
            os.environ["AI_PROVIDER"] = previous_provider
        if previous_key is not None:
            os.environ["AI_API_KEY"] = previous_key
