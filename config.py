"""Configuration constants and model definitions for BananaUI."""
import os
from pathlib import Path

# Application Version
APP_VERSION = "v1.0"

# Paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "nanobanana_logo.png"

# Ensure essential directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# NanoBanana Models (Ordered from newest to oldest)
AVAILABLE_MODELS = [
    {
        "display_name": "Nano Banana 2.1 (gemini-nano-banana-2.1)",
        "model_id": "gemini-nano-banana-2.1",
        "description": "Latest flagship image generation and editing model"
    },
    {
        "display_name": "Nano Banana Pro (gemini-3-pro-image)",
        "model_id": "gemini-3-pro-image",
        "description": "Professional high-detail & precision reasoning model"
    },
    {
        "display_name": "Nano Banana 2 (gemini-3.1-flash-image)",
        "model_id": "gemini-3.1-flash-image",
        "description": "Previous-gen high efficiency model"
    },
    {
        "display_name": "Nano Banana 2 Lite (gemini-3.1-flash-lite-image)",
        "model_id": "gemini-3.1-flash-lite-image",
        "description": "Ultra fast lightweight model"
    },
    {
        "display_name": "Nano Banana (gemini-2.5-flash-image)",
        "model_id": "gemini-2.5-flash-image",
        "description": "Original Nano Banana preview model"
    },
]

MODEL_PLACEHOLDER = "[SELECT A MODEL HERE]"

# Combobox options: placeholder as first entry, followed by available models
COMBOBOX_MODEL_OPTIONS = [MODEL_PLACEHOLDER] + [m["display_name"] for m in AVAILABLE_MODELS]

# Default selection when program starts is the placeholder
DEFAULT_MODEL_NAME = MODEL_PLACEHOLDER

def is_proper_model(model_name: str) -> bool:
    """Returns True if a proper model is selected (not empty or the placeholder)."""
    cleaned = model_name.strip()
    return bool(cleaned) and cleaned != MODEL_PLACEHOLDER

def get_model_id_from_display(display_name: str) -> str:
    """Resolve display name or raw model ID to the API model identifier."""
    cleaned = display_name.strip()
    if not is_proper_model(cleaned):
        raise ValueError("Please select a valid NanoBanana model.")
    for m in AVAILABLE_MODELS:
        if m["display_name"] == cleaned:
            return m["model_id"]
        if m["model_id"] == cleaned:
            return m["model_id"]
    # If the user entered a custom model ID directly, use it as is
    return cleaned

MAX_ATTACHMENTS = 8

# API Base URL
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
