from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, is_configured
from app.schemas import (
    DayItinerary,
    ItineraryResponse,
    RegenerateDayRequest,
    SaveTripRequest,
    TripRequest,
)
from app.services import authenticated_user_id, generate_itinerary, supabase_request

app = FastAPI(title="Wayfarer Travel Planner API", version="1.0.0")
settings = get_settings()
allowed_origins = [settings.frontend_origin]
if settings.frontend_origin == "http://localhost:5173":
    allowed_origins.append("http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


async def current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to manage saved trips.",
        )
    return await authenticated_user_id(authorization.removeprefix("Bearer ").strip())


@app.get("/api/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "services": {
            "gemini_configured": is_configured(settings.gemini_api_key),
            "gemini_model": settings.gemini_model,
            "supabase_configured": bool(
                is_configured(settings.supabase_url)
                and is_configured(settings.supabase_anon_key)
                and is_configured(settings.supabase_service_role_key)
            ),
        },
    }


@app.post("/api/itinerary/generate", response_model=ItineraryResponse)
async def create_itinerary(trip: TripRequest) -> ItineraryResponse:
    result = await generate_itinerary(trip)
    if not isinstance(result, ItineraryResponse):
        raise HTTPException(status_code=502, detail="Could not create the requested itinerary.")
    return result


@app.post("/api/trips/save", status_code=status.HTTP_201_CREATED)
async def save_trip(
    body: SaveTripRequest,
    user_id: str = Depends(current_user),
) -> dict[str, str]:
    trip_payload = body.trip.model_dump(mode="json")
    trip_rows = await supabase_request(
        "POST",
        "trips",
        payload={
            "user_id": user_id,
            "destination": trip_payload["destination"],
            "budget_tier": trip_payload["budget"],
            "start_date": trip_payload["start_date"],
            "end_date": trip_payload["end_date"],
            "travel_style": trip_payload["travel_style"],
            "group_size": trip_payload["group_size"],
            "interests": trip_payload["interests"],
        },
        prefer="return=representation",
    )
    if not isinstance(trip_rows, list) or not trip_rows:
        raise HTTPException(status_code=502, detail="Supabase did not return the saved trip.")
    trip_id = trip_rows[0]["id"]
    try:
        await supabase_request(
            "POST",
            "itineraries",
            payload=[
                {
                    "trip_id": trip_id,
                    "day_number": day.day,
                    "activities": day.model_dump(mode="json"),
                }
                for day in body.itinerary.itinerary
            ],
            prefer="return=minimal",
        )
    except HTTPException:
        await supabase_request("DELETE", "trips", params={"id": f"eq.{trip_id}"})
        raise
    await supabase_request(
        "PATCH",
        "trips",
        params={"id": f"eq.{trip_id}"},
        payload={
            "trip_summary": body.itinerary.trip_summary,
            "total_estimated_cost": body.itinerary.total_estimated_cost,
        },
        prefer="return=minimal",
    )
    return {"id": str(trip_id), "message": "Trip saved."}


@app.get("/api/trips")
async def list_trips(user_id: str = Depends(current_user)) -> list[dict]:
    return await supabase_request(
        "GET",
        "trips",
        params={
            "select": "id,destination,budget_tier,start_date,end_date,travel_style,group_size,interests,trip_summary,total_estimated_cost,created_at,itineraries(day_number,activities)",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
        },
    )


@app.post("/api/itinerary/regenerate-day", response_model=DayItinerary)
async def regenerate_day(
    body: RegenerateDayRequest,
    user_id: str = Depends(current_user),
) -> DayItinerary:
    trip_rows = await supabase_request(
        "GET",
        "trips",
        params={"select": "id,user_id,start_date,end_date", "id": f"eq.{body.trip_id}"},
    )
    if not trip_rows or trip_rows[0].get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Saved trip not found.")
    trip_start = date.fromisoformat(trip_rows[0]["start_date"])
    trip_end = date.fromisoformat(trip_rows[0]["end_date"])
    if body.day_number > (trip_end - trip_start).days + 1:
        raise HTTPException(status_code=422, detail="Day number is outside this trip.")
    if body.preferences.start_date != trip_start or body.preferences.end_date != trip_end:
        raise HTTPException(status_code=422, detail="Trip dates cannot change during day regeneration.")

    day = await generate_itinerary(body.preferences, body.day_number)
    if not isinstance(day, DayItinerary):
        raise HTTPException(status_code=502, detail="Could not regenerate this itinerary day.")
    await supabase_request(
        "PATCH",
        "itineraries",
        params={
            "trip_id": f"eq.{body.trip_id}",
            "day_number": f"eq.{body.day_number}",
        },
        payload={"activities": day.model_dump(mode="json")},
        prefer="return=minimal",
    )
    return day
