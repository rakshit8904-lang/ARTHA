"""Tests for the first, deliberately read-only assistant integration."""


def test_assistant_page_requires_login(client):
    response = client.get("/assistant")
    assert response.status_code in (302, 401)


def test_assistant_api_requires_login(client):
    response = client.post("/api/v1/assistant/chat", json={
        "provider": "openai", "messages": [{"role": "user", "content": "What is an RD?"}]
    })
    assert response.status_code in (302, 401)


def test_assistant_reports_missing_provider_configuration(alice, app):
    app.config["OPENAI_API_KEY"] = ""
    response = alice.post("/assistant/chat", {
        "provider": "openai", "messages": [{"role": "user", "content": "What is an RD?"}]
    })
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "ai_provider_unavailable"


def test_assistant_rejects_invalid_provider(alice):
    response = alice.post("/assistant/chat", {
        "provider": "unknown", "messages": [{"role": "user", "content": "Hello"}]
    })
    assert response.status_code == 400


def test_assistant_rejects_non_user_final_message(alice):
    response = alice.post("/assistant/chat", {
        "provider": "openai", "messages": [{"role": "assistant", "content": "Hello"}]
    })
    assert response.status_code == 400
