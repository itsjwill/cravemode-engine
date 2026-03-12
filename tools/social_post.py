"""
CraveMode Social Media Posting — Ayrshare-powered multi-platform posting.

Wraps the Ayrshare unified API to let restaurants post generated content
directly to Instagram, TikTok, Facebook, and Google Business Profile.

Pipeline: Generate -> Quality Gate -> Post

Each restaurant client connects their social profiles via Ayrshare.
We store their Ayrshare profile key in the client record.

API Reference: https://docs.ayrshare.com
"""

import requests
from datetime import datetime, timezone
from .config import AYRSHARE_API_KEY, AIRTABLE_API_KEY

AYRSHARE_BASE = "https://api.ayrshare.com/api"

# Supported platforms for restaurants
PLATFORMS = ["instagram", "tiktok", "facebook", "gmb"]

PLATFORM_LABELS = {
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "facebook": "Facebook",
    "gmb": "Google Business Profile",
}

# Optimal posting specs per platform
PLATFORM_SPECS = {
    "instagram": {
        "image_ratio": "4:5",
        "video_ratio": "9:16",
        "max_hashtags": 30,
        "max_caption": 2200,
        "best_times_utc": ["17:00", "19:00", "12:00"],
    },
    "tiktok": {
        "image_ratio": "9:16",
        "video_ratio": "9:16",
        "max_hashtags": 5,
        "max_caption": 2200,
        "best_times_utc": ["19:00", "12:00", "15:00"],
    },
    "facebook": {
        "image_ratio": "1:1",
        "video_ratio": "16:9",
        "max_hashtags": 5,
        "max_caption": 63206,
        "best_times_utc": ["18:00", "15:00", "12:00"],
    },
    "gmb": {
        "image_ratio": "4:3",
        "video_ratio": None,  # GMB doesn't support video posts well
        "max_hashtags": 0,
        "max_caption": 1500,
        "best_times_utc": ["12:00", "17:00"],
    },
}


def _headers(profile_key=None):
    """Build Ayrshare API headers. profile_key for client-specific posting."""
    h = {
        "Authorization": f"Bearer {AYRSHARE_API_KEY}",
        "Content-Type": "application/json",
    }
    if profile_key:
        h["Profile-Key"] = profile_key
    return h


# --- Profile Management ---

def create_profile(client_name, client_id):
    """
    Create an Ayrshare profile for a restaurant client.
    Returns profile key to store in client record.
    """
    resp = requests.post(
        f"{AYRSHARE_BASE}/profiles/profile",
        headers=_headers(),
        json={"title": f"{client_name} ({client_id})"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "profile_key": data.get("profileKey"),
        "ref_id": data.get("refId"),
        "title": data.get("title"),
    }


def get_profile(profile_key):
    """Get profile details and connected platforms."""
    resp = requests.get(
        f"{AYRSHARE_BASE}/profiles/profile",
        headers=_headers(profile_key),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_connected_platforms(profile_key):
    """Get list of platforms connected for a profile."""
    profile = get_profile(profile_key)
    connected = []
    for platform in PLATFORMS:
        if profile.get(platform, {}).get("connected"):
            connected.append(platform)
    return connected


def get_connect_url(profile_key, platform):
    """Get the URL for a client to connect their social account."""
    resp = requests.get(
        f"{AYRSHARE_BASE}/profiles/generateJWT",
        headers=_headers(profile_key),
        params={"domain": "cravemode"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("url")


# --- Posting ---

def post_content(profile_key, platforms, media_urls, caption,
                 hashtags=None, schedule_date=None, is_video=False):
    """
    Post content to one or more platforms.

    Args:
        profile_key: Ayrshare profile key for the restaurant
        platforms: List of platform names ["instagram", "tiktok", ...]
        media_urls: List of media URLs (images or videos)
        caption: Post caption/text
        hashtags: Optional list of hashtags (auto-formatted)
        schedule_date: ISO 8601 datetime string for scheduled posting
        is_video: True if posting video content

    Returns:
        dict: Ayrshare response with post IDs per platform
    """
    # Validate platforms
    valid = [p for p in platforms if p in PLATFORMS]
    if not valid:
        raise ValueError(f"No valid platforms. Choose from: {PLATFORMS}")

    # Build caption with hashtags
    full_caption = caption
    if hashtags:
        tag_str = " ".join(f"#{t.lstrip('#')}" for t in hashtags)
        full_caption = f"{caption}\n\n{tag_str}"

    payload = {
        "post": full_caption,
        "platforms": valid,
    }

    if media_urls:
        if is_video:
            payload["videoUrl"] = media_urls[0]
        else:
            payload["mediaUrls"] = media_urls

    if schedule_date:
        payload["scheduleDate"] = schedule_date

    resp = requests.post(
        f"{AYRSHARE_BASE}/post",
        headers=_headers(profile_key),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def post_image(profile_key, platforms, image_url, caption,
               hashtags=None, schedule_date=None):
    """Convenience: post a single image."""
    return post_content(
        profile_key, platforms, [image_url], caption,
        hashtags=hashtags, schedule_date=schedule_date, is_video=False,
    )


def post_video(profile_key, platforms, video_url, caption,
               hashtags=None, schedule_date=None):
    """Convenience: post a single video."""
    return post_content(
        profile_key, platforms, [video_url], caption,
        hashtags=hashtags, schedule_date=schedule_date, is_video=True,
    )


# --- Scheduling ---

def get_best_time(platform, timezone_offset=0):
    """Get the next best posting time for a platform."""
    specs = PLATFORM_SPECS.get(platform, {})
    times = specs.get("best_times_utc", ["12:00"])
    # Return the first best time (simplified — in production, check against current time)
    return times[0]


def schedule_week(profile_key, platforms, content_items, start_date=None):
    """
    Schedule a week of content across platforms.

    Args:
        profile_key: Restaurant's Ayrshare profile key
        platforms: Platforms to post to
        content_items: List of dicts with keys:
            - media_url: URL of image/video
            - caption: Post caption
            - hashtags: List of hashtags
            - is_video: bool
            - day_offset: Days from start_date (0-6)

    Returns:
        list: Results for each scheduled post
    """
    from datetime import timedelta

    if start_date is None:
        start_date = datetime.now(timezone.utc).replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        # Start from next day
        start_date += timedelta(days=1)

    results = []
    for item in content_items:
        day = item.get("day_offset", 0)
        post_date = start_date + timedelta(days=day)
        schedule_iso = post_date.isoformat()

        media_urls = [item["media_url"]] if item.get("media_url") else []
        result = post_content(
            profile_key=profile_key,
            platforms=platforms,
            media_urls=media_urls,
            caption=item.get("caption", ""),
            hashtags=item.get("hashtags"),
            schedule_date=schedule_iso,
            is_video=item.get("is_video", False),
        )
        results.append({
            "scheduled_for": schedule_iso,
            "platforms": platforms,
            "result": result,
        })

    return results


# --- Analytics ---

def get_post_analytics(profile_key, post_id):
    """Get analytics for a specific post."""
    resp = requests.get(
        f"{AYRSHARE_BASE}/analytics/post",
        headers=_headers(profile_key),
        params={"id": post_id},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_platform_analytics(profile_key, platform):
    """Get overall analytics for a platform."""
    resp = requests.get(
        f"{AYRSHARE_BASE}/analytics/social",
        headers=_headers(profile_key),
        params={"platforms": [platform]},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# --- Hashtag Suggestions ---

def suggest_hashtags(keyword, num=10):
    """Get hashtag suggestions for food content."""
    resp = requests.get(
        f"{AYRSHARE_BASE}/hashtags/auto",
        headers=_headers(),
        params={"keyword": keyword, "num": num},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# --- Caption Generation ---

def build_food_caption(dish_name, restaurant_name, cuisine=None, product_type=None):
    """
    Build a social media caption for food content.

    Returns dict with platform-optimized captions.
    """
    base = f"Fresh from {restaurant_name}"
    if cuisine:
        cuisine_emojis = {
            "italian": "🇮🇹", "mexican": "🌮", "asian": "🥢",
            "american": "🍔", "seafood": "🦞", "bbq": "🔥",
            "bakery": "🥐", "default": "🍽️",
        }
        emoji = cuisine_emojis.get(cuisine, "🍽️")
        base = f"{emoji} Fresh from {restaurant_name}"

    captions = {
        "instagram": (
            f"{base}\n\n"
            f"📸 {dish_name}\n\n"
            f"Ready to make your taste buds dance? Come try it for yourself.\n\n"
            f"📍 Tag someone who needs to see this!\n"
            f".\n.\n."
        ),
        "tiktok": (
            f"{dish_name} from {restaurant_name} hits different 🤤\n\n"
            f"Would you try this?"
        ),
        "facebook": (
            f"Have you tried our {dish_name}? 😍\n\n"
            f"Stop by {restaurant_name} and see what everyone's talking about.\n\n"
            f"📞 Order now or visit us today!"
        ),
        "gmb": (
            f"Try our {dish_name}! "
            f"Visit {restaurant_name} for an unforgettable dining experience."
        ),
    }

    return captions


# --- Convenience for CraveMode Pipeline ---

def post_from_airtable(profile_key, record, platforms=None, product_type=None):
    """
    Post content directly from a CraveMode Airtable record.

    Args:
        profile_key: Restaurant's Ayrshare profile key
        record: Airtable record dict
        platforms: Platforms to post to (defaults to all connected)
        product_type: hero_shot, menu_strip, sizzle_reel, etc.

    Returns:
        dict: Posting results
    """
    fields = record.get("fields", {})
    ad_name = fields.get("Ad Name", fields.get("Name", ""))
    restaurant = fields.get("Product", fields.get("Name", ""))

    # Get media URL
    is_video = False
    media_url = None

    # Check for video first
    for vid_field in ("Generated Video 1", "video"):
        vid = fields.get(vid_field, [])
        if vid:
            media_url = vid[0].get("url")
            is_video = True
            break

    # Fall back to image
    if not media_url:
        for img_field in ("Generated Image 1", "image_1"):
            img = fields.get(img_field, [])
            if img:
                media_url = img[0].get("url")
                break

    if not media_url:
        raise ValueError(f"No generated media found in record '{ad_name}'")

    # Auto-detect platforms if not specified
    if not platforms:
        platforms = get_connected_platforms(profile_key)
        if not platforms:
            raise ValueError("No social platforms connected. Have the client connect via Ayrshare.")

    # Build caption
    cuisine = fields.get("Category", fields.get("cuisine", "default"))
    captions = build_food_caption(ad_name, restaurant, cuisine, product_type)

    # Post to each platform with optimized caption
    results = {}
    for platform in platforms:
        caption = captions.get(platform, captions.get("instagram", ad_name))
        hashtags = _default_hashtags(cuisine, product_type)

        try:
            result = post_content(
                profile_key=profile_key,
                platforms=[platform],
                media_urls=[media_url],
                caption=caption,
                hashtags=hashtags,
                is_video=is_video,
            )
            results[platform] = {"status": "posted", "result": result}
        except Exception as e:
            results[platform] = {"status": "error", "error": str(e)}

    return results


def _default_hashtags(cuisine=None, product_type=None):
    """Generate default hashtags for food content."""
    tags = ["foodie", "foodphotography", "restaurant", "yummy", "delicious"]

    cuisine_tags = {
        "italian": ["italianfood", "pasta", "pizzatime"],
        "mexican": ["mexicanfood", "tacos", "comidamexicana"],
        "asian": ["asianfood", "sushi", "ramen"],
        "american": ["americanfood", "burger", "bbq"],
        "seafood": ["seafood", "freshcatch", "oceantoplate"],
        "bbq": ["bbq", "smoked", "grillmaster"],
        "bakery": ["bakery", "freshbaked", "pastry"],
    }
    if cuisine and cuisine in cuisine_tags:
        tags.extend(cuisine_tags[cuisine])

    product_tags = {
        "hero_shot": ["foodporn", "instafood"],
        "sizzle_reel": ["foodvideo", "asmrfood", "satisfying"],
        "delivery_listing": ["fooddelivery", "ordernow", "doordash"],
        "seasonal_promo": ["seasonal", "limitedtime"],
        "menu_strip": ["menu", "eatlocal"],
    }
    if product_type and product_type in product_tags:
        tags.extend(product_tags[product_type])

    return tags
