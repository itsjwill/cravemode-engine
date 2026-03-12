"""
CraveMode Client Manager — Quota tracking, plan tiers, usage monitoring.

Each client has:
- A tier (Starter/Growth/Premium)
- Monthly quotas (images + videos)
- Usage counters that reset monthly
- Restaurant metadata (name, cuisine, dishes)
"""

import json
from datetime import datetime
from pathlib import Path


# Client data file
DATA_DIR = Path(__file__).parent.parent / "data"
CLIENTS_FILE = DATA_DIR / "clients.json"


def _ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_clients():
    """Load all clients from JSON file."""
    _ensure_data_dir()
    if CLIENTS_FILE.exists():
        with open(CLIENTS_FILE) as f:
            return json.load(f)
    return {}


def _save_clients(clients):
    """Save all clients to JSON file."""
    _ensure_data_dir()
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, indent=2, default=str)


# --- Tier Definitions (mirrors food_prompts.py) ---

TIERS = {
    "starter": {
        "name": "Starter",
        "price": 297,
        "images_per_month": 15,
        "videos_per_month": 3,
        "products": ["hero_shot", "menu_strip", "delivery_listing"],
    },
    "growth": {
        "name": "Growth",
        "price": 597,
        "images_per_month": 30,
        "videos_per_month": 8,
        "products": ["hero_shot", "menu_strip", "sizzle_reel", "delivery_listing"],
    },
    "premium": {
        "name": "Premium",
        "price": 997,
        "images_per_month": 60,
        "videos_per_month": 15,
        "products": ["hero_shot", "menu_strip", "sizzle_reel", "seasonal_promo", "delivery_listing"],
    },
}


# --- Client CRUD ---

def create_client(client_id, name, cuisine="default", tier="starter", dishes=None):
    """
    Register a new restaurant client.

    Args:
        client_id: Unique identifier (slug, e.g., "marios-pizza")
        name: Restaurant display name
        cuisine: Cuisine type from food_prompts.CUISINE_STYLES
        tier: Plan tier key
        dishes: List of dish dicts [{"name": "...", "category": "entree"}]

    Returns:
        dict: The created client record
    """
    clients = _load_clients()

    if client_id in clients:
        raise ValueError(f"Client '{client_id}' already exists")

    now = datetime.now().isoformat()
    client = {
        "id": client_id,
        "name": name,
        "cuisine": cuisine,
        "tier": tier,
        "dishes": dishes or [],
        "created_at": now,
        "status": "active",
        "usage": {
            "month": datetime.now().strftime("%Y-%m"),
            "images_generated": 0,
            "videos_generated": 0,
            "images_approved": 0,
            "videos_approved": 0,
        },
        "history": [],
    }

    clients[client_id] = client
    _save_clients(clients)
    return client


def get_client(client_id):
    """Get a client by ID. Returns None if not found."""
    clients = _load_clients()
    return clients.get(client_id)


def list_clients(status="active"):
    """List all clients, optionally filtered by status."""
    clients = _load_clients()
    if status:
        return {k: v for k, v in clients.items() if v.get("status") == status}
    return clients


def update_client(client_id, **kwargs):
    """Update client fields. Supports: name, cuisine, tier, dishes, status."""
    clients = _load_clients()
    if client_id not in clients:
        raise ValueError(f"Client '{client_id}' not found")

    allowed = {"name", "cuisine", "tier", "dishes", "status", "ayrshare_profile_key"}
    for key, value in kwargs.items():
        if key in allowed:
            clients[client_id][key] = value

    _save_clients(clients)
    return clients[client_id]


# --- Usage Tracking ---

def _reset_usage_if_new_month(client):
    """Reset usage counters if we're in a new month."""
    current_month = datetime.now().strftime("%Y-%m")
    if client["usage"]["month"] != current_month:
        # Archive old usage
        client["history"].append(dict(client["usage"]))
        # Reset
        client["usage"] = {
            "month": current_month,
            "images_generated": 0,
            "videos_generated": 0,
            "images_approved": 0,
            "videos_approved": 0,
        }
    return client


def check_quota(client_id, content_type="image", count=1):
    """
    Check if client has quota for generation.

    Args:
        client_id: Client identifier
        content_type: "image" or "video"
        count: Number of items to generate

    Returns:
        dict: {"allowed": bool, "remaining": int, "limit": int, "used": int}
    """
    client = get_client(client_id)
    if not client:
        return {"allowed": False, "remaining": 0, "limit": 0, "used": 0, "error": "Client not found"}

    client = _reset_usage_if_new_month(client)
    tier = TIERS.get(client["tier"], TIERS["starter"])

    if content_type == "image":
        limit = tier["images_per_month"]
        used = client["usage"]["images_generated"]
    else:
        limit = tier["videos_per_month"]
        used = client["usage"]["videos_generated"]

    remaining = max(0, limit - used)
    allowed = remaining >= count

    return {
        "allowed": allowed,
        "remaining": remaining,
        "limit": limit,
        "used": used,
        "tier": client["tier"],
    }


def record_usage(client_id, content_type="image", count=1, approved=False):
    """
    Record usage for a client after generation.

    Args:
        client_id: Client identifier
        content_type: "image" or "video"
        count: Number generated
        approved: Whether the content was approved
    """
    clients = _load_clients()
    if client_id not in clients:
        return

    client = _reset_usage_if_new_month(clients[client_id])

    if content_type == "image":
        client["usage"]["images_generated"] += count
        if approved:
            client["usage"]["images_approved"] += count
    else:
        client["usage"]["videos_generated"] += count
        if approved:
            client["usage"]["videos_approved"] += count

    clients[client_id] = client
    _save_clients(clients)


# --- Reporting ---

def get_usage_summary(client_id):
    """
    Get a formatted usage summary for a client.

    Returns:
        dict with usage stats, remaining quota, cost estimates
    """
    client = get_client(client_id)
    if not client:
        return None

    client = _reset_usage_if_new_month(client)
    tier = TIERS.get(client["tier"], TIERS["starter"])
    usage = client["usage"]

    img_remaining = max(0, tier["images_per_month"] - usage["images_generated"])
    vid_remaining = max(0, tier["videos_per_month"] - usage["videos_generated"])

    # Cost estimate (production cost to us)
    img_cost = usage["images_generated"] * 0.13  # Nano Banana Pro via Google
    vid_cost = usage["videos_generated"] * 0.50  # Veo 3.1
    total_cost = img_cost + vid_cost

    return {
        "client": client["name"],
        "tier": tier["name"],
        "price": tier["price"],
        "month": usage["month"],
        "images": {
            "generated": usage["images_generated"],
            "approved": usage["images_approved"],
            "remaining": img_remaining,
            "limit": tier["images_per_month"],
        },
        "videos": {
            "generated": usage["videos_generated"],
            "approved": usage["videos_approved"],
            "remaining": vid_remaining,
            "limit": tier["videos_per_month"],
        },
        "production_cost": round(total_cost, 2),
        "margin": round(tier["price"] - total_cost, 2),
        "margin_pct": round((1 - total_cost / tier["price"]) * 100, 1) if tier["price"] > 0 else 0,
    }


def get_all_usage_report():
    """Get usage summary for all active clients."""
    clients = list_clients(status="active")
    report = []
    total_revenue = 0
    total_cost = 0

    for client_id in clients:
        summary = get_usage_summary(client_id)
        if summary:
            report.append(summary)
            total_revenue += summary["price"]
            total_cost += summary["production_cost"]

    return {
        "clients": report,
        "total_clients": len(report),
        "total_mrr": total_revenue,
        "total_production_cost": round(total_cost, 2),
        "total_margin": round(total_revenue - total_cost, 2),
        "average_margin_pct": round((1 - total_cost / total_revenue) * 100, 1) if total_revenue > 0 else 0,
    }
