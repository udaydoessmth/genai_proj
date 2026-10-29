"""
ATLAS — AI Travel Itinerary Planner
Streamlit deployment with Supabase auth/storage and Gemini AI.
"""

import json
import os
import streamlit as st
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator, ValidationError

# ─────────────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ATLAS — AI Travel Planner",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────
# Custom CSS — bold minimal black & white editorial design
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;600;700;800&family=Newsreader:ital,opsz,wght@1,6..72,400;1,6..72,500&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

st.markdown("""
<style>
/* ── Global ────────────────────────────────────────────────── */
html, body, .stApp, .stApp * {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
:root {
    --ink: #000000;
    --muted: #666666;
    --line: #e5e5e5;
    --line-bold: #000000;
    --paper: #ffffff;
    --accent: #000000;
    --bg: #ffffff;
    --bg-subtle: #f8f8f8;
}
#MainMenu, header, footer { visibility: hidden !important; }
.stApp { background: #ffffff !important; color: #000000 !important; }
.block-container { max-width: 1200px; padding: 2.2rem 2.5rem !important; }

/* ── Sidebar ───────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1.5px solid #000000 !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 13px;
    color: #444444;
}
.wf-brand {
    display: flex; align-items: center; gap: 10px;
    margin: 0 0 30px 0; text-decoration: none; color: #000000;
    font: 800 22px 'Space Grotesk', sans-serif; letter-spacing: -0.8px;
    text-transform: uppercase;
}
.wf-brand-mark {
    display: grid; width: 34px; height: 34px; place-items: center;
    border-radius: 4px; background: #000000; color: #ffffff;
    font-size: 17px;
}
.wf-brand-period { color: #000000; }
.wf-sidebar-note {
    position: relative; overflow: hidden; margin: 20px 0;
    border: 1.5px solid #000000; border-radius: 6px;
    background: #fafafa; padding: 16px 14px;
    box-shadow: 3px 3px 0px #000000;
}
.wf-note-title {
    margin: 4px 0 4px; font: 700 12px 'Space Grotesk', sans-serif;
    color: #000000; text-transform: uppercase; letter-spacing: 0.5px;
}
.wf-note-copy { margin: 0; color: #555555; font-size: 11px; line-height: 1.6; }
.wf-user-bar {
    display: flex; align-items: center; gap: 10px;
    border-top: 1.5px solid #000000; padding: 16px 0 0; margin-top: 20px;
}
.wf-avatar {
    display: grid; width: 36px; height: 36px; flex: 0 0 auto;
    place-items: center; border-radius: 4px;
    background: #000000; color: #ffffff;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px; font-weight: 800;
}
.wf-user-info { min-width: 0; }
.wf-user-name { font-size: 12px; font-weight: 700; color: #000000; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-user-email { font-size: 11px; color: #777777; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Buttons ───────────────────────────────────────────────── */
.stButton > button {
    border-radius: 4px !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stFormSubmitButton"] > button,
button[kind="primary"] {
    background: #000000 !important;
    color: #ffffff !important;
    border: 1.5px solid #000000 !important;
    padding: 0.7rem 1.4rem !important;
    font-size: 13px !important;
    border-radius: 4px !important;
}
div[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primary"]:hover {
    background: #ffffff !important;
    color: #000000 !important;
    border-color: #000000 !important;
    box-shadow: 3px 3px 0px #000000 !important;
    transform: translate(-1px, -1px);
}
button[kind="secondary"] {
    background: #ffffff !important;
    color: #000000 !important;
    border: 1.5px solid #000000 !important;
}
button[kind="secondary"]:hover {
    background: #000000 !important;
    color: #ffffff !important;
}

/* ── Inputs ────────────────────────────────────────────────── */
.stTextInput input, .stDateInput input, .stNumberInput input {
    border: 1.5px solid #000000 !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    color: #000000 !important;
    background: #ffffff !important;
}
.stTextInput input:focus, .stDateInput input:focus, .stNumberInput input:focus {
    border-color: #000000 !important;
    box-shadow: 3px 3px 0px #000000 !important;
    outline: none !important;
}
.stTextInput input::placeholder { color: #888888 !important; }
.stMultiSelect [data-baseweb="tag"] {
    background: #000000 !important;
    color: #ffffff !important;
    border-radius: 3px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
}

/* ── Tabs ──────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 2px solid #000000;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 4px 4px 0 0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    padding: 8px 16px !important;
    color: #737373 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
.stTabs [aria-selected="true"] {
    background: #000000 !important;
    color: #ffffff !important;
    border-bottom: none !important;
}

/* ── Radio (horizontal) ────────────────────────────────────── */
.stRadio > div { gap: 0 !important; }
.stRadio [role="radiogroup"] { gap: 6px !important; }
.stRadio label {
    border: 1.5px solid #d4d4d4 !important;
    border-radius: 4px !important;
    padding: 8px 14px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    background: #ffffff !important;
    color: #000000 !important;
    transition: all 0.15s !important;
}
.stRadio label[data-checked="true"],
.stRadio label:has(input:checked) {
    border-color: #000000 !important;
    background: #000000 !important;
    color: #ffffff !important;
}

/* ── Auth Page ─────────────────────────────────────────────── */
.wf-auth-page {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 70vh; text-align: center;
}
.wf-auth-card {
    width: 100%; max-width: 440px;
    border: 2px solid #000000; border-radius: 8px;
    background: #ffffff; padding: 34px 34px 26px;
    box-shadow: 6px 6px 0px #000000;
}
.wf-auth-card h1 {
    margin: 14px 0 6px; color: #000000;
    font: 800 28px 'Space Grotesk', sans-serif; letter-spacing: -0.8px;
    text-transform: uppercase;
}
.wf-auth-card p { color: #555555; font-size: 12px; line-height: 1.6; }
.wf-eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    color: #000000; font-family: 'Space Grotesk', sans-serif;
    font-size: 11px; font-weight: 800; letter-spacing: 2px;
    text-transform: uppercase;
}
.wf-eyebrow-line {
    display: inline-block; width: 22px; height: 2px; background: #000000;
}

/* ── Itinerary Cover ───────────────────────────────────────── */
.wf-cover {
    position: relative; height: 190px; overflow: hidden;
    border-radius: 6px 6px 0 0;
    background: #000000;
    border-bottom: 2px solid #000000;
}
.wf-cover-grid {
    position: absolute; inset: 0;
    background-image: linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px);
    background-size: 24px 24px;
}
.wf-cover-circle {
    position: absolute; top: -30px; right: 12%;
    width: 200px; height: 200px; border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.2);
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
}
.wf-cover-sun, .wf-cover-hill, .wf-cover-water { display: none; }
.wf-cover-label {
    position: absolute; z-index: 2; bottom: 20px; left: 24px;
    color: #ffffff; font: 800 32px 'Space Grotesk', sans-serif;
    letter-spacing: -0.5px; text-transform: uppercase;
}
.wf-cover-topline {
    position: absolute; z-index: 2; top: 16px; left: 24px; right: 24px;
    display: flex; justify-content: space-between;
    color: #999999; font-family: 'Space Grotesk', sans-serif;
    font-size: 10px; font-weight: 800; letter-spacing: 2px;
}

/* ── Activity Timeline ─────────────────────────────────────── */
.wf-activity {
    display: grid; grid-template-columns: 60px 18px 1fr;
    gap: 12px; padding: 14px 0; position: relative;
}
.wf-activity + .wf-activity { border-top: 1px solid #e5e5e5; }
.wf-activity-time {
    padding-top: 2px; color: #000000;
    font-family: 'Space Grotesk', monospace;
    font-size: 11px; font-weight: 700; text-align: right;
}
.wf-activity-marker {
    display: flex; justify-content: center; position: relative;
}
.wf-dot {
    z-index: 1; width: 10px; height: 10px; margin-top: 5px;
    border: 2px solid #ffffff; border-radius: 50%;
    background: #000000; box-shadow: 0 0 0 2px #000000;
}
.wf-activity-content { min-width: 0; }
.wf-activity-header {
    display: flex; align-items: center; justify-content: space-between;
    gap: 8px; margin-bottom: 4px;
}
.wf-activity-header h4 {
    margin: 0; color: #000000;
    font: 700 13px 'Space Grotesk', sans-serif; letter-spacing: -0.2px;
}
.wf-badge {
    flex: 0 0 auto; border-radius: 3px; padding: 3px 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9px; font-weight: 800; letter-spacing: 0.5px;
    text-transform: uppercase; border: 1.5px solid #000000;
}
.wf-badge.sightseeing { background: #000000; color: #ffffff; }
.wf-badge.dining { background: #ffffff; color: #000000; }
.wf-badge.transport { background: #f0f0f0; color: #000000; }
.wf-badge.stay { background: #1a1a1a; color: #ffffff; }
.wf-badge.experience { background: #ffffff; color: #000000; border-style: dashed; }
.wf-activity-desc {
    margin: 0 0 6px; color: #444444;
    font-size: 12px; line-height: 1.6;
}
.wf-activity-meta {
    display: flex; justify-content: space-between; gap: 8px;
    color: #777777; font-size: 11px; font-weight: 500;
}

/* ── Stats Bar ─────────────────────────────────────────────── */
.wf-stats {
    display: grid; grid-template-columns: repeat(3, 1fr);
    border: 1.5px solid #000000;
    background: #fafafa;
    padding: 14px 0; margin: 16px 0;
}
.wf-stat {
    display: flex; flex-direction: column; gap: 4px;
    padding: 0 16px;
}
.wf-stat + .wf-stat { border-left: 1.5px solid #000000; }
.wf-stat-label {
    color: #555555; font-family: 'Space Grotesk', sans-serif;
    font-size: 9px; font-weight: 800; letter-spacing: 1px;
}
.wf-stat-value {
    color: #000000; font-family: 'Space Grotesk', sans-serif;
    font-size: 14px; font-weight: 800;
}

/* ── Saved Trip Cards ──────────────────────────────────────── */
.wf-saved-card {
    overflow: hidden; border: 2px solid #000000; border-radius: 6px;
    background: #ffffff; box-shadow: 4px 4px 0px #000000;
    transition: transform 0.15s, box-shadow 0.15s; margin-bottom: 12px;
}
.wf-saved-card:hover {
    transform: translate(-2px, -2px);
    box-shadow: 6px 6px 0px #000000;
}
.wf-saved-art {
    position: relative; height: 130px; overflow: hidden;
    display: flex; align-items: flex-end; justify-content: space-between;
    padding: 14px; color: #ffffff; background: #000000;
    border-bottom: 2px solid #000000;
}
.wf-saved-art::before, .wf-saved-art::after { display: none; }
.wf-saved-index {
    position: absolute; top: 12px; left: 14px; z-index: 1;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9px; font-weight: 800; letter-spacing: 1.5px;
    color: #999999;
}
.wf-saved-dest {
    z-index: 1; font: 800 20px 'Space Grotesk', sans-serif;
    text-transform: uppercase; letter-spacing: -0.5px;
    max-width: 85%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.wf-saved-body { padding: 14px; }
.wf-saved-body h3 {
    margin: 6px 0 4px; color: #000000;
    font: 700 16px 'Space Grotesk', sans-serif; text-transform: uppercase;
}
.wf-saved-body p {
    color: #555555; font-size: 11px; line-height: 1.6;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
    min-height: 32px; margin: 0 0 10px;
}
.wf-saved-date {
    color: #777777; font-family: 'Space Grotesk', sans-serif;
    font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
}

/* ── Summary Card ──────────────────────────────────────────── */
.wf-summary-card {
    border: 2px solid #000000; border-radius: 8px;
    background: #ffffff; box-shadow: 6px 6px 0px #000000;
    overflow: hidden;
}
.wf-summary-body { padding: 22px; }
.wf-trip-kicker {
    color: #666666; font-family: 'Space Grotesk', sans-serif;
    font-size: 9px; font-weight: 800; letter-spacing: 1.5px;
}
.wf-trip-title {
    margin: 6px 0 8px; color: #000000;
    font: 800 28px 'Space Grotesk', sans-serif; letter-spacing: -1px;
    text-transform: uppercase;
}
.wf-trip-summary {
    color: #333333; font-size: 13px; line-height: 1.7; margin: 0;
}

/* ── Empty State ───────────────────────────────────────────── */
.wf-empty {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; text-align: center;
    min-height: 450px; border: 2px dashed #000000;
    border-radius: 8px; background: #fafafa; padding: 30px;
}
.wf-empty-icon {
    width: 52px; height: 52px; display: grid; place-items: center;
    border-radius: 6px; background: #000000; color: #ffffff;
    font-size: 24px; margin-bottom: 16px;
}
.wf-empty h3 {
    margin: 0 0 6px; color: #000000;
    font: 800 20px 'Space Grotesk', sans-serif; text-transform: uppercase;
}
.wf-empty p { color: #666666; font-size: 13px; margin: 0; }

/* ── Footer ────────────────────────────────────────────────── */
.wf-footer {
    display: flex; justify-content: space-between;
    margin: 36px 0 0; color: #888888;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9px; font-weight: 700; letter-spacing: 1px;
    border-top: 1px solid #e5e5e5; padding-top: 16px;
}

/* ── Sparkle chip ──────────────────────────────────────────── */
.wf-sparkle-chip {
    display: inline-flex; align-items: center; gap: 5px;
    border: 1.5px solid #000000; border-radius: 4px;
    background: #ffffff; padding: 4px 10px;
    color: #000000; font-family: 'Space Grotesk', sans-serif;
    font-size: 10px; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Endnote ───────────────────────────────────────────────── */
.wf-endnote {
    display: flex; align-items: center; gap: 12px;
    margin: 24px 0 12px; color: #000000;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 9px; font-weight: 800; letter-spacing: 2px; text-align: center;
}
.wf-endnote-rule { height: 1.5px; flex: 1; background: #000000; }

/* ── Misc ──────────────────────────────────────────────────── */
.wf-section-label {
    color: #000000; font-family: 'Space Grotesk', sans-serif;
    font-size: 10px; font-weight: 800; letter-spacing: 2px;
    text-transform: uppercase;
}
.wf-heading {
    margin: 6px 0 0; color: #000000;
    font: 800 36px 'Space Grotesk', sans-serif; letter-spacing: -1.2px;
}
.wf-heading-accent {
    color: #000000; font-family: 'Newsreader', Georgia, serif;
    font-size: 1.1em; font-style: italic; font-weight: 400;
    text-decoration: underline; text-underline-offset: 4px;
    text-decoration-thickness: 2px;
}
.wf-page-intro { color: #555555; font-size: 14px; margin: 4px 0 0; }
.wf-divider { height: 1.5px; background: #000000; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Pydantic Models (for Gemini structured output)
# ─────────────────────────────────────────────────────────────────────
ActivityCategory = Literal[
    "Dining", "Sightseeing", "Transport", "Accommodation", "Experience"
]


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
            raise ValueError("Itinerary days must be sequential starting at 1.")
        return self


# ─────────────────────────────────────────────────────────────────────
# Configuration — reads from Streamlit secrets, falls back to env vars
# ─────────────────────────────────────────────────────────────────────
def get_config(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, then environment variables."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.environ.get(key, default)


SUPABASE_URL = get_config("SUPABASE_URL")
SUPABASE_ANON_KEY = get_config("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = get_config("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = get_config("GEMINI_API_KEY")
GEMINI_MODEL = get_config("GEMINI_MODEL", "gemini-2.5-flash")


def is_configured(value: str) -> bool:
    v = value.strip().lower()
    return bool(v) and not v.startswith(("your_", "your-"))


def all_configured() -> list[str]:
    """Return list of missing config keys."""
    missing: list[str] = []
    if not is_configured(SUPABASE_URL):
        missing.append("SUPABASE_URL")
    if not is_configured(SUPABASE_ANON_KEY):
        missing.append("SUPABASE_ANON_KEY")
    if not is_configured(SUPABASE_SERVICE_ROLE_KEY):
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if not is_configured(GEMINI_API_KEY):
        missing.append("GEMINI_API_KEY")
    return missing


# ─────────────────────────────────────────────────────────────────────
# Client initialisation
# ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def _get_admin_supabase():
    """Supabase client with service-role key for data operations."""
    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _get_auth_supabase():
    """Fresh Supabase client for auth operations (anon key)."""
    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# ─────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "user_id": None,
    "user_email": None,
    "itinerary": None,
    "trip_data": None,
    "active_trip_id": None,
    "page": "plan",
    "saved_trips": [],
    "auth_error": "",
    "auth_notice": "",
}


def _init_state():
    for key, val in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────────────────────────────
def _sign_in(email: str, password: str):
    try:
        client = _get_auth_supabase()
        resp = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if resp.user:
            st.session_state.user_id = resp.user.id
            st.session_state.user_email = resp.user.email
            st.session_state.auth_error = ""
            st.session_state.auth_notice = ""
            st.rerun()
        else:
            st.session_state.auth_error = "Sign-in failed. Please try again."
    except Exception as exc:
        msg = str(exc)
        if "Invalid login credentials" in msg:
            st.session_state.auth_error = "Invalid email or password."
        elif "Email not confirmed" in msg:
            st.session_state.auth_error = (
                "Please confirm your email address first."
            )
        else:
            st.session_state.auth_error = msg


def _sign_up(email: str, password: str):
    try:
        client = _get_auth_supabase()
        resp = client.auth.sign_up({"email": email, "password": password})
        if resp.user and resp.session:
            st.session_state.user_id = resp.user.id
            st.session_state.user_email = resp.user.email
            st.session_state.auth_error = ""
            st.session_state.auth_notice = ""
            st.rerun()
        elif resp.user:
            st.session_state.auth_error = ""
            st.session_state.auth_notice = (
                "Account created! Check your email for the confirmation link, "
                "then sign in."
            )
        else:
            st.session_state.auth_error = "Could not create account."
    except Exception as exc:
        st.session_state.auth_error = str(exc)


def _sign_out():
    for key in _DEFAULTS:
        st.session_state[key] = _DEFAULTS[key]
    st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Gemini service
# ─────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = (
    "You are ATLAS, an expert travel architect and planning assistant. Return only a JSON "
    "object matching the supplied JSON schema. Give practical suggestions and "
    "honestly label all prices and opening-hour details as estimates; never "
    "claim live availability or verified opening hours. Group each day's "
    "activities geographically to reduce travel time, include realistic "
    "transport between distant areas, leave a sensible pace, and respect "
    "the stated dates, budget, group size, style, and interests. Include "
    "at least one meal and a mix of activities each day. Accommodation "
    "suggestions should be clearly identified as suggestions, not bookings."
)


def _trip_prompt(trip_data: dict, day_number: int | None = None) -> str:
    day_instruction = (
        f"Generate only a replacement for day {day_number}; keep the same date, "
        "destination, and trip constraints."
        if day_number is not None
        else "Generate the complete trip, one itinerary entry for each calendar day."
    )
    return (
        f"Trip details: {json.dumps(trip_data, ensure_ascii=False, default=str)}\n"
        f"{day_instruction}\n"
        "Use the schema's currency-neutral cost strings and activity categories. "
        "Do not invent exact transit timetables."
    )


def _generate_itinerary(trip_data: dict) -> dict | None:
    """Generate a complete itinerary using Gemini (synchronous)."""
    from google import genai
    from google.genai import types, errors

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=_trip_prompt(trip_data),
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ItineraryResponse,
                temperature=0.7,
            ),
        )
        content = response.text
        if not content:
            st.error("Gemini returned no content. The request may have been blocked.")
            return None
        result = ItineraryResponse.model_validate_json(content)
        return result.model_dump(mode="json")
    except errors.APIError as exc:
        code = getattr(exc, "code", None)
        if code == 429:
            st.error("🚦 Gemini rate-limit reached. Please wait and try again.")
        elif code == 401:
            st.error("🔑 Invalid Gemini API key. Check your GEMINI_API_KEY.")
        elif code == 404:
            st.error(
                f"Model **{GEMINI_MODEL}** not found. "
                "Set GEMINI_MODEL to a supported model."
            )
        else:
            st.error(f"Gemini API error (HTTP {code}): {exc}")
        return None
    except (ValidationError, ValueError):
        st.error(
            "Gemini returned an itinerary that didn't match the required format. "
            "Please try again."
        )
        return None
    except Exception as exc:
        st.error(f"Itinerary generation failed: {exc}")
        return None


def _regenerate_day(trip_data: dict, day_number: int) -> dict | None:
    """Regenerate a single day (synchronous)."""
    from google import genai
    from google.genai import types

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=_trip_prompt(trip_data, day_number),
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=DayItinerary,
                temperature=0.7,
            ),
        )
        content = response.text
        if not content:
            return None
        result = DayItinerary.model_validate_json(content)
        # Enforce correct day/date
        result.day = day_number
        result.date = (
            date.fromisoformat(trip_data["start_date"])
            + timedelta(days=day_number - 1)
        )
        return result.model_dump(mode="json")
    except Exception as exc:
        st.error(f"Day regeneration failed: {exc}")
        return None


# ─────────────────────────────────────────────────────────────────────
# Supabase data operations (uses service-role key)
# ─────────────────────────────────────────────────────────────────────
def _save_trip(user_id: str, trip_data: dict, itinerary: dict) -> str | None:
    """Insert trip + itinerary rows. Returns trip_id on success."""
    try:
        admin = _get_admin_supabase()
        trip_result = (
            admin.table("trips")
            .insert(
                {
                    "user_id": user_id,
                    "destination": trip_data["destination"],
                    "budget_tier": trip_data["budget"],
                    "start_date": trip_data["start_date"],
                    "end_date": trip_data["end_date"],
                    "travel_style": trip_data["travel_style"],
                    "group_size": trip_data["group_size"],
                    "interests": trip_data["interests"],
                    "trip_summary": itinerary.get("trip_summary", ""),
                    "total_estimated_cost": itinerary.get(
                        "total_estimated_cost", ""
                    ),
                }
            )
            .execute()
        )
        if not trip_result.data:
            st.error("Supabase did not return the saved trip.")
            return None
        trip_id = trip_result.data[0]["id"]

        itinerary_rows = [
            {
                "trip_id": trip_id,
                "day_number": day["day"],
                "activities": day,
            }
            for day in itinerary["itinerary"]
        ]
        admin.table("itineraries").insert(itinerary_rows).execute()
        return trip_id
    except Exception as exc:
        st.error(f"Failed to save trip: {exc}")
        return None


def _load_saved_trips(user_id: str) -> list[dict]:
    """Fetch this user's saved trips (most recent first)."""
    try:
        admin = _get_admin_supabase()
        result = (
            admin.table("trips")
            .select(
                "id, destination, budget_tier, start_date, end_date, "
                "travel_style, group_size, interests, trip_summary, "
                "total_estimated_cost, created_at, "
                "itineraries(day_number, activities)"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        st.error(f"Failed to load trips: {exc}")
        return []


def _update_day_in_db(trip_id: str, day_number: int, day_data: dict):
    """Patch a single day's activities in Supabase."""
    try:
        admin = _get_admin_supabase()
        (
            admin.table("itineraries")
            .update({"activities": day_data})
            .eq("trip_id", trip_id)
            .eq("day_number", day_number)
            .execute()
        )
    except Exception as exc:
        st.error(f"Failed to update day: {exc}")


# ─────────────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────────────
_CATEGORY_CLASS = {
    "Dining": "dining",
    "Sightseeing": "sightseeing",
    "Transport": "transport",
    "Accommodation": "stay",
    "Experience": "experience",
}

_GRADIENT_PRESETS = [
    "linear-gradient(135deg, #000000 0%, #1a1a1a 100%)",
    "linear-gradient(135deg, #141414 0%, #2b2b2b 100%)",
    "linear-gradient(135deg, #222222 0%, #0d0d0d 100%)",
    "linear-gradient(135deg, #050505 0%, #1c1c1c 100%)",
]


def _render_activity(activity: dict):
    """Render a single activity as an HTML timeline card."""
    cat = activity.get("category", "Sightseeing")
    cls = _CATEGORY_CLASS.get(cat, "sightseeing")
    # Escape HTML to avoid injection
    import html

    st.markdown(
        f"""
        <div class="wf-activity">
            <div class="wf-activity-time">{html.escape(activity['time_slot'])}</div>
            <div class="wf-activity-marker"><span class="wf-dot {cls}"></span></div>
            <div class="wf-activity-content">
                <div class="wf-activity-header">
                    <h4>{html.escape(activity['title'])}</h4>
                    <span class="wf-badge {cls}">{html.escape(cat)}</span>
                </div>
                <p class="wf-activity-desc">{html.escape(activity['description'])}</p>
                <div class="wf-activity-meta">
                    <span>📍 {html.escape(activity['location'])}</span>
                    <span>{html.escape(activity['estimated_cost'])}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_trip_date(start: str, end: str) -> str:
    try:
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        return f"{s.strftime('%b %d')} — {e.strftime('%b %d, %Y')}"
    except ValueError:
        return f"{start} — {end}"


# ─────────────────────────────────────────────────────────────────────
# UI: Configuration error page
# ─────────────────────────────────────────────────────────────────────
def _render_config_error(missing: list[str]):
    st.markdown(
        """
        <div class="wf-auth-page">
        <div class="wf-auth-card">
            <div class="wf-brand">
                <span class="wf-brand-mark">🧭</span>
                ATLAS<span class="wf-brand-period">.</span>
            </div>
            <div class="wf-eyebrow"><span class="wf-eyebrow-line"></span> SETUP REQUIRED</div>
            <h1>Almost there.</h1>
            <p>Add the following secrets to deploy ATLAS.</p>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning(
        "**Missing configuration keys:**\n\n"
        + "\n".join(f"- `{k}`" for k in missing)
        + "\n\nAdd them to `.streamlit/secrets.toml` (local) or "
        "Streamlit Cloud → App settings → Secrets.",
    )
    st.code(
        "# .streamlit/secrets.toml\n"
        'SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"\n'
        'SUPABASE_ANON_KEY = "YOUR_PUBLIC_ANON_KEY"\n'
        'SUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY"\n'
        'GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"\n'
        'GEMINI_MODEL = "gemini-2.5-flash"\n',
        language="toml",
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────
# UI: Auth page
# ─────────────────────────────────────────────────────────────────────
def _render_auth_page():
    _col_l, center, _col_r = st.columns([1, 2, 1])
    with center:
        st.markdown(
            """
            <div style="text-align:center; margin-bottom: 10px;">
                <div class="wf-brand" style="justify-content:center;">
                    <span class="wf-brand-mark">🧭</span>
                    ATLAS<span class="wf-brand-period">.</span>
                </div>
                <div class="wf-eyebrow" style="justify-content:center;">
                    <span class="wf-eyebrow-line"></span> YOUR JOURNEY, YOURS
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_signin, tab_signup = st.tabs(["Sign In", "Create Account"])

        # ── Sign In ──
        with tab_signin:
            st.markdown(
                "<p style='color:#899389; font-size:13px; text-align:center;'>"
                "Sign in to see your trips and plan your next adventure.</p>",
                unsafe_allow_html=True,
            )
            with st.form("signin_form", clear_on_submit=False):
                si_email = st.text_input(
                    "Email address",
                    placeholder="you@example.com",
                    key="si_email",
                )
                si_pass = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                    key="si_pass",
                )
                if st.form_submit_button(
                    "✦  Sign in", use_container_width=True
                ):
                    if si_email and si_pass:
                        _sign_in(si_email, si_pass)
                    else:
                        st.session_state.auth_error = (
                            "Please enter both email and password."
                        )

        # ── Sign Up ──
        with tab_signup:
            st.markdown(
                "<p style='color:#899389; font-size:13px; text-align:center;'>"
                "Create an account to save your journeys and keep them close.</p>",
                unsafe_allow_html=True,
            )
            with st.form("signup_form", clear_on_submit=False):
                su_email = st.text_input(
                    "Email address",
                    placeholder="you@example.com",
                    key="su_email",
                )
                su_pass = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                    key="su_pass",
                )
                if st.form_submit_button(
                    "✦  Create account", use_container_width=True
                ):
                    if su_email and su_pass:
                        _sign_up(su_email, su_pass)
                    else:
                        st.session_state.auth_error = (
                            "Please enter both email and password."
                        )

        # Feedback messages
        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)
        if st.session_state.auth_notice:
            st.success(st.session_state.auth_notice)

        st.markdown(
            "<p style='text-align:center; color:#a0a79f; font-size:10px; "
            "margin-top:24px;'>"
            "Your itinerary workspace is private to your account.</p>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────
# UI: Sidebar
# ─────────────────────────────────────────────────────────────────────
def _render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="wf-brand">'
            '<span class="wf-brand-mark">🧭</span>'
            'ATLAS<span class="wf-brand-period">.</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<span class="wf-section-label">WORKSPACE</span>',
            unsafe_allow_html=True,
        )

        if st.button(
            "✦  Plan a trip",
            use_container_width=True,
            type="secondary" if st.session_state.page != "plan" else "primary",
        ):
            st.session_state.page = "plan"
            st.rerun()

        saved_count = len(st.session_state.saved_trips)
        label = f"📑  Saved trips ({saved_count})" if saved_count else "📑  Saved trips"
        if st.button(
            label,
            use_container_width=True,
            type="secondary"
            if st.session_state.page != "saved"
            else "primary",
        ):
            st.session_state.page = "saved"
            st.session_state.saved_trips = _load_saved_trips(
                st.session_state.user_id
            )
            st.rerun()

        # Inspiration note
        st.markdown(
            '<div class="wf-sidebar-note">'
            '<div class="wf-note-title">✨ Travel, thoughtfully.</div>'
            '<p class="wf-note-copy">Your next great story starts with a little inspiration.</p>'
            "</div>",
            unsafe_allow_html=True,
        )

        # User bar
        initial = (
            st.session_state.user_email[0].upper()
            if st.session_state.user_email
            else "W"
        )
        name = (
            st.session_state.user_email.split("@")[0]
            if st.session_state.user_email
            else ""
        )
        st.markdown(
            f'<div class="wf-user-bar">'
            f'<div class="wf-avatar">{initial}</div>'
            f'<div class="wf-user-info">'
            f'<div class="wf-user-name">{name}</div>'
            f'<div class="wf-user-email">{st.session_state.user_email or ""}</div>'
            f"</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Sign out", use_container_width=True):
            _sign_out()


# ─────────────────────────────────────────────────────────────────────
# UI: Trip planner page
# ─────────────────────────────────────────────────────────────────────
_INTEREST_OPTIONS = [
    "Food & drink",
    "Culture",
    "Nature",
    "Architecture",
    "Adventure",
    "Shopping",
]


def _render_planner():
    # ── Welcome header ──
    st.markdown(
        '<div class="wf-eyebrow"><span class="wf-eyebrow-line"></span> '
        "THE ART OF GETTING AWAY</div>"
        '<h1 class="wf-heading">Where to <span class="wf-heading-accent">next?</span></h1>'
        '<p class="wf-page-intro">A trip that feels like you, from the very first day.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    form_col, result_col = st.columns([4, 6], gap="large")

    # ── Form column ──
    with form_col:
        st.markdown(
            '<div style="display:flex; justify-content:space-between; align-items:center;">'
            '<div><span class="wf-section-label">YOUR CANVAS</span>'
            "<h3 style=\"margin:6px 0 0; font: 700 17px 'Manrope',sans-serif; "
            'letter-spacing:-0.5px;">Build your trip</h3></div>'
            '<span class="wf-sparkle-chip">✨ AI powered</span></div>',
            unsafe_allow_html=True,
        )

        with st.form("trip_form", clear_on_submit=False):
            destination = st.text_input(
                "Where would you like to go?",
                placeholder="A city, a country, or a daydream...",
                key="f_dest",
            )

            date_l, date_r = st.columns(2)
            with date_l:
                start_date = st.date_input(
                    "Arrive",
                    value=date.today(),
                    key="f_start",
                )
            with date_r:
                end_date = st.date_input(
                    "Depart",
                    value=date.today() + timedelta(days=7),
                    key="f_end",
                )

            st.markdown('<div class="wf-divider"></div>', unsafe_allow_html=True)

            budget = st.radio(
                "💰 Your budget",
                options=["Budget", "Moderate", "Luxury"],
                index=1,
                horizontal=True,
                key="f_budget",
            )

            travel_style = st.radio(
                "💕 Travel style",
                options=["Solo", "Couple", "Family", "Friends"],
                index=1,
                horizontal=True,
                key="f_style",
            )

            group_size = st.number_input(
                "👥 Travellers",
                min_value=1,
                max_value=20,
                value=2,
                key="f_group",
            )

            interests = st.multiselect(
                "What are you drawn to?",
                options=_INTEREST_OPTIONS,
                default=["Food & drink", "Culture"],
                key="f_interests",
            )

            generate = st.form_submit_button(
                "✨  Create my itinerary",
                use_container_width=True,
            )

        # Handle form submission
        if generate:
            if not destination or len(destination.strip()) < 2:
                st.error("Please enter a destination (at least 2 characters).")
            elif end_date < start_date:
                st.error("End date must be on or after start date.")
            elif (end_date - start_date).days > 30:
                st.error("Trips can be at most 31 calendar days long.")
            elif not interests:
                st.error("Choose at least one interest.")
            else:
                trip_data = {
                    "destination": destination.strip(),
                    "budget": budget,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "travel_style": travel_style,
                    "group_size": group_size,
                    "interests": interests,
                }
                st.session_state.trip_data = trip_data
                st.session_state.active_trip_id = None
                with st.spinner("✨ Finding your way... this may take a moment"):
                    result = _generate_itinerary(trip_data)
                if result:
                    st.session_state.itinerary = result
                    st.rerun()

    # ── Result column ──
    with result_col:
        if st.session_state.itinerary:
            _render_itinerary()
        else:
            _render_empty_state()


# ─────────────────────────────────────────────────────────────────────
# UI: Empty preview state
# ─────────────────────────────────────────────────────────────────────
def _render_empty_state():
    st.markdown(
        """
        <div class="wf-empty">
            <div class="wf-empty-icon">✦</div>
            <h3>Your story starts here</h3>
            <p>Tell us where you're headed, and we'll take it from there.</p>
            <div style="display:flex; gap:20px; margin-top:28px; color:#555555; font-size:11px;">
                <span><strong style="color:#000000; margin-right:4px;">01</strong> Made for your pace</span>
                <span><strong style="color:#000000; margin-right:4px;">02</strong> Days that flow naturally</span>
                <span><strong style="color:#000000; margin-right:4px;">03</strong> Room for the unexpected</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# UI: Itinerary display
# ─────────────────────────────────────────────────────────────────────
def _render_itinerary():
    itin = st.session_state.itinerary
    trip = st.session_state.trip_data
    if not itin or not trip:
        return

    days = itin["itinerary"]
    num_days = len(days)
    activity_count = sum(len(d["activities"]) for d in days)
    dest = trip["destination"]
    date_label = _format_trip_date(trip["start_date"], trip["end_date"])

    # Cover art
    st.markdown(
        f"""
        <div class="wf-summary-card">
            <div class="wf-cover">
                <div class="wf-cover-grid"></div>
                <div class="wf-cover-circle"></div>
                <span class="wf-cover-label">{dest}</span>
                <div class="wf-cover-topline">
                    <span>✦ YOUR JOURNEY, COMPOSED</span>
                    <span>01 / {str(num_days).zfill(2)}</span>
                </div>
            </div>
            <div class="wf-summary-body">
                <span class="wf-trip-kicker">A LITTLE GETAWAY TO</span>
                <h2 class="wf-trip-title">{dest}</h2>
                <div style="display:flex; align-items:center; gap:6px; color:#555555; font-size:11px; font-weight:600; margin-bottom:10px;">
                    📅 {date_label} · {num_days} {"day" if num_days == 1 else "days"}
                </div>
                <p class="wf-trip-summary">{itin.get("trip_summary", "")}</p>
                <div class="wf-stats">
                    <div class="wf-stat">
                        <span class="wf-stat-label">ESTIMATED TOTAL</span>
                        <span class="wf-stat-value">{itin.get("total_estimated_cost", "—")}</span>
                    </div>
                    <div class="wf-stat">
                        <span class="wf-stat-label">TRAVELLING</span>
                        <span class="wf-stat-value">{trip["group_size"]} {"person" if trip["group_size"] == 1 else "people"}</span>
                    </div>
                    <div class="wf-stat">
                        <span class="wf-stat-label">PLANNED FOR</span>
                        <span class="wf-stat-value">{activity_count} moments</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Save / status buttons
    btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 2])
    with btn_col1:
        if st.session_state.active_trip_id:
            st.success("✅ Trip saved")
        else:
            if st.button(
                "📑  Save trip", use_container_width=True, type="primary"
            ):
                with st.spinner("Saving your trip..."):
                    trip_id = _save_trip(
                        st.session_state.user_id,
                        trip,
                        itin,
                    )
                if trip_id:
                    st.session_state.active_trip_id = trip_id
                    st.session_state.saved_trips = _load_saved_trips(
                        st.session_state.user_id
                    )
                    st.rerun()
    with btn_col3:
        if st.button("✦  Plan another trip", use_container_width=True):
            st.session_state.itinerary = None
            st.session_state.trip_data = None
            st.session_state.active_trip_id = None
            st.rerun()

    st.markdown("")

    # Day-by-day itinerary
    st.markdown(
        '<div><span class="wf-section-label">THE GOOD PART</span>'
        "<h3 style=\"margin:5px 0 12px; font: 700 16px 'Manrope',sans-serif; "
        'letter-spacing:-0.35px;">Your days, unrushed.</h3></div>',
        unsafe_allow_html=True,
    )

    tab_labels = []
    for d in days:
        try:
            day_date = date.fromisoformat(str(d["date"]))
            weekday = day_date.strftime("%a")
        except (ValueError, TypeError):
            weekday = ""
        tab_labels.append(f"Day {str(d['day']).zfill(2)} · {weekday}")

    tabs = st.tabs(tab_labels)
    for tab, day in zip(tabs, days):
        with tab:
            # Refine day button (only if trip is saved)
            if st.session_state.active_trip_id:
                if st.button(
                    f"🔄 Refine Day {day['day']}",
                    key=f"regen_{day['day']}",
                ):
                    with st.spinner(
                        f"Regenerating Day {day['day']}..."
                    ):
                        new_day = _regenerate_day(trip, day["day"])
                    if new_day:
                        # Update in session state
                        idx = day["day"] - 1
                        st.session_state.itinerary["itinerary"][
                            idx
                        ] = new_day
                        # Update in Supabase
                        _update_day_in_db(
                            st.session_state.active_trip_id,
                            day["day"],
                            new_day,
                        )
                        st.session_state.saved_trips = _load_saved_trips(
                            st.session_state.user_id
                        )
                        st.rerun()

            # Render activities
            for activity in day.get("activities", []):
                _render_activity(activity)

    # Endnote
    st.markdown(
        '<div class="wf-endnote">'
        '<span class="wf-endnote-rule"></span>'
        "<span>GOOD PLANS LEAVE ROOM FOR MAGIC</span>"
        '<span class="wf-endnote-rule"></span></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# UI: Saved trips page
# ─────────────────────────────────────────────────────────────────────
def _render_saved_trips():
    st.markdown(
        '<div class="wf-eyebrow"><span class="wf-eyebrow-line"></span> '
        "THE PLACES THAT STAY WITH YOU</div>"
        '<h1 class="wf-heading">Your <span class="wf-heading-accent">field notes.</span></h1>'
        '<p class="wf-page-intro">Every journey you have saved, ready when you are.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Refresh trips list
    trips = st.session_state.saved_trips
    if not trips:
        trips = _load_saved_trips(st.session_state.user_id)
        st.session_state.saved_trips = trips

    if not trips:
        st.markdown(
            """
            <div class="wf-empty" style="min-height:340px;">
                <div class="wf-empty-icon">🧭</div>
                <h3>A blank page, in the best way.</h3>
                <p>Your next favorite place is just around the corner.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("✨  Dream up a trip", type="primary"):
            st.session_state.page = "plan"
            st.rerun()
        return

    # Grid of saved trip cards
    cols = st.columns(3, gap="medium")
    for i, trip in enumerate(trips):
        with cols[i % 3]:
            gradient = _GRADIENT_PRESETS[i % len(_GRADIENT_PRESETS)]
            dest = trip.get("destination", "Unknown")
            date_str = _format_trip_date(
                trip.get("start_date", ""), trip.get("end_date", "")
            )
            summary = trip.get("trip_summary") or (
                f"{trip.get('travel_style', '')} · {trip.get('budget_tier', '')}"
            )

            st.markdown(
                f"""
                <div class="wf-saved-card">
                    <div class="wf-saved-art" style="background:{gradient}">
                        <span class="wf-saved-index">FIELD NOTES &nbsp; Nº {str(i + 1).zfill(2)}</span>
                        <span class="wf-saved-dest">{dest}</span>
                    </div>
                    <div class="wf-saved-body">
                        <span class="wf-saved-date">{date_str}</span>
                        <h3>{dest}</h3>
                        <p>{summary[:120]}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Open itinerary →",
                key=f"open_{trip['id']}",
                use_container_width=True,
            ):
                _load_saved_trip(trip)


def _load_saved_trip(trip: dict):
    """Load a saved trip into the planner view."""
    st.session_state.trip_data = {
        "destination": trip["destination"],
        "budget": trip["budget_tier"],
        "start_date": trip["start_date"],
        "end_date": trip["end_date"],
        "travel_style": trip["travel_style"],
        "group_size": trip["group_size"],
        "interests": trip.get("interests", []),
    }

    # Reconstruct itinerary from saved data
    itineraries = trip.get("itineraries", [])
    days = sorted(
        [entry["activities"] for entry in itineraries],
        key=lambda d: d.get("day", 0),
    )
    st.session_state.itinerary = {
        "trip_summary": trip.get("trip_summary", ""),
        "total_estimated_cost": trip.get("total_estimated_cost", ""),
        "itinerary": days,
    }
    st.session_state.active_trip_id = trip["id"]

    # Update form keys so the form reflects the saved trip
    st.session_state.f_dest = trip["destination"]
    st.session_state.f_start = date.fromisoformat(trip["start_date"])
    st.session_state.f_end = date.fromisoformat(trip["end_date"])
    st.session_state.f_budget = trip["budget_tier"]
    st.session_state.f_style = trip["travel_style"]
    st.session_state.f_group = trip["group_size"]
    st.session_state.f_interests = trip.get("interests", [])

    st.session_state.page = "plan"
    st.rerun()


# ─────────────────────────────────────────────────────────────────────
# UI: Footer
# ─────────────────────────────────────────────────────────────────────
def _render_footer():
    st.markdown(
        '<div class="wf-footer">'
        "<span>ATLAS © 2026</span>"
        "<span>Made for the journey, not just the destination.</span>"
        "<span>YOUR WORLD, WELL WANDERED</span>"
        "</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
def main():
    _init_state()

    # Check configuration
    missing = all_configured()
    if missing:
        _render_config_error(missing)

    # Auth gate
    if not st.session_state.user_id:
        _render_auth_page()
        return

    # Load saved trips on first load after sign-in
    if not st.session_state.saved_trips:
        st.session_state.saved_trips = _load_saved_trips(
            st.session_state.user_id
        )

    # Sidebar
    _render_sidebar()

    # Route to the right page
    if st.session_state.page == "saved":
        _render_saved_trips()
    else:
        _render_planner()

    _render_footer()


main()
