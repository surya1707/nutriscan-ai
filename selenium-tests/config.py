"""
Central configuration for the NutriScan AI Selenium suite.

Everything that could plausibly change between a laptop run and a GitHub
Actions run lives here and is resolved from environment variables, with
sane defaults for local development.

IMPORTANT — read before changing BASE_URL:
This suite tests the WEB APP ONLY, and it runs against a *built, served*
copy of web/dist (via `vite preview`, started by the CI workflow) or
against the live GitHub Pages deployment. There is deliberately NO
backend server started alongside it (see README "Why no backend" and
docs/AUDIT_REPORT-style design notes below). The app under test is a
Firebase-auth React SPA, so:
  - Guest mode is the only login path that is fully automatable in CI
    (Google OAuth needs a real Google account + popup; magic-link email
    needs inbox access — neither is safely scriptable in headless CI).
  - Any call that reaches the FastAPI backend (VITE_API_URL) will fail
    with a network error in CI, and the suite tests that this is handled
    *gracefully* by the UI rather than expecting a live backend response.
"""

import os


def _bool_env(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# ── Target ────────────────────────────────────────────────────────────────
# Default: a `vite preview` server the CI workflow starts itself (self
# contained, doesn't depend on GitHub Pages having redeployed yet).
# Override with BASE_URL env var (or --base-url CLI flag) to point at the
# live GitHub Pages deployment instead, e.g.:
#   https://surya1707.github.io/nutriscan-ai/
BASE_URL = os.environ.get("BASE_URL", "http://localhost:4173/nutriscan-ai/").rstrip("/") + "/"

HEADLESS = _bool_env("HEADLESS", True)

# Selenium waits
DEFAULT_TIMEOUT = int(os.environ.get("SELENIUM_TIMEOUT", "15"))
SHORT_TIMEOUT = int(os.environ.get("SELENIUM_SHORT_TIMEOUT", "5"))
LOGIN_REDIRECT_TIMEOUT = int(os.environ.get("SELENIUM_LOGIN_TIMEOUT", "10"))

# ── Routes (BrowserRouter, basename="/nutriscan-ai/", GitHub Pages
#    404.html SPA-redirect trick handles deep links — see web/public/404.html)
ROUTES = {
    "login": "login",
    "home": "",
    "history": "history",
    "profile": "profile",
    "scan": "scan",
    "results": "results/new",
    "unknown": "this-route-does-not-exist",
}

# ── localStorage keys the app reads/writes (see src/store/authStore.ts) ───
GUEST_KEY = "nutriscan_is_guest"
EMAIL_LINK_KEY = "nutriscan_email_for_signin"

# ── Responsive breakpoints (see web/src/components/layout/AppShell.tsx
#    inline <style> block — these are the exact px values the app itself
#    switches layout at, not arbitrary guesses)
VIEWPORTS = {
    "mobile": (390, 844),      # < 768px  -> bottom tab bar
    "tablet": (820, 1180),     # 768-1023px -> hamburger + drawer
    "desktop": (1440, 900),    # >= 1024px -> fixed sidebar
}

# ── Reporting ────────────────────────────────────────────────────────────
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
RESULTS_DIR = os.path.join(REPORTS_DIR, "results")       # per-worker raw JSON
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
LOGS_DIR = os.path.join(REPORTS_DIR, "logs")

# ── Pass-rate gate ──────────────────────────────────────────────────────
# One number, used consistently in both the job-summary display and the
# enforcement step (the reference audit this suite is based on flagged a
# 95%-displayed / 90%-enforced mismatch as a bug — don't reintroduce it).
PASS_RATE_THRESHOLD = float(os.environ.get("PASS_RATE_THRESHOLD", "95"))
