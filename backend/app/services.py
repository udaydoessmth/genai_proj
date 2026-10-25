import json
import logging
from datetime import date, timedelta
from typing import Any

import httpx
from fastapi import HTTPException, status
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.config import get_settings, is_configured
from app.schemas import DayItinerary, ItineraryResponse, TripRequest

logger = logging.getLogger(__name__)


def _system_prompt() -> str:
    return (
        "You are Wayfarer, a careful travel-planning assistant. Return only a JSON "
        "object matching the supplied JSON schema. Give practical suggestions and "
        "honestly label all prices and opening-hour details as estimates; never "
        "claim live availability or verified opening hours. Group each day's "
        "activities geographically to reduce travel time, include realistic "
        "transport between distant areas, leave a sensible pace, and respect "
        "the stated dates, budget, group size, style, and interests. Include "
        "at least one meal and a mix of activities each day. Accommodation "
        "suggestions should be clearly identified as suggestions, not bookings."
    )


def _trip_prompt(trip: TripRequest, day_number: int | None = None) -> str:
    details = trip.model_dump(mode="json")
    day_instruction = (
        f"Generate only a replacement for day {day_number}; keep the same date, "
        "destination, and trip constraints."
        if day_number is not None
        else "Generate the complete trip, one itinerary entry for each calendar day."
    )
    return (
        f"Trip details: {json.dumps(details, ensure_ascii=False)}\n"
        f"{day_instruction}\n"
        "Use the schema's currency-neutral cost strings and activity categories. "
        "Do not invent exact transit timetables."
    )


async def generate_itinerary(
    trip: TripRequest, day_number: int | None = None
) -> ItineraryResponse | DayItinerary:
    settings = get_settings()
    if not is_configured(settings.gemini_api_key):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The itinerary service is not configured. Add GEMINI_API_KEY to backend\\.env.",
        )

    response_schema = DayItinerary if day_number is not None else ItineraryResponse
    try:
        async with genai.Client(api_key=settings.gemini_api_key).aio as client:
            response = await client.models.generate_content(
                model=settings.gemini_model,
                contents=_trip_prompt(trip, day_number),
                config=types.GenerateContentConfig(
                    system_instruction=_system_prompt(),
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.7,
                ),
            )
    except errors.APIError as exc:
        provider_status = getattr(exc, "code", None)
        logger.warning(
            "Gemini API request failed with HTTP %s (provider status: %s)",
            provider_status,
            getattr(exc, "status", None),
        )
        if provider_status == 429:
            detail = (
                "Gemini quota or rate limit reached. Check your Google AI Studio "
                "plan and model limits, then try again later."
            )
        elif provider_status == 400:
            detail = (
                "Gemini rejected the request (HTTP 400). Check GEMINI_MODEL is "
                "a supported model and accepts the itinerary JSON schema."
            )
        elif provider_status == 401:
            detail = "Gemini rejected the API key (HTTP 401). Replace GEMINI_API_KEY with a valid Google AI Studio key."
        elif provider_status == 403:
            detail = (
                "Gemini denied access (HTTP 403). Check the key's Google AI Studio "
                "project, API access, and regional availability."
            )
        elif provider_status == 404:
            detail = (
                "Gemini could not find the configured model (HTTP 404). "
                "Set GEMINI_MODEL to a supported model such as gemini-2.5-flash."
            )
        elif isinstance(provider_status, int) and provider_status >= 500:
            detail = "Gemini is temporarily unavailable. Try again shortly."
        else:
            detail = "The Gemini request failed. Check the backend logs for provider details."
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not connect to Gemini. Check the backend network connection.",
        ) from exc

    content = response.text
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned no itinerary text. The request may have been blocked or truncated.",
        )
    try:
        if day_number is not None:
            result = DayItinerary.model_validate_json(content)
            result.day = day_number
            result.date = trip.start_date + timedelta(days=day_number - 1)
            return result
        result = ItineraryResponse.model_validate_json(content)
        expected_days = (trip.end_date - trip.start_date).days + 1
        if len(result.itinerary) != expected_days:
            raise ValueError("The generated itinerary has an incorrect number of days.")
        for index, day in enumerate(result.itinerary):
            expected_date = trip.start_date + timedelta(days=index)
            if day.date != expected_date:
                raise ValueError("The generated itinerary dates do not match the trip.")
        return result
    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an itinerary that did not match the required schema or trip dates.",
        ) from exc


async def authenticated_user_id(access_token: str) -> str:
    settings = get_settings()
    if not is_configured(settings.supabase_url) or not is_configured(settings.supabase_anon_key):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured.",
        )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_anon_key,
                    "Authorization": f"Bearer {access_token}",
                },
            )
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session is invalid or has expired.",
            )
        response.raise_for_status()
        user_id = response.json().get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase did not return a valid user.",
            )
        return str(user_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase authentication could not be verified.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase authentication is temporarily unavailable.",
        ) from exc


async def supabase_request(
    method: str,
    table: str,
    *,
    params: dict[str, str] | None = None,
    payload: dict[str, Any] | list[dict[str, Any]] | None = None,
    prefer: str | None = None,
) -> Any:
    settings = get_settings()
    if not is_configured(settings.supabase_url) or not is_configured(settings.supabase_service_role_key):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase data storage is not configured.",
        )

    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(
                method,
                f"{settings.supabase_url.rstrip('/')}/rest/v1/{table}",
                params=params,
                json=payload,
                headers=headers,
            )
        response.raise_for_status()
        return response.json() if response.content else None
    except httpx.HTTPStatusError as exc:
        response_detail = exc.response.text[:400].strip()
        detail = f"Supabase returned HTTP {exc.response.status_code}."
        if response_detail:
            detail = f"{detail} {response_detail}"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase could not complete the data operation. {detail}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase data storage is temporarily unavailable.",
        ) from exc
