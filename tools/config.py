"""
CraveMode Engine Configuration.

Loads API keys from .claude/.env and provides CraveMode-specific constants.
Inherits provider system from parent creative-engine-template.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# CraveMode root
CRAVEMODE_ROOT = Path(__file__).parent.parent

# Load environment — check CraveMode .claude/.env first, then parent
CRAVEMODE_ENV = CRAVEMODE_ROOT / ".claude" / ".env"
PARENT_ENV = CRAVEMODE_ROOT.parent / ".claude" / ".env"

if CRAVEMODE_ENV.exists():
    load_dotenv(CRAVEMODE_ENV)
elif PARENT_ENV.exists():
    load_dotenv(PARENT_ENV)

# --- API Keys ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
KIE_API_KEY = os.getenv("KIE_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
WAVESPEED_API_KEY = os.getenv("WAVESPEED_API_KEY")
AYRSHARE_API_KEY = os.getenv("AYRSHARE_API_KEY")

# --- Airtable ---
AIRTABLE_API_URL = "https://api.airtable.com/v0"
AIRTABLE_TABLE_NAME = "Leads"  # Existing restaurant photography table

# --- Kie AI API ---
KIE_CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"

# --- CraveMode Defaults ---
DEFAULT_IMAGE_MODEL = "nano-banana-pro"
DEFAULT_VIDEO_MODEL = "kling-3.0"
DEFAULT_ASPECT_RATIO_HERO = "4:5"
DEFAULT_ASPECT_RATIO_MENU = "16:9"
DEFAULT_ASPECT_RATIO_DELIVERY = "1:1"
DEFAULT_ASPECT_RATIO_SEASONAL = "1:1"
DEFAULT_ASPECT_RATIO_SIZZLE = "9:16"

# --- Quality Gate Thresholds ---
MIN_INPUT_RESOLUTION = 1080
MIN_QUALITY_SCORE = 7.0

# --- Cost Constants (per unit) ---
COSTS = {
    ("nano-banana", "google"): 0.04,
    ("nano-banana-pro", "google"): 0.13,
    ("nano-banana-pro", "kie"): 0.09,
    ("veo-3.1", "google"): 0.50,
    ("kling-3.0", "kie"): 0.30,
    ("kling-3.0", "wavespeed"): 0.30,
    ("sora-2-pro", "kie"): 0.30,
    ("sora-2-pro", "wavespeed"): 0.30,
}

# --- Directories ---
INPUTS_DIR = CRAVEMODE_ROOT / "references" / "inputs"
DATA_DIR = CRAVEMODE_ROOT / "data"

# --- Wire up parent providers ---
# Add parent tools to path so we can reuse providers
PARENT_TOOLS = CRAVEMODE_ROOT.parent / "tools"
if str(PARENT_TOOLS) not in sys.path:
    sys.path.insert(0, str(CRAVEMODE_ROOT.parent))


def get_cost(model, provider=None):
    """Get cost per generation for a model+provider."""
    if provider is None:
        if model in ("nano-banana", "nano-banana-pro"):
            provider = "google"
        elif model == "veo-3.1":
            provider = "google"
        else:
            provider = "kie"
    return COSTS.get((model, provider), 0.0)


def check_credentials():
    """Verify required API keys are set."""
    required = {
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    missing = [name for name, value in required.items() if not value]

    if not GOOGLE_API_KEY and not KIE_API_KEY:
        missing.append("GOOGLE_API_KEY or KIE_API_KEY (at least one required)")

    if missing:
        print("Missing API keys:")
        for key in missing:
            print(f"  - {key}")
        env_path = CRAVEMODE_ENV if CRAVEMODE_ENV.exists() else PARENT_ENV
        print(f"\nAdd them to: {env_path}")
    return missing
