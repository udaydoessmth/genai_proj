export type Budget = 'Budget' | 'Moderate' | 'Luxury'
export type TravelStyle = 'Solo' | 'Couple' | 'Family' | 'Friends'
export type Category =
  | 'Dining'
  | 'Sightseeing'
  | 'Transport'
  | 'Accommodation'
  | 'Experience'

export interface TripRequest {
  destination: string
  budget: Budget
  start_date: string
  end_date: string
  travel_style: TravelStyle
  group_size: number
  interests: string[]
}

export interface Activity {
  time_slot: string
  title: string
  description: string
  location: string
  estimated_cost: string
  category: Category
}

export interface DayItinerary {
  day: number
  date: string
  activities: Activity[]
}

export interface ItineraryResponse {
  trip_summary: string
  total_estimated_cost: string
  itinerary: DayItinerary[]
}

export interface SavedTrip {
  id: string
  destination: string
  budget_tier: Budget
  start_date: string
  end_date: string
  travel_style: TravelStyle
  group_size: number
  interests: string[]
  trip_summary: string
  total_estimated_cost: string
  itineraries: { day_number: number; activities: DayItinerary }[]
}
