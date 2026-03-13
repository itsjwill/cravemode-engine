"""
Configuration loader for Creative Content Engine.
Loads API keys from .claude/.env and provides centralized constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .claude/.env
PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / ".claude" / ".env"
load_dotenv(ENV_PATH)

# --- API Keys ---
KIE_API_KEY = os.getenv("KIE_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- WaveSpeed AI ---
WAVESPEED_API_KEY = os.getenv("WAVESPEED_API_KEY")
WAVESPEED_API_URL = "https://api.wavespeed.ai/api/v3"

# --- Kie AI Endpoints ---
KIE_FILE_UPLOAD_URL = "https://kieai.redpandaai.co/api/file-stream-upload"
KIE_CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"

# --- Airtable ---
AIRTABLE_API_URL = "https://api.airtable.com/v0"
AIRTABLE_TABLE_NAME = "Content"

# --- Cost Constants (legacy — use get_cost() for multi-provider) ---
IMAGE_COST = 0.09   # per Nano Banana Pro image 1K-2K (Kie AI, 18 credits)
VIDEO_COST = 1.00   # per Kling 3.0 Pro 5s video with audio (Kie AI, 200 credits)
WAVESPEED_VIDEO_COST = 0.30  # per Kling/Sora video via WaveSpeed (approximate)

# --- Kie AI Credit Pricing (as of March 2026) ---
# 1 credit = $0.005 at $50/10K tier
# Packages: $5/1K, $50/10K, $500/105K (5% off), $1250/275K (10% off)
#
# Image: Nano Banana Pro 1K-2K = 18 credits ($0.09), 4K = 24 credits ($0.12)
# Video: Kling 3.0 — credits PER SECOND:
#   Standard no audio: 20/s, Standard+audio: 30/s, Pro no audio: 27/s, Pro+audio: 40/s
#   5s Pro+audio = 200 credits ($1.00), 10s Pro+audio = 400 credits ($2.00)
# Video: Sora 2 Standard 10s = 30 credits ($0.15), 15s = 35 credits ($0.175)
# Video: Sora 2 Pro 720p 10s = 150 credits ($0.75), 1080p 10s = 330 credits ($1.65)
# Video: Veo 3.1 Fast 8s = 80 credits ($0.40), Quality 8s = 400 credits ($2.00)

# --- Per-model per-provider costs (March 2026) ---
COSTS = {
    # --- Image models --- Kie AI
    ("z-image", "kie"): 0.004,          # 0.8 credits — cheapest, good for batch previews
    ("nano-banana", "kie"): 0.02,       # 4 credits
    ("nano-banana-2", "kie"): 0.06,     # 12 credits (2K) — newer, cheaper than Pro
    ("nano-banana-pro", "kie"): 0.09,   # 18 credits (1K-2K)
    ("nano-banana-pro-4k", "kie"): 0.12, # 24 credits (4K)
    ("flux-2-pro", "kie"): 0.025,       # 5 credits (1K)
    ("seedream-4.0", "kie"): 0.025,     # 5 credits (any res up to 4K)
    ("seedream-4.5", "kie"): 0.032,     # 6.5 credits
    ("imagen-4-fast", "kie"): 0.02,     # 4 credits
    ("imagen-4", "kie"): 0.04,          # 8 credits
    ("imagen-4-ultra", "kie"): 0.06,    # 12 credits
    ("gpt-4o-image", "kie"): 0.03,      # ~6 credits (1 image)
    ("ideogram-v3", "kie"): 0.035,      # 7 credits (balanced)
    # --- Image models --- Google
    ("nano-banana", "google"): 0.04,
    ("nano-banana-pro", "google"): 0.13,
    # --- Image models --- WaveSpeed
    ("gpt-image-1.5", "wavespeed"): 0.07,
    # --- Video models --- Kie AI
    # Kling 2.1 (BUDGET — use for testing)
    ("kling-2.1", "kie"): 0.125,        # 25 credits (5s Standard 720p)
    ("kling-2.1-pro", "kie"): 0.25,     # 50 credits (5s Pro 1080p)
    ("kling-2.1-master", "kie"): 0.80,  # 160 credits (5s Master 1080p)
    # Kling 3.0 (PREMIUM — use for final/polished)
    ("kling-3.0", "kie"): 1.00,         # 200 credits (5s Pro+audio)
    ("kling-3.0-std", "kie"): 0.50,     # 100 credits (5s Std no audio)
    ("kling-3.0-std-audio", "kie"): 0.75, # 150 credits (5s Std+audio)
    ("kling-3.0-noaudio", "kie"): 0.675, # 135 credits (5s Pro no audio)
    # Sora 2
    ("sora-2", "kie"): 0.15,            # 30 credits (10s Standard)
    ("sora-2-pro", "kie"): 0.75,        # 150 credits (10s 720p)
    ("sora-2-pro-hd", "kie"): 1.65,     # 330 credits (10s 1080p)
    # Wan 2.5
    ("wan-2.5", "kie"): 0.30,           # 60 credits (5s 720p, native audio)
    ("wan-2.5-hd", "kie"): 0.50,        # 100 credits (5s 1080p)
    # Hailuo 2.3
    ("hailuo-2.3", "kie"): 0.15,        # 30 credits (6s 768p Standard)
    ("hailuo-2.3-pro", "kie"): 0.22,    # 45 credits (6s 768p Pro)
    # Veo 3.1
    ("veo-3.1", "google"): 0.50,
    ("veo-3.1-fast", "kie"): 0.40,      # 80 credits (8s)
    ("veo-3.1-quality", "kie"): 2.00,   # 400 credits (8s)
    # --- Video models --- WaveSpeed
    ("kling-3.0", "wavespeed"): 0.30,
    ("sora-2", "wavespeed"): 0.30,
    ("sora-2-pro", "wavespeed"): 0.30,
    # --- Audio models --- Kie AI
    ("suno", "kie"): 0.06,              # 12 credits (generate/extend music)
    ("elevenlabs-tts", "kie"): 0.03,    # 6 credits per 1K chars
    ("elevenlabs-sfx", "kie"): 0.001,   # 0.24 credits/sec (sound effects)
}

# --- Default Models ---
DEFAULT_IMAGE_MODEL = "nano-banana-pro"
DEFAULT_VIDEO_MODEL = "veo-3.1"

# --- Directories ---
INPUTS_DIR = PROJECT_ROOT / "references" / "inputs"

# --- Video Models (Kie AI) ---
# Both models support image-to-video (using image_urls for the start frame).
# Kling 3.0: image/text-to-video, std/pro quality, 3-15s duration, multi-shot support
# Sora 2 Pro: image-to-video, portrait/landscape, 10s/15s, high quality
VIDEO_MODELS = {
    "kling-3.0": "kling-3.0/video",
    "sora-2-pro": "sora-2-pro-image-to-video",
    "veo-3.1": "veo-3.1-generate-preview",
}

# --- Video Models (WaveSpeed AI) ---
# Same models available through WaveSpeed's infrastructure.
# WaveSpeed uses model ID in the URL path (not request body).
WAVESPEED_VIDEO_MODELS = {
    "kling-3.0": "kwaivgi/kling-v3.0-pro/image-to-video",
    "kling-3.0-std": "kwaivgi/kling-v3.0-std/image-to-video",
    "sora-2": "openai/sora-2/image-to-video",
    "sora-2-pro": "openai/sora-2/image-to-video-pro",
}


def get_cost(model, provider=None):
    """
    Get the cost per generation for a model+provider combination.

    Args:
        model: Model name (e.g., "nano-banana-pro", "veo-3.1")
        provider: Provider name (e.g., "google", "kie"). If None, uses default.

    Returns:
        float: Cost per unit
    """
    if provider is None:
        # Import here to avoid circular imports
        from .providers import IMAGE_PROVIDERS, VIDEO_PROVIDERS
        if model in IMAGE_PROVIDERS:
            provider = IMAGE_PROVIDERS[model]["default"]
        elif model in VIDEO_PROVIDERS:
            provider = VIDEO_PROVIDERS[model]["default"]
        else:
            return 0.0
    return COSTS.get((model, provider), 0.0)


def check_credentials():
    """Verify required API keys are set. Returns list of missing keys."""
    required = {
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    missing = [name for name, value in required.items() if not value]

    # At least one generation provider must be configured
    if not KIE_API_KEY and not GOOGLE_API_KEY:
        missing.append("KIE_API_KEY or GOOGLE_API_KEY (at least one required)")

    if missing:
        print("Missing API keys:")
        for key in missing:
            print(f"  - {key}")
        print(f"\nAdd them to: {ENV_PATH}")
    return missing


def check_wavespeed_credentials():
    """Verify WaveSpeed API key + Airtable keys are set. Returns list of missing keys."""
    required = {
        "WAVESPEED_API_KEY": WAVESPEED_API_KEY,
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        print("Missing API keys:")
        for key in missing:
            print(f"  - {key}")
        print(f"\nAdd them to: {ENV_PATH}")
    return missing
