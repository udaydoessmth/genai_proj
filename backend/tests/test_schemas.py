from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import DayItinerary, ItineraryResponse, TripRequest


def valid_trip(**overrides: object) -> TripRequest:
    values: dict[str, object] = {
        "destination": "Kyoto",
        "budget": "Moderate",
        "start_date": "2026-11-01",
        "end_date": "2026-11-03",
        "travel_style": "Couple",
        "group_size": 2,
        "interests": ["Food", "Culture"],
    }
    values.update(overrides)
    return TripRequest.model_validate(values)


def test_trip_accepts_valid_request() -> None:
    trip = valid_trip()
    assert trip.destination == "Kyoto"
    assert trip.end_date == date(2026, 11, 3)


@pytest.mark.parametrize(
    "overrides",
    [
        {"end_date": "2026-10-31"},
        {"end_date": "2027-01-01"},
        {"group_size": 0},
        {"interests": []},
    ],
)
def test_trip_rejects_invalid_constraints(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        valid_trip(**overrides)


def test_itinerary_requires_sequential_days() -> None:
    day = {
        "day": 2,
        "date": "2026-11-01",
        "activities": [
            {
                "time_slot": "Morning",
                "title": "Visit a temple",
                "description": "Explore the grounds.",
                "location": "Kyoto",
                "estimated_cost": "$10",
                "category": "Sightseeing",
            }
        ],
    }
    with pytest.raises(ValidationError):
        ItineraryResponse.model_validate(
            {
                "trip_summary": "A Kyoto visit.",
                "total_estimated_cost": "$100",
                "itinerary": [day],
            }
        )
    assert DayItinerary.model_validate(day).day == 2
