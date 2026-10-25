from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_cors_allows_local_vite_origins() -> None:
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = client.options(
            "/api/itinerary/generate",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_unconfigured_origin() -> None:
    response = client.options(
        "/api/itinerary/generate",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400


def test_health_reports_service_configuration_without_credentials() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body["services"]) == {
        "gemini_configured",
        "gemini_model",
        "supabase_configured",
    }
    assert isinstance(body["services"]["gemini_configured"], bool)
    assert isinstance(body["services"]["supabase_configured"], bool)
    assert isinstance(body["services"]["gemini_model"], str)
