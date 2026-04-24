"""
config.py – centralised configuration & API key loader for StyleAI.
All keys are read from environment variables (set via .env or system env).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL:   str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# ── OpenWeatherMap ─────────────────────────────────────────────────────────────
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE:    str = "https://api.openweathermap.org/data/2.5"

# ── News API ───────────────────────────────────────────────────────────────────
NEWS_API_KEY:  str = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE: str = "https://newsapi.org/v2"

# ── Pexels (outfit inspiration images – free, simple API key, no OAuth) ───────
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
PEXELS_BASE:    str = "https://api.pexels.com/v1"

# ── Agent loop limits ─────────────────────────────────────────────────────────
MAX_AGENT_STEPS: int = 8          # max tool-call rounds
MAX_TOKENS:      int = 2048

# ── Logs ──────────────────────────────────────────────────────────────────────
LOGS_DIR: str = os.path.join(os.path.dirname(__file__), "..", "logs")
