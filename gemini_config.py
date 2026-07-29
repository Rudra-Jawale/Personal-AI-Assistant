"""Shared Gemini configuration for every AI feature in the project."""

import os

from dotenv import load_dotenv


DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

# These names no longer accept generate-content requests.  Keeping the mapping
# lets existing .env files continue to work after upgrading the application.
RETIRED_MODELS = {
    "gemini-pro",
    "models/gemini-pro",
    "gemini-2.5-flash",
    "models/gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025",
    "models/gemini-2.5-flash-preview-09-2025",
}


def get_gemini_settings():
    """Return the configured Gemini API key and a supported text model name."""
    # Preserve environment variables supplied by the shell, deployment host,
    # or tests; use .env only when a setting is not already provided.
    load_dotenv()
    api_key = os.getenv("GOOGLE_GEMINI_KEY", "").strip()
    model = (
        os.getenv("GEMINI_MODEL")
        or os.getenv("Gemini_MODEL")  # Backwards-compatible project setting.
        or DEFAULT_GEMINI_MODEL
    ).strip()

    # The current google-genai SDK accepts names without the API's `models/`
    # prefix. Normalize old settings so calls are consistent everywhere.
    if model.startswith("models/"):
        model = model.removeprefix("models/")
    if model in RETIRED_MODELS:
        model = DEFAULT_GEMINI_MODEL

    return api_key, model
