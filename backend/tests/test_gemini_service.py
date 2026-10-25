import asyncio
import json
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from google.genai import errors

from app import services
from app.schemas import DayItinerary, ItineraryResponse, TripRequest


def valid_trip() -> TripRequest:
    return TripRequest.model_validate(
        {
            "destination": "Kyoto",
            "budget": "Moderate",
            "start_date": "2026-11-01",
            "end_date": "2026-11-01",
            "travel_style": "Couple",
            "group_size": 2,
            "interests": ["Food", "Culture"],
        }
    )


def valid_response() -> ItineraryResponse:
    return ItineraryResponse.model_validate(
        {
            "trip_summary": "A relaxed day exploring Kyoto.",
            "total_estimated_cost": "$100",
            "itinerary": [
                {
                    "day": 1,
                    "date": "2026-11-01",
                    "activities": [
                        {
                            "time_slot": "Morning",
                            "title": "Visit a temple",
                            "description": "Explore the temple grounds.",
                            "location": "Higashiyama, Kyoto",
                            "estimated_cost": "$10",
                            "category": "Sightseeing",
                        }
                    ],
                }
            ],
        }
    )


class FakeModels:
    def __init__(self, response: object) -> None:
        self.response = response
        self.request: dict[str, object] = {}

    async def generate_content(self, **kwargs: object) -> object:
        self.request = kwargs
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeAsyncClient:
    def __init__(self, response: object) -> None:
        self.models = FakeModels(response)

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def configured_settings() -> SimpleNamespace:
    return SimpleNamespace(
        gemini_api_key="test-key",
        gemini_model="gemini-test-model",
    )


def test_generate_itinerary_uses_gemini_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = valid_response()
    fake_client = FakeAsyncClient(SimpleNamespace(text=expected.model_dump_json()))
    monkeypatch.setattr(services, "get_settings", configured_settings)
    monkeypatch.setattr(
        services.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(aio=fake_client),
    )

    result = asyncio.run(services.generate_itinerary(valid_trip()))

    assert result == expected
    assert fake_client.models.request["model"] == "gemini-test-model"
    config = fake_client.models.request["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is ItineraryResponse


def test_generate_itinerary_rejects_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(services, "get_settings", configured_settings)
    monkeypatch.setattr(
        services.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(aio=FakeAsyncClient(SimpleNamespace(text="{bad"))),
    )

    with pytest.raises(HTTPException) as raised:
        asyncio.run(services.generate_itinerary(valid_trip()))
    assert raised.value.status_code == 502
    assert "required schema" in raised.value.detail


def test_generate_itinerary_reports_quota_errors_without_provider_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "get_settings", configured_settings)
    quota_error = errors.APIError(
        code=429,
        response_json={"error": {"message": "quota exhausted"}},
    )
    monkeypatch.setattr(
        services.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(aio=FakeAsyncClient(quota_error)),
    )

    with pytest.raises(HTTPException) as raised:
        asyncio.run(services.generate_itinerary(valid_trip()))
    assert raised.value.status_code == 502
    assert "quota or rate limit" in raised.value.detail
    assert "quota exhausted" not in raised.value.detail


@pytest.mark.parametrize(
    ("provider_code", "expected_detail"),
    [
        (400, "supported model"),
        (401, "API key"),
        (403, "denied access"),
        (404, "could not find the configured model"),
    ],
)
def test_generate_itinerary_classifies_gemini_client_errors(
    monkeypatch: pytest.MonkeyPatch,
    provider_code: int,
    expected_detail: str,
) -> None:
    monkeypatch.setattr(services, "get_settings", configured_settings)
    provider_error = errors.APIError(
        code=provider_code,
        response_json={"error": {"message": "private provider response"}},
    )
    monkeypatch.setattr(
        services.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(aio=FakeAsyncClient(provider_error)),
    )

    with pytest.raises(HTTPException) as raised:
        asyncio.run(services.generate_itinerary(valid_trip()))
    assert raised.value.status_code == 502
    assert expected_detail.lower() in raised.value.detail.lower()
    assert "private provider response" not in raised.value.detail


def test_generated_day_is_fixed_to_requested_trip_date(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = valid_response().itinerary[0].model_dump(mode="json")
    payload["day"] = 27
    payload["date"] = "2020-01-01"
    response = DayItinerary.model_validate(payload)
    fake_client = FakeAsyncClient(SimpleNamespace(text=json.dumps(response.model_dump(mode="json"))))
    monkeypatch.setattr(services, "get_settings", configured_settings)
    monkeypatch.setattr(
        services.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(aio=fake_client),
    )

    result = asyncio.run(services.generate_itinerary(valid_trip(), day_number=1))

    assert result.day == 1
    assert result.date == date(2026, 11, 1)
