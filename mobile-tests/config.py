"""
Central configuration for the NutriScan AI Android (Appium) suite.

Confirmed stack for THIS repo (see mobile-tests/README.md "Stack detection"
section for the full evidence table):

  - Mobile framework: Flutter, Dart SDK >=3.0.0 <4.0.0 (mobile/pubspec.yaml)
  - Router: go_router ^13.0.0 (mobile/lib/core/router/app_router.dart)
  - Auth: Firebase Auth — Google Sign-In, email link, or Guest mode
    (mobile/lib/features/auth/providers/auth_provider.dart). There is NO
    phone/password login and NO backend-issued JWT for mobile — unlike the
    web app's guest-only design, the ONLY path that is safely automatable
    in headless CI (no real Google account, no inbox access) is
    "Continue as Guest".
  - App package id (debug):  com.example.nutriscan
    (mobile/android/app/build.gradle.kts -> applicationId)
  - Test entrypoint: lib/main_test.dart (calls enableFlutterDriverExtension()
    then boots the real, unmodified widget tree from main.dart)
  - Build command:
      flutter build apk --debug -t lib/main_test.dart
  - Local persistence: Drift (SQLite) via mobile/lib/core/database — scan
    history and user profile are stored ON-DEVICE. There is no backend
    call in the mobile app's critical path today (OCR is on-device via
    google_mlkit_text_recognition; the /scanner "web mode" TODO branch is
    web-build only and out of scope for Android E2E).

IMPORTANT: this repo has no android-e2e workflow, no mobile_test/ folder,
and no ValueKeys on the Flutter widget tree before this suite was added.
Both were added alongside this suite (see mobile-tests/README.md).
"""

import os


def _bool_env(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# ── App under test ──────────────────────────────────────────────────────
APP_PACKAGE = os.environ.get("APP_PACKAGE", "com.example.nutriscan")
APP_ACTIVITY = os.environ.get("APP_ACTIVITY", ".MainActivity")
APK_PATH = os.environ.get("APK_PATH", "")  # resolved to absolute by CI, see scripts/ci_run_shard.sh

# ── Appium server ────────────────────────────────────────────────────────
APPIUM_SERVER_URL = os.environ.get("APPIUM_SERVER_URL", "http://127.0.0.1:4723")
APPIUM_COMMAND_TIMEOUT = int(os.environ.get("APPIUM_COMMAND_TIMEOUT", "12"))  # seconds — see README "gotchas"
NEW_SESSION_TIMEOUT = int(os.environ.get("NEW_SESSION_TIMEOUT", "90"))

AUTOMATION_NAME = "Flutter"
PLATFORM_NAME = "Android"
DEVICE_NAME = os.environ.get("DEVICE_NAME", "emulator-5554")

# ── Waits ────────────────────────────────────────────────────────────────
DEFAULT_TIMEOUT = int(os.environ.get("APPIUM_TIMEOUT", "30"))
SHORT_TIMEOUT = int(os.environ.get("APPIUM_SHORT_TIMEOUT", "20"))

# ── Backend (unused by the current mobile app — kept for forward-compat if
#    a backend integration is added later; see config note above) ────────
BACKEND_URL = os.environ.get("BACKEND_URL", "http://10.0.2.2:8001")

# ── Reporting ────────────────────────────────────────────────────────────
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
LOGS_DIR = os.path.join(REPORTS_DIR, "logs")

# ── Pass-rate gate — one number, used in both display and enforcement ────
PASS_RATE_THRESHOLD = float(os.environ.get("PASS_RATE_THRESHOLD", "95"))

# ── Test data ────────────────────────────────────────────────────────────
ALLERGIES = [
    "Peanuts", "Tree Nuts", "Dairy", "Eggs", "Soy",
    "Wheat / Gluten", "Fish", "Shellfish", "Sesame", "Mustard", "Sulfites", "Corn",
]
CONDITIONS = [
    "Diabetes", "Hypertension", "High Cholesterol", "Celiac Disease",
    "IBS", "Kidney Disease", "PCOS", "Heart Disease",
]
GOALS = [
    "Vegan", "Vegetarian", "Keto", "Low Sodium", "Low Sugar",
    "High Protein", "Whole Foods", "Halal", "Kosher", "Gluten-Free",
]

# Visible-text markers per screen — appium-flutter-driver has no
# page_source and no URL/route concept (returns 405 permanently), so
# "which screen am I on" is answered by matching a unique visible string.
ROUTE_TEXT_MARKERS = {
    "auth": "NutriScan AI",
    "home": "Eat with\nintelligence.",
    "history": "Scan history",
    "profile": "Health Profile",
    "scanner": "NutriScan",
    "results": "Scan Results",
}
