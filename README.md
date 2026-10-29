# Wayfarer
https://genaiproj-darrb8nlwl7ukx7zq8klom.streamlit.app/

Wayfarer is a personalized travel-planning starter app: a React/Vite dashboard talks to a FastAPI service, which generates structured itineraries with Google Gemini and optionally stores them in Supabase.

## Architecture

```text
React + Vite + Tailwind CSS + Supabase Auth
                    │ Bearer access token / JSON
                    ▼
FastAPI ───── Gemini structured itinerary generation
   │
   └── Supabase Auth verification + PostgREST (service role, server only)
                    │
                    ▼
          PostgreSQL trips + itineraries
```

The browser uses only the Supabase anon key. The backend verifies Supabase access tokens, obtains the user ID from Supabase Auth, and scopes trip queries to that ID. The service-role key and Gemini API key are backend-only secrets. Row-level security is enabled for both database tables.

## Requirements

- Node.js 18 or newer (the current Vite release may require a newer compatible Node release; Node 20.19+ or 22.12+ is recommended).
- Python 3.10 or newer.
- A Supabase project for sign-in and saved-trip persistence.
- A Google Gemini API key for itinerary generation.

## Local setup (PowerShell)

From the project root:

```powershell
npm install
Copy-Item .env.example .env
```

Fill in `.env`. `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are browser-visible project settings; never put the service-role key in a `VITE_` variable. The root `.env` is ignored by Git.

Set up the backend virtual environment:

```powershell
py -3 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Put the backend-only settings in `backend\.env` (Gemini API key, Supabase URL, anon key, and service-role key). `backend\.env` is ignored by Git. The backend reads this file regardless of its launch directory.

Start the API from the repository root:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend
```

Alternatively, activate the virtual environment, change into `backend`, and start the API:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In another terminal, from the repository root:

```powershell
npm run dev
```

Open the Vite URL shown in the terminal. The API health check is `http://localhost:8000/api/health`; interactive API docs are at `http://localhost:8000/docs`.

## Supabase setup

1. Create a Supabase project at [supabase.com](https://supabase.com/) and wait for its database to finish provisioning.
2. In the project dashboard, open **SQL Editor**, create a query, paste the contents of [`supabase/schema.sql`](./supabase/schema.sql), and run it. This creates the trip tables, indexes, and row-level security policies.
3. Open **Project Settings → API** (or **Project Settings → API Keys**) and copy the **Project URL**, the public **anon** or **publishable** key, and the **service_role** or **secret** key. The service-role/secret key bypasses row-level security: use it only in the backend environment, never in frontend code, a `VITE_` variable, source control, or a message.
4. In **Authentication → Providers**, enable email/password sign-in. In **Authentication → URL Configuration**, set the local Site URL to `http://localhost:5173` and allow both `http://localhost:5173/**` and `http://127.0.0.1:5173/**` as redirect URLs. Add the production frontend URL when deploying.
5. Add the Project URL and public key to the frontend `.env`, and the Project URL, public key, and service-role/secret key to `backend\.env` as shown below.

Supabase creates and manages its own `auth.users` table; do not create a separate users table for this app.

## Gemini setup

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey). Add it only to `backend\.env` as `GEMINI_API_KEY`; never put it in the frontend `.env`, a `VITE_` variable, source code, or Git. The default model is `gemini-2.5-flash`, a stable model listed in Google's Gemini API model docs. Free-tier model availability and request limits depend on Google's current project and region limits; check [Gemini API pricing and free-tier details](https://ai.google.dev/gemini-api/docs/pricing) and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) for your account. Set `GEMINI_MODEL` to another supported model if needed.

## Configure and run locally

The example files are templates, not working credentials. After copying them, replace every placeholder with values from your own accounts:

**Project-root `.env`** (Vite/browser settings only):

```dotenv
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLIC_ANON_OR_PUBLISHABLE_KEY
VITE_API_URL=http://localhost:8000
```

**`backend\.env`** (server-side secrets/settings):

```dotenv
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=YOUR_PUBLIC_ANON_OR_PUBLISHABLE_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_OR_SECRET_KEY
FRONTEND_ORIGIN=http://localhost:5173
```

Use two PowerShell terminals from the project root. In the first, start the backend:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend
```

In the second, start the frontend:

```powershell
npm run dev
```

Open `http://localhost:5173`. If you do not have an active Supabase session, the app first shows the dedicated sign-in/create-account page; after successful sign-in it opens the trip dashboard. To generate itineraries, enter a destination and preferences and select **Create my itinerary**. To verify saved trips end-to-end, save a generated trip. The API health check is `http://localhost:8000/api/health`; interactive API docs are at `http://localhost:8000/docs`.

The sign-in page's **Connection diagnostics** panel shows whether Supabase frontend settings are present, whether the backend is reachable, and whether its Gemini and Supabase settings are configured. API failures also show the request method, path, HTTP status, and server error detail; no secret values are returned by the health endpoint.

For local development, open either `http://localhost:5173` or `http://127.0.0.1:5173`; both are allowed by the default local backend CORS configuration. If you set a different `FRONTEND_ORIGIN`, restart the backend after changing it. For production, set `FRONTEND_ORIGIN` to the exact deployed frontend origin.

If you only want to try itinerary generation first, you need the Gemini key and the backend `.env`; Supabase is required for sign-in, saving trips, and regenerating a saved trip's day. Without credentials, those integrations cannot work, and the app reports a configuration error instead of pretending a trip was saved or generated.

## API

- `POST /api/itinerary/generate` — generate a complete, schema-validated itinerary. Does not require sign-in.
- `POST /api/trips/save` — save trip details and day itineraries. Requires a Supabase bearer access token.
- `GET /api/trips` — list the signed-in user's saved trips.
- `POST /api/itinerary/regenerate-day` — regenerate and persist one day of a saved trip.
- `GET /api/health` — service health.

Itinerary costs are estimates, not booking quotes. AI-generated locations, prices, opening hours, and transit suggestions should be verified before travel. The prompt favors nearby activities but is not a live routing or mapping service.

## Validation

```powershell
npm run build
backend\.venv\Scripts\python.exe -m pytest
```

## Deployment

Deployment is not automatic: you need accounts with your chosen frontend and backend hosting providers. Deploy the frontend as a static Vite site and the backend as an ASGI service (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Set `VITE_API_URL` to the deployed backend URL at frontend build time. Configure `GEMINI_API_KEY`, `GEMINI_MODEL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `FRONTEND_ORIGIN` as backend environment variables/secrets. Configure `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` as frontend build variables. Apply the SQL schema and add the production frontend URL to Supabase Auth's Site URL/redirect allow list. Use HTTPS, restrict CORS to the real frontend origin, and keep server secrets in the hosting provider's secret manager.
