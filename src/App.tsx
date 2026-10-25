import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRight,
  Bookmark,
  CalendarDays,
  Check,
  Compass,
  Eye,
  EyeOff,
  Heart,
  LogIn,
  LogOut,
  MapPin,
  Menu,
  Plus,
  RefreshCw,
  Sparkles,
  Users,
  Wallet,
  X,
} from 'lucide-react'
import type { FormEvent } from 'react'
import { checkApiHealth, generateItinerary, listTrips, regenerateDay, saveTrip } from './lib/api'
import type { ApiHealth } from './lib/api'
import { supabase, supabaseConfigured } from './lib/supabase'
import type { Session } from '@supabase/supabase-js'
import type {
  Activity,
  Budget,
  Category,
  DayItinerary,
  ItineraryResponse,
  SavedTrip,
  TravelStyle,
  TripRequest,
} from './types'

const interestOptions = ['Food & drink', 'Culture', 'Nature', 'Architecture', 'Adventure', 'Shopping']
const categoryClass: Record<Category, string> = {
  Dining: 'dining',
  Sightseeing: 'sightseeing',
  Transport: 'transport',
  Accommodation: 'stay',
  Experience: 'experience',
}

const today = new Date()
const inTwoWeeks = new Date(today)
inTwoWeeks.setDate(today.getDate() + 7)
const dateInput = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`

function App() {
  const [view, setView] = useState<'create' | 'saved'>('create')
  const [trip, setTrip] = useState<TripRequest>({
    destination: '',
    budget: 'Moderate',
    start_date: dateInput(today),
    end_date: dateInput(inTwoWeeks),
    travel_style: 'Couple',
    group_size: 2,
    interests: ['Food & drink', 'Culture'],
  })
  const [itinerary, setItinerary] = useState<ItineraryResponse | null>(null)
  const [activeTripId, setActiveTripId] = useState<string | null>(null)
  const [savedTrips, setSavedTrips] = useState<SavedTrip[]>([])
  const [selectedDay, setSelectedDay] = useState(1)
  const [busy, setBusy] = useState(false)
  const [saving, setSaving] = useState(false)
  const [loadingTrips, setLoadingTrips] = useState(false)
  const [error, setError] = useState('')
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [authBusy, setAuthBusy] = useState(false)
  const [session, setSession] = useState<Session | null>(null)
  const [sessionChecked, setSessionChecked] = useState(false)
  const [sessionError, setSessionError] = useState('')
  const [authNotice, setAuthNotice] = useState('')
  const [apiHealth, setApiHealth] = useState<Awaited<ReturnType<typeof checkApiHealth>> | null>(null)
  const [apiHealthError, setApiHealthError] = useState('')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const userEmail = session?.user.email ?? null

  useEffect(() => {
    if (!supabase) {
      setSessionChecked(true)
      return
    }
    let mounted = true
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      if (mounted) {
        setSession(session)
        setSessionChecked(true)
        setSessionError('')
      }
    })
    void supabase.auth.getSession()
      .then(({ data: sessionData, error: sessionLoadError }) => {
        if (!mounted) return
        if (sessionLoadError) throw sessionLoadError
        setSession(sessionData.session)
        setSessionError('')
      })
      .catch((reason: unknown) => {
        if (mounted) setSessionError(messageOf(reason))
      })
      .finally(() => {
        if (mounted) setSessionChecked(true)
      })
    return () => {
      mounted = false
      data.subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    let mounted = true
    void checkApiHealth()
      .then((health) => {
        if (mounted) {
          setApiHealth(health)
          setApiHealthError('')
        }
      })
      .catch((reason: unknown) => {
        if (mounted) setApiHealthError(messageOf(reason))
      })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (!userEmail) {
      setSavedTrips([])
      return
    }
    setLoadingTrips(true)
    void listTrips()
      .then(setSavedTrips)
      .catch((reason: unknown) => setError(messageOf(reason)))
      .finally(() => setLoadingTrips(false))
  }, [userEmail])

  const currentDay = itinerary?.itinerary.find((day) => day.day === selectedDay)
  const dateLabel = useMemo(() => {
    if (!itinerary?.itinerary.length) return ''
    const first = new Date(`${itinerary.itinerary[0].date}T12:00:00`)
    const last = new Date(`${itinerary.itinerary.at(-1)!.date}T12:00:00`)
    const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }
    return `${first.toLocaleDateString('en-US', options)} – ${last.toLocaleDateString('en-US', { ...options, year: 'numeric' })}`
  }, [itinerary])

  function patchTrip<K extends keyof TripRequest>(key: K, value: TripRequest[K]) {
    setTrip((previous) => ({ ...previous, [key]: value }))
  }

  function toggleInterest(interest: string) {
    const selected = trip.interests.includes(interest)
    patchTrip(
      'interests',
      selected ? trip.interests.filter((item) => item !== interest) : [...trip.interests, interest],
    )
  }

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setBusy(true)
    setItinerary(null)
    setActiveTripId(null)
    setSelectedDay(1)
    try {
      setItinerary(await generateItinerary(trip))
    } catch (reason) {
      setError(messageOf(reason))
    } finally {
      setBusy(false)
    }
  }

  async function handleSave() {
    if (!itinerary) return
    setError('')
    setSaving(true)
    try {
      const result = await saveTrip(trip, itinerary)
      setActiveTripId(result.id)
      setSavedTrips(await listTrips())
    } catch (reason) {
      setError(messageOf(reason))
    } finally {
      setSaving(false)
    }
  }

  async function handleRegenerate(dayNumber: number) {
    if (!activeTripId) {
      setError('Save this trip first to refresh an individual day.')
      return
    }
    setError('')
    setBusy(true)
    try {
      const day = await regenerateDay(activeTripId, dayNumber, trip)
      setItinerary((previous) =>
        previous
          ? { ...previous, itinerary: previous.itinerary.map((item) => item.day === dayNumber ? day : item) }
          : previous,
      )
      setSavedTrips(await listTrips())
    } catch (reason) {
      setError(messageOf(reason))
    } finally {
      setBusy(false)
    }
  }

  function openSavedTrip(saved: SavedTrip) {
    const restoredTrip: TripRequest = {
      destination: saved.destination,
      budget: saved.budget_tier,
      start_date: saved.start_date,
      end_date: saved.end_date,
      travel_style: saved.travel_style,
      group_size: saved.group_size,
      interests: saved.interests,
    }
    setTrip(restoredTrip)
    const days: DayItinerary[] = saved.itineraries
      .map((entry) => entry.activities)
      .sort((a, b) => a.day - b.day)
    setItinerary({
      trip_summary: saved.trip_summary,
      total_estimated_cost: saved.total_estimated_cost,
      itinerary: days,
    })
    setActiveTripId(saved.id)
    setSelectedDay(1)
    setError('')
    setView('create')
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!supabase) {
      setSessionError('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to the project-root .env, then restart Vite.')
      return
    }
    setAuthBusy(true)
    setSessionError('')
    setAuthNotice('')
    try {
      const result = authMode === 'signup'
        ? await supabase.auth.signUp({
            email,
            password,
            options: { emailRedirectTo: window.location.origin },
          })
        : await supabase.auth.signInWithPassword({ email, password })
      if (result.error) throw result.error
      if (authMode === 'signup' && !result.data.session) {
        setAuthMode('signin')
        setPassword('')
        setAuthNotice('Account created. Check your email for the confirmation link, then sign in here.')
      } else {
        setPassword('')
        setAuthNotice('')
      }
    } catch (reason) {
      setSessionError(messageOf(reason))
    } finally {
      setAuthBusy(false)
    }
  }

  async function handleSignOut() {
    if (!supabase) return
    const { error: signOutError } = await supabase.auth.signOut()
    if (signOutError) setError(`Sign out failed: ${signOutError.message}`)
  }

  const activityCount = itinerary?.itinerary.reduce((total, day) => total + day.activities.length, 0) ?? 0

  if (!sessionChecked) {
    return <AppStatusPage title="Checking your session" message="Connecting securely to your account…" />
  }

  if (!session) {
    return (
      <AuthPage
        mode={authMode}
        email={email}
        password={password}
        showPassword={showPassword}
        busy={authBusy}
        supabaseConfigured={supabaseConfigured}
        sessionError={sessionError}
        authNotice={authNotice}
        apiHealth={apiHealth}
        apiHealthError={apiHealthError}
        onSubmit={(event) => void handleAuth(event)}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onTogglePassword={() => setShowPassword((shown) => !shown)}
        onModeChange={(mode) => {
          setAuthMode(mode)
          setSessionError('')
          setAuthNotice('')
        }}
        onRetrySession={() => {
          setSessionChecked(false)
          setSessionError('')
          if (!supabase) {
            setSessionChecked(true)
            return
          }
          void supabase.auth.getSession()
            .then(({ data, error: sessionLoadError }) => {
              if (sessionLoadError) throw sessionLoadError
              setSession(data.session)
            })
            .catch((reason: unknown) => setSessionError(messageOf(reason)))
            .finally(() => setSessionChecked(true))
        }}
      />
    )
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}>
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setView('create') }}>
          <span className="brand-mark"><Compass size={21} strokeWidth={2.2} /></span>
          <span>wayfarer<span className="brand-period">.</span></span>
        </a>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          <button className={`nav-link ${view === 'create' ? 'nav-active' : ''}`} onClick={() => { setView('create'); setMobileNavOpen(false) }}>
            <Plus size={18} /> Plan a trip
          </button>
          <button className={`nav-link ${view === 'saved' ? 'nav-active' : ''}`} onClick={() => { setView('saved'); setMobileNavOpen(false) }}>
            <Bookmark size={17} /> Saved trips
            {savedTrips.length > 0 && <span className="nav-count">{savedTrips.length}</span>}
          </button>
        </nav>

        <div className="sidebar-note">
          <div className="note-icon"><Sparkles size={16} /></div>
          <p className="note-title">Travel, thoughtfully.</p>
          <p className="note-copy">Your next great story starts with a little inspiration.</p>
        </div>

        <div className="sidebar-bottom">
          <div className="avatar">{userEmail ? userEmail[0].toUpperCase() : 'W'}</div>
          <div className="account-copy">
            <strong>{userEmail ? userEmail.split('@')[0] : 'Your account'}</strong>
            <span>{userEmail ?? 'Sign in to save trips'}</span>
          </div>
          {userEmail ? (
            <button className="icon-button account-action" onClick={() => void handleSignOut()} aria-label="Sign out" title="Sign out">
              <LogOut size={16} />
            </button>
          ) : null}
        </div>
      </aside>

      {mobileNavOpen && <button className="mobile-backdrop" aria-label="Close menu" onClick={() => setMobileNavOpen(false)} />}
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileNavOpen(!mobileNavOpen)} aria-label="Open menu"><Menu size={20} /></button>
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{view === 'saved' ? 'Saved trips' : 'Trip planner'}</strong></div>
          <div className="topbar-right">
            <span className="status-dot" /> Your next adventure awaits
            <button className="topbar-avatar" onClick={() => void handleSignOut()} aria-label="Sign out">
              {userEmail ? userEmail[0].toUpperCase() : 'W'}
            </button>
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="alert" role="alert">
              <span>{error}</span><button className="alert-close" onClick={() => setError('')} aria-label="Dismiss"><X size={16} /></button>
            </div>
          )}
          {view === 'saved' ? (
            <SavedTrips
              trips={savedTrips}
              loading={loadingTrips}
              onSelect={openSavedTrip}
              onCreate={() => setView('create')}
            />
          ) : (
            <>
              <section className="welcome-row">
                <div>
                  <div className="eyebrow"><span className="eyebrow-line" /> THE ART OF GETTING AWAY</div>
                  <h1>Where to <span className="serif-accent">next?</span></h1>
                  <p className="page-intro">A trip that feels like you, from the very first day.</p>
                </div>
                <div className="welcome-stamp"><Compass size={18} /><span>MADE FOR<br />THE CURIOUS</span></div>
              </section>

              <section className="planner-grid">
                <form className="builder-card" onSubmit={handleGenerate}>
                  <div className="card-heading">
                    <div><span className="step-label">YOUR CANVAS</span><h2>Build your trip</h2></div>
                    <span className="sparkle-chip"><Sparkles size={15} /> AI powered</span>
                  </div>

                  <label className="field-label" htmlFor="destination">Where would you like to go?</label>
                  <div className="input-wrap destination-wrap">
                    <MapPin size={17} />
                    <input
                      id="destination"
                      required
                      minLength={2}
                      maxLength={120}
                      placeholder="A city, a country, or a daydream..."
                      value={trip.destination}
                      onChange={(event) => patchTrip('destination', event.target.value)}
                    />
                  </div>

                  <div className="field-row date-row">
                    <div className="field-group">
                      <label className="field-label" htmlFor="start-date">Arrive</label>
                      <div className="input-wrap"><CalendarDays size={16} /><input id="start-date" type="date" required value={trip.start_date} onChange={(event) => patchTrip('start_date', event.target.value)} /></div>
                    </div>
                    <div className="date-connector"><ArrowRight size={14} /></div>
                    <div className="field-group">
                      <label className="field-label" htmlFor="end-date">Depart</label>
                      <div className="input-wrap"><CalendarDays size={16} /><input id="end-date" type="date" required min={trip.start_date} value={trip.end_date} onChange={(event) => patchTrip('end_date', event.target.value)} /></div>
                    </div>
                  </div>

                  <div className="section-divider" />
                  <div className="field-row">
                    <div className="field-group">
                      <span className="field-label"><Wallet size={14} /> Your budget</span>
                      <div className="segmented-control">
                        {(['Budget', 'Moderate', 'Luxury'] as Budget[]).map((option) => (
                          <button key={option} type="button" className={trip.budget === option ? 'segment selected' : 'segment'} onClick={() => patchTrip('budget', option)}>{option}</button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="field-row style-row">
                    <div className="field-group">
                      <span className="field-label"><Heart size={14} /> Travel style</span>
                      <div className="style-options">
                        {(['Solo', 'Couple', 'Family', 'Friends'] as TravelStyle[]).map((style) => (
                          <button key={style} type="button" className={`style-option ${trip.travel_style === style ? 'style-selected' : ''}`} onClick={() => patchTrip('travel_style', style)}>
                            <span className="style-emoji">{style === 'Solo' ? '✦' : style === 'Couple' ? '♡' : style === 'Family' ? '⌂' : '✧'}</span>{style}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="field-row group-row">
                    <label className="field-label" htmlFor="group-size"><Users size={14} /> Travellers</label>
                    <div className="stepper">
                      <button type="button" aria-label="Remove traveller" onClick={() => patchTrip('group_size', Math.max(1, trip.group_size - 1))}>−</button>
                      <span>{trip.group_size} <span className="traveller-word">{trip.group_size === 1 ? 'traveller' : 'travellers'}</span></span>
                      <button type="button" aria-label="Add traveller" onClick={() => patchTrip('group_size', Math.min(20, trip.group_size + 1))}>+</button>
                    </div>
                  </div>

                  <div className="field-group interests-group">
                    <span className="field-label">What are you drawn to?</span>
                    <div className="interest-list">
                      {interestOptions.map((interest) => (
                        <button key={interest} type="button" className={`interest-chip ${trip.interests.includes(interest) ? 'interest-selected' : ''}`} onClick={() => toggleInterest(interest)}>
                          {trip.interests.includes(interest) && <Check size={12} />}{interest}
                        </button>
                      ))}
                    </div>
                  </div>
                  {trip.interests.length === 0 && <p className="inline-hint">Choose at least one interest to personalize your trip.</p>}

                  <button className="generate-button" type="submit" disabled={busy || trip.interests.length === 0}>
                    {busy ? <><span className="spinner" /> Finding your way...</> : <><Sparkles size={17} /> Create my itinerary <ArrowRight size={16} /></>}
                  </button>
                  <p className="privacy-note"><span className="tiny-spark">✦</span> Thoughtful ideas, tailored just for you</p>
                </form>

                <section className="itinerary-column">
                  {itinerary ? (
                    <ItineraryPanel
                      itinerary={itinerary}
                      trip={trip}
                      currentDay={currentDay}
                      selectedDay={selectedDay}
                      dateLabel={dateLabel}
                      activityCount={activityCount}
                      activeTripId={activeTripId}
                      saving={saving}
                      busy={busy}
                      onSelectDay={setSelectedDay}
                      onSave={() => void handleSave()}
                      onRegenerate={(day) => void handleRegenerate(day)}
                      onNewTrip={() => { setItinerary(null); setActiveTripId(null); setView('create') }}
                    />
                  ) : (
                    <EmptyPreview busy={busy} />
                  )}
                </section>
              </section>
              <footer className="page-footer">              <span>WAYFARER © 2026</span><span>Made for the journey, not just the destination.</span><span>YOUR WORLD, WELL WANDERED</span></footer>
            </>
          )}
        </div>
      </main>

    </div>
  )
}

function AppStatusPage({ title, message }: { title: string; message: string }) {
  return (
    <main className="auth-page">
      <div className="auth-card status-card" role="status">
        <div className="modal-brand"><span className="brand-mark"><Compass size={20} /></span> wayfarer<span className="brand-period">.</span></div>
        <span className="spinner spinner-dark status-spinner" />
        <h1>{title}</h1>
        <p>{message}</p>
      </div>
    </main>
  )
}

function AuthPage({
  mode,
  email,
  password,
  showPassword,
  busy,
  supabaseConfigured,
  sessionError,
  authNotice,
  apiHealth,
  apiHealthError,
  onSubmit,
  onEmailChange,
  onPasswordChange,
  onTogglePassword,
  onModeChange,
  onRetrySession,
}: {
  mode: 'signin' | 'signup'
  email: string
  password: string
  showPassword: boolean
  busy: boolean
  supabaseConfigured: boolean
  sessionError: string
  authNotice: string
  apiHealth: ApiHealth | null
  apiHealthError: string
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onEmailChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onTogglePassword: () => void
  onModeChange: (mode: 'signin' | 'signup') => void
  onRetrySession: () => void
}) {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <a className="auth-brand" href="/" aria-label="Wayfarer home">
          <span className="brand-mark"><Compass size={21} strokeWidth={2.2} /></span>
          <span>wayfarer<span className="brand-period">.</span></span>
        </a>
        <div className="auth-copy">
          <div className="eyebrow"><span className="eyebrow-line" /> YOUR JOURNEY, YOURS</div>
          <h1 id="auth-title">{mode === 'signin' ? 'Welcome back.' : 'Make yourself at home.'}</h1>
          <p>{mode === 'signin' ? 'Sign in to see your trips and plan your next adventure.' : 'Create an account to save your journeys and keep them close.'}</p>
        </div>

        {!supabaseConfigured && (
          <div className="diagnostic-message diagnostic-error" role="alert">
            <strong>Supabase is not configured</strong>
            <span>Add <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> to the project-root <code>.env</code>, then restart Vite.</span>
          </div>
        )}
        {sessionError && (
          <div className="diagnostic-message diagnostic-error" role="alert">
            <strong>Sign-in error</strong><span>{sessionError}</span>
          </div>
        )}
        {authNotice && <div className="diagnostic-message diagnostic-success" role="status">{authNotice}</div>}

        <form className="auth-form auth-page-form" onSubmit={onSubmit}>
          <label className="field-label" htmlFor="auth-email">Email address</label>
          <input
            id="auth-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => onEmailChange(event.target.value)}
            placeholder="you@example.com"
          />
          <label className="field-label" htmlFor="auth-password">Password</label>
          <div className="password-field">
            <input
              id="auth-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              minLength={8}
              required
              value={password}
              onChange={(event) => onPasswordChange(event.target.value)}
              placeholder="At least 8 characters"
            />
            <button type="button" className="password-toggle" onClick={onTogglePassword} aria-label={showPassword ? 'Hide password' : 'Show password'}>
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          <button className="generate-button auth-submit" disabled={busy || !supabaseConfigured}>
            {busy ? <><span className="spinner" /> {mode === 'signin' ? 'Signing in...' : 'Creating account...'}</> : <>{mode === 'signin' ? <LogIn size={16} /> : <Plus size={16} />}{mode === 'signin' ? 'Sign in' : 'Create account'} <ArrowRight size={16} /></>}
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'signin' ? 'New to Wayfarer?' : 'Already have an account?'}
          <button type="button" onClick={() => onModeChange(mode === 'signin' ? 'signup' : 'signin')}>
            {mode === 'signin' ? 'Create an account' : 'Sign in'}
          </button>
        </p>

        <details className="diagnostics">
          <summary>Connection diagnostics</summary>
          <div className="diagnostics-list">
            <DiagnosticRow label="Frontend Supabase config" ok={supabaseConfigured} detail={supabaseConfigured ? 'URL and public key are set' : 'Check project-root .env'} />
            <DiagnosticRow label="Supabase session" ok={!sessionError} detail={sessionError ? 'Session check returned an error' : 'No active session; sign in to continue'} />
            <DiagnosticRow
              label="Backend API"
              ok={apiHealth?.status === 'ok'}
              detail={apiHealth?.status === 'ok' ? 'Reachable' : apiHealthError ? 'Not reachable' : 'Checking…'}
            />
            {apiHealth?.services && (
              <>
                <DiagnosticRow label="Gemini backend key" ok={apiHealth.services.gemini_configured} detail={apiHealth.services.gemini_configured ? `Present; model ${apiHealth.services.gemini_model}; provider access not tested` : 'Add GEMINI_API_KEY to backend\\.env'} />
                <DiagnosticRow label="Supabase backend keys" ok={apiHealth.services.supabase_configured} detail={apiHealth.services.supabase_configured ? 'Present; project access not tested' : 'Replace placeholder values in backend\\.env'} />
              </>
            )}
            {apiHealthError && <div className="diagnostic-detail">{apiHealthError}</div>}
            <button type="button" className="retry-session" onClick={onRetrySession}>Retry session check</button>
          </div>
        </details>
        <p className="auth-footnote">Your itinerary workspace is private to your account.</p>
      </section>
    </main>
  )
}

function DiagnosticRow({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <div className="diagnostic-row">
      <span className={`diagnostic-indicator ${ok ? 'indicator-ok' : 'indicator-warn'}`} />
      <span className="diagnostic-label">{label}</span>
      <span className="diagnostic-detail">{detail}</span>
    </div>
  )
}

function EmptyPreview({ busy }: { busy: boolean }) {
  return (
    <div className={`empty-preview ${busy ? 'preview-loading' : ''}`}>
      <div className="map-illustration">
        <div className="map-grid" />
        <svg className="route-path" viewBox="0 0 450 290" fill="none" aria-hidden="true">
          <path d="M54 232C92 211 84 139 143 151S207 207 236 147 284 55 321 91 353 186 405 56" stroke="#72917a" strokeWidth="2" strokeDasharray="5 7" />
          <circle cx="54" cy="232" r="7" fill="#d98058" stroke="#fff" strokeWidth="4" />
          <circle cx="143" cy="151" r="7" fill="#72917a" stroke="#fff" strokeWidth="4" />
          <circle cx="236" cy="147" r="7" fill="#72917a" stroke="#fff" strokeWidth="4" />
          <circle cx="321" cy="91" r="7" fill="#72917a" stroke="#fff" strokeWidth="4" />
          <circle cx="405" cy="56" r="7" fill="#d98058" stroke="#fff" strokeWidth="4" />
          <path d="M223 93c0-9 7-16 16-16s16 7 16 16c0 12-16 28-16 28s-16-16-16-28Z" fill="#d98058" />
          <circle cx="239" cy="93" r="5" fill="white" />
        </svg>
        <span className="map-caption map-caption-one">somewhere lovely</span>
        <span className="map-caption map-caption-two">your kind of place</span>
        <span className="map-caption map-caption-three">a little detour</span>
        <span className="map-coordinate">35°00' N &nbsp; 135°46' E</span>
      </div>
      <div className="preview-message">
        {busy ? <><span className="spinner spinner-dark" /><span>Finding the good stuff...</span></> : <><span className="preview-star">✳</span><span>Your story starts here</span></>}
      </div>
      <p className="preview-subcopy">{busy ? 'Gathering little-known gems and thoughtful details.' : 'Tell us where you’re headed, and we’ll take it from there.'}</p>
      <div className="preview-features">
        <span><span className="feature-mark">01</span> Made for your pace</span>
        <span><span className="feature-mark">02</span> Days that flow naturally</span>
        <span><span className="feature-mark">03</span> Room for the unexpected</span>
      </div>
    </div>
  )
}

function ItineraryPanel({
  itinerary,
  trip,
  currentDay,
  selectedDay,
  dateLabel,
  activityCount,
  activeTripId,
  saving,
  busy,
  onSelectDay,
  onSave,
  onRegenerate,
  onNewTrip,
}: {
  itinerary: ItineraryResponse
  trip: TripRequest
  currentDay: DayItinerary | undefined
  selectedDay: number
  dateLabel: string
  activityCount: number
  activeTripId: string | null
  saving: boolean
  busy: boolean
  onSelectDay: (day: number) => void
  onSave: () => void
  onRegenerate: (day: number) => void
  onNewTrip: () => void
}) {
  return (
    <div className="result-card">
      <div className="result-cover">
        <div className="cover-art">
          <div className="cover-sun" />
          <div className="cover-hill cover-hill-back" />
          <div className="cover-hill cover-hill-front" />
          <div className="cover-building">
            <span className="building-roof" /><span className="building-body"><i /><i /><i /></span>
          </div>
          <div className="cover-water" />
          <span className="cover-label">{trip.destination.toUpperCase()}</span>
          <span className="cover-index">FIELD NOTES &nbsp; Nº 001</span>
        </div>
        <div className="cover-topline"><span><Sparkles size={13} /> YOUR JOURNEY, COMPOSED</span><span className="cover-pip">01 / {String(itinerary.itinerary.length).padStart(2, '0')}</span></div>
      </div>
      <div className="result-body">
        <div className="trip-title-row">
          <div>
            <span className="trip-kicker">A LITTLE GETAWAY TO</span>
            <h2>{trip.destination}</h2>
            <p className="trip-dates"><CalendarDays size={14} /> {dateLabel} <span className="date-separator">·</span> {itinerary.itinerary.length} {itinerary.itinerary.length === 1 ? 'day' : 'days'}</p>
          </div>
          <button className={`save-button ${activeTripId ? 'saved-button' : ''}`} onClick={onSave} disabled={saving || Boolean(activeTripId)}>
            {saving ? <span className="spinner spinner-dark" /> : activeTripId ? <Check size={16} /> : <Bookmark size={15} />}
            {saving ? 'Saving...' : activeTripId ? 'Saved' : 'Save trip'}
          </button>
        </div>
        <p className="trip-summary">{itinerary.trip_summary}</p>
        <div className="trip-stats">
          <div><Wallet size={15} /><span><small>ESTIMATED TOTAL</small><strong>{itinerary.total_estimated_cost}</strong></span></div>
          <div><Users size={15} /><span><small>TRAVELLING</small><strong>{trip.group_size} {trip.group_size === 1 ? 'person' : 'people'}</strong></span></div>
          <div><Sparkles size={15} /><span><small>PLANNED FOR</small><strong>{activityCount} moments</strong></span></div>
        </div>

        <div className="itinerary-heading"><div><span className="step-label">THE GOOD PART</span><h3>Your days, unrushed.</h3></div><button className="refresh-day" onClick={() => onRegenerate(selectedDay)} disabled={busy || !activeTripId} title={!activeTripId ? 'Save the trip to refresh a day' : 'Refresh this day'}><RefreshCw size={14} /> Refine day</button></div>
        <div className="day-tabs" role="tablist" aria-label="Itinerary days">
          {itinerary.itinerary.map((day) => (
            <button key={day.day} role="tab" aria-selected={selectedDay === day.day} className={`day-tab ${selectedDay === day.day ? 'day-tab-active' : ''}`} onClick={() => onSelectDay(day.day)}>
              <span>DAY {String(day.day).padStart(2, '0')}</span><strong>{new Date(`${day.date}T12:00:00`).toLocaleDateString('en-US', { weekday: 'short' })}</strong>
            </button>
          ))}
        </div>
        {currentDay && (
          <div className="activity-list">
            {currentDay.activities.map((activity, index) => <ActivityCard activity={activity} key={`${currentDay.day}-${index}`} />)}
          </div>
        )}
        <div className="endnote"><span className="endnote-rule" /><span>GOOD PLANS LEAVE ROOM FOR MAGIC</span><span className="endnote-rule" /></div>
        <button className="new-trip-button" onClick={onNewTrip}><Plus size={15} /> Plan another trip</button>
      </div>
    </div>
  )
}

function ActivityCard({ activity }: { activity: Activity }) {
  return (
    <article className="activity-card">
      <div className="activity-time">{activity.time_slot}</div>
      <div className="activity-marker"><span className={`category-dot ${categoryClass[activity.category]}`} /></div>
      <div className="activity-content">
        <div className="activity-title-row"><h4>{activity.title}</h4><span className={`category-badge ${categoryClass[activity.category]}`}>{activity.category}</span></div>
        <p>{activity.description}</p>
        <div className="activity-meta"><span><MapPin size={12} /> {activity.location}</span><span>{activity.estimated_cost}</span></div>
      </div>
    </article>
  )
}

function SavedTrips({
  trips,
  loading,
  onSelect,
  onCreate,
}: {
  trips: SavedTrip[]
  loading: boolean
  onSelect: (trip: SavedTrip) => void
  onCreate: () => void
}) {
  return (
    <section className="saved-page">
      <div className="eyebrow"><span className="eyebrow-line" /> THE PLACES THAT STAY WITH YOU</div>
      <div className="saved-heading-row"><div><h1>Your <span className="serif-accent">field notes.</span></h1><p className="page-intro">Every journey you’ve saved, ready when you are.</p></div><button className="generate-button saved-new-button" onClick={onCreate}><Plus size={16} /> Plan a trip</button></div>
      {loading ? <div className="saved-state"><span className="spinner spinner-dark" /> Gathering your journeys...</div> :
        trips.length === 0 ? (
          <div className="saved-empty"><div className="saved-empty-icon"><Compass size={23} /></div><h2>A blank page, in the best way.</h2><p>Your next favorite place is just around the corner.</p><button className="generate-button" onClick={onCreate}><Sparkles size={16} /> Dream up a trip</button></div>
        ) : (
          <div className="saved-grid">{trips.map((trip, index) => (
            <button className="saved-card" key={trip.id} onClick={() => onSelect(trip)}>
              <div className={`saved-art saved-art-${index % 4}`}><span>FIELD NOTES &nbsp; Nº {String(index + 1).padStart(2, '0')}</span><span className="saved-art-label">{trip.destination}</span><Compass size={22} /></div>
              <div className="saved-card-body"><span className="saved-card-date">{formatTripDate(trip.start_date, trip.end_date)}</span><h3>{trip.destination}</h3><p>{trip.trip_summary || `${trip.travel_style} · ${trip.budget_tier}`}</p><span className="saved-card-open">Open itinerary <ArrowRight size={14} /></span></div>
            </button>
          ))}</div>
        )}
    </section>
  )
}

function formatTripDate(start: string, end: string) {
  const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }
  return `${new Date(`${start}T12:00:00`).toLocaleDateString('en-US', options)} — ${new Date(`${end}T12:00:00`).toLocaleDateString('en-US', { ...options, year: 'numeric' })}`
}

function messageOf(reason: unknown): string {
  return reason instanceof Error ? reason.message : 'Something went wrong. Please try again.'
}

export default App
