from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


BudgetTier = Literal["Budget", "Moderate", "Luxury"]
TravelStyle = Literal["Solo", "Couple", "Family", "Friends"]
ActivityCategory = Literal[
    "Dining", "Sightseeing", "Transport", "Accommodation", "Experience"
]


class TripRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    destination: str = Field(min_length=2, max_length=120)
    budget: BudgetTier
    start_date: date
    end_date: date
    travel_style: TravelStyle
    group_size: int = Field(ge=1, le=20)
    interests: list[str] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_dates(self) -> "TripRequest":
        if self.end_date < self.start_date:
            raise ValueError("End date must be on or after start date.")
        if (self.end_date - self.start_date).days > 30:
            raise ValueError("Trips can be at most 31 calendar days long.")
        if any(not interest.strip() or len(interest) > 40 for interest in self.interests):
            raise ValueError("Each interest must contain 1 to 40 characters.")
        return self


class Activity(BaseModel):
    time_slot: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1200)
    location: str = Field(min_length=1, max_length=240)
    estimated_cost: str = Field(min_length=1, max_length=100)
    category: ActivityCategory


class DayItinerary(BaseModel):
    day: int = Field(ge=1, le=31)
    date: date
    activities: list[Activity] = Field(min_length=1, max_length=12)


class ItineraryResponse(BaseModel):
    trip_summary: str = Field(min_length=1, max_length=2000)
    total_estimated_cost: str = Field(min_length=1, max_length=160)
    itinerary: list[DayItinerary] = Field(min_length=1, max_length=31)

    @model_validator(mode="after")
    def validate_day_sequence(self) -> "ItineraryResponse":
        days = [entry.day for entry in self.itinerary]
        if days != list(range(1, len(days) + 1)):
            raise ValueError("Itinerary days must be sequential and start at 1.")
        return self


class SaveTripRequest(BaseModel):
    trip: TripRequest
    itinerary: ItineraryResponse


class RegenerateDayRequest(BaseModel):
    trip_id: str = Field(min_length=1, max_length=100)
    day_number: int = Field(ge=1, le=31)
    preferences: TripRequest
