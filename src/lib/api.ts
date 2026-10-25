import { supabase } from './supabase'
import type { ItineraryResponse, SavedTrip, TripRequest } from '../types'

const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? ''

export interface ApiHealth {
  status: string
  services?: {
    gemini_configured: boolean
    gemini_model: string
    supabase_configured: boolean
  }
}

class ApiRequestError extends Error {
  readonly method: string
  readonly path: string
  readonly status?: number

  constructor(
    message: string,
    method: string,
    path: string,
    status?: number,
  ) {
    super(message)
    this.name = 'ApiRequestError'
    this.method = method
    this.path = path
    this.status = status
  }
}

export const checkApiHealth = () => request<ApiHealth>('/api/health')

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = false,
): Promise<T> {
  const method = options.method ?? 'GET'
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (authenticated) {
    if (!supabase) {
      throw new ApiRequestError(
        'Supabase is not configured. Check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in the project-root .env.',
        method,
        path,
      )
    }
    const { data, error } = await supabase.auth.getSession()
    if (error) throw new ApiRequestError(`Could not read your sign-in session: ${error.message}`, method, path)
    if (!data.session) throw new ApiRequestError('Your session has expired. Sign in again.', method, path, 401)
    headers.set('Authorization', `Bearer ${data.session.access_token}`)
  }
  let response: Response
  try {
    response = await fetch(`${apiUrl}${path}`, { ...options, headers })
  } catch (reason) {
    const detail = reason instanceof Error ? reason.message : 'Network request failed.'
    throw new ApiRequestError(
      `Cannot reach ${apiUrl || 'the configured API'} (${detail}). Check that the backend is running and that the browser origin is allowed by CORS.`,
      method,
      path,
    )
  }
  const responseText = await response.text()
  let body: { detail?: unknown; message?: unknown } = {}
  if (responseText) {
    try {
      body = JSON.parse(responseText) as typeof body
    } catch {
      if (!response.ok) {
        throw new ApiRequestError(
          `The server returned a non-JSON error response: ${responseText.slice(0, 240)}`,
          method,
          path,
          response.status,
        )
      }
    }
  }
  if (!response.ok) {
    const detail = typeof body.detail === 'string'
      ? body.detail
      : typeof body.message === 'string'
        ? body.message
        : JSON.stringify(body.detail ?? body)
    throw new ApiRequestError(
      `${method} ${path} failed with HTTP ${response.status}: ${detail || response.statusText}`,
      method,
      path,
      response.status,
    )
  }
  if (!responseText) {
    throw new ApiRequestError('The API returned an empty response.', method, path, response.status)
  }
  try {
    return JSON.parse(responseText) as T
  } catch {
    throw new ApiRequestError('The API returned an invalid JSON response.', method, path, response.status)
  }
}

export const generateItinerary = (trip: TripRequest) =>
  request<ItineraryResponse>('/api/itinerary/generate', {
    method: 'POST',
    body: JSON.stringify(trip),
  })

export const saveTrip = (trip: TripRequest, itinerary: ItineraryResponse) =>
  request<{ id: string; message: string }>(
    '/api/trips/save',
    { method: 'POST', body: JSON.stringify({ trip, itinerary }) },
    true,
  )

export const listTrips = () => request<SavedTrip[]>('/api/trips', {}, true)

export const regenerateDay = (
  tripId: string,
  dayNumber: number,
  preferences: TripRequest,
) =>
  request<ItineraryResponse['itinerary'][number]>('/api/itinerary/regenerate-day', {
    method: 'POST',
    body: JSON.stringify({ trip_id: tripId, day_number: dayNumber, preferences }),
  }, true)
