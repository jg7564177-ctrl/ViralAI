from services.agnes_chat import AgnesChatClient
from services.ai_service import AIChatService


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def post(self, endpoint, **kwargs):
        self.calls.append((endpoint, kwargs))
        return next(self.responses)


def test_agnes_client_retries_unknown_model_without_exposing_key(monkeypatch):
    monkeypatch.setenv("AGNES_API_KEY", "test-secret")
    monkeypatch.setenv("AGNES_CHAT_MODEL", "agnes-chat")
    monkeypatch.setenv("AGNES_CHAT_FALLBACK_MODELS", "gpt-4o-mini,claude-3-haiku")
    session = FakeSession([
        FakeResponse(404, {"error": "model not found"}),
        FakeResponse(200, {"choices": [{"message": {"content": "Réponse Agnes réelle"}}]}),
    ])

    result = AgnesChatClient(session=session).complete(
        "Donne-moi un hook",
        context=[{"role": "user", "content": "Je crée un Short"}],
    )

    assert result.content == "Réponse Agnes réelle"
    assert result.model == "gpt-4o-mini"
    assert len(session.calls) == 2
    assert session.calls[0][0] == "https://apihub.agnes-ai.com/v1/chat/completions"
    assert session.calls[0][1]["headers"]["Authorization"] == "Bearer test-secret"
    assert "test-secret" not in str(session.calls[0][1]["json"])


def test_chat_service_marks_local_fallback_when_agnes_fails(monkeypatch):
    monkeypatch.setenv("AGNES_API_KEY", "test-secret")
    session = FakeSession([
        FakeResponse(500, {"error": "temporarily unavailable"}),
        FakeResponse(503, {"error": "temporarily unavailable"}),
        FakeResponse(503, {"error": "temporarily unavailable"}),
    ])
    service = AIChatService(AgnesChatClient(session=session))

    result = service.reply_with_metadata("Crée une vidéo de danse de 20 secondes")

    assert result["provider"] == "local_fallback"
    assert result["degraded"] is True
    assert result["response"]