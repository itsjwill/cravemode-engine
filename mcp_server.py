"""
CraveMode Social MCP Server — Model Context Protocol server for social media posting.

Exposes tools for AI agents to post generated food content directly to
restaurant social media profiles (Instagram, TikTok, Facebook, Google Business Profile).

Uses Ayrshare as the unified social media API backend.

Run standalone:
    python cravemode/mcp_server.py

Or add to MCP config (~/.mcp.json):
    {
        "mcpServers": {
            "cravemode-social": {
                "command": "python",
                "args": ["/path/to/cravemode/mcp_server.py"]
            }
        }
    }
"""

import sys
import json
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.social_post import (
    post_image, post_video, post_content, post_from_airtable,
    schedule_week, get_connected_platforms, get_connect_url,
    create_profile, get_post_analytics, get_platform_analytics,
    suggest_hashtags, build_food_caption,
    PLATFORMS, PLATFORM_LABELS, PLATFORM_SPECS,
)
from tools.client_manager import get_client, list_clients
from tools.airtable import get_records_by_restaurant


# --- MCP Protocol Implementation (stdio) ---

def _read_message():
    """Read a JSON-RPC message from stdin."""
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line.strip())


def _write_message(msg):
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _success(request_id, result):
    """Build a success response."""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id, code, message):
    """Build an error response."""
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


# --- Tool Definitions ---

TOOLS = [
    {
        "name": "post_food_image",
        "description": (
            "Post a food image to restaurant social media profiles. "
            "Supports Instagram, TikTok, Facebook, and Google Business Profile. "
            "Automatically generates platform-optimized captions with hashtags."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "Restaurant client ID (e.g., 'marios-pizza')",
                },
                "image_url": {
                    "type": "string",
                    "description": "URL of the food image to post",
                },
                "dish_name": {
                    "type": "string",
                    "description": "Name of the dish (e.g., 'Margherita Pizza')",
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": PLATFORMS},
                    "description": "Platforms to post to. Defaults to all connected.",
                },
                "caption": {
                    "type": "string",
                    "description": "Custom caption. Auto-generated if not provided.",
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Custom hashtags. Auto-generated if not provided.",
                },
                "schedule_date": {
                    "type": "string",
                    "description": "ISO 8601 datetime to schedule post. Posts immediately if not set.",
                },
            },
            "required": ["client_id", "image_url", "dish_name"],
        },
    },
    {
        "name": "post_food_video",
        "description": (
            "Post a food video (sizzle reel, transition, etc.) to restaurant social media. "
            "Best for TikTok and Instagram Reels."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "Restaurant client ID",
                },
                "video_url": {
                    "type": "string",
                    "description": "URL of the food video to post",
                },
                "dish_name": {
                    "type": "string",
                    "description": "Name of the dish featured in the video",
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["instagram", "tiktok", "facebook"]},
                    "description": "Platforms to post to. Defaults to Instagram + TikTok.",
                },
                "caption": {
                    "type": "string",
                    "description": "Custom caption. Auto-generated if not provided.",
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Custom hashtags. Auto-generated if not provided.",
                },
                "schedule_date": {
                    "type": "string",
                    "description": "ISO 8601 datetime to schedule post.",
                },
            },
            "required": ["client_id", "video_url", "dish_name"],
        },
    },
    {
        "name": "post_from_record",
        "description": (
            "Post content directly from a CraveMode Airtable record. "
            "Automatically picks the best media (video > image) and generates captions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "Restaurant client ID",
                },
                "record_name": {
                    "type": "string",
                    "description": "Ad Name or restaurant name to find the record",
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": PLATFORMS},
                    "description": "Platforms to post to. Defaults to all connected.",
                },
                "product_type": {
                    "type": "string",
                    "enum": ["hero_shot", "menu_strip", "sizzle_reel", "seasonal_promo", "delivery_listing"],
                    "description": "Product type for caption optimization.",
                },
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "schedule_content_week",
        "description": (
            "Schedule a full week of food content across platforms. "
            "Takes a list of content items and spaces them across 7 days at optimal times."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "Restaurant client ID",
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": PLATFORMS},
                    "description": "Platforms to schedule for",
                },
                "content_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "media_url": {"type": "string"},
                            "caption": {"type": "string"},
                            "hashtags": {"type": "array", "items": {"type": "string"}},
                            "is_video": {"type": "boolean"},
                            "day_offset": {"type": "integer", "description": "Day 0-6"},
                        },
                        "required": ["media_url", "caption"],
                    },
                    "description": "Content items to schedule across the week",
                },
            },
            "required": ["client_id", "platforms", "content_items"],
        },
    },
    {
        "name": "get_social_profiles",
        "description": (
            "Get connected social media profiles for a restaurant client. "
            "Shows which platforms are linked and ready for posting."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "Restaurant client ID",
                },
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "connect_social_profile",
        "description": (
            "Get the URL for a restaurant to connect their social media account. "
            "Returns a link the restaurant owner can click to authorize their account."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "Restaurant client ID",
                },
                "platform": {
                    "type": "string",
                    "enum": PLATFORMS,
                    "description": "Platform to connect",
                },
            },
            "required": ["client_id", "platform"],
        },
    },
    {
        "name": "get_post_stats",
        "description": "Get engagement analytics for a specific post.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "post_id": {"type": "string", "description": "Post ID from Ayrshare"},
            },
            "required": ["client_id", "post_id"],
        },
    },
    {
        "name": "suggest_food_hashtags",
        "description": "Get hashtag suggestions for food content based on a keyword.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Food keyword (e.g., 'pizza', 'sushi', 'bbq')",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of suggestions (default 10)",
                },
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "list_restaurant_clients",
        "description": "List all CraveMode restaurant clients and their social posting status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# --- Tool Handlers ---

def _get_profile_key(client_id):
    """Get Ayrshare profile key for a client."""
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Client '{client_id}' not found")
    profile_key = client.get("ayrshare_profile_key")
    if not profile_key:
        raise ValueError(
            f"Client '{client_id}' has no Ayrshare profile. "
            f"Create one first with create_profile()."
        )
    return profile_key, client


def handle_post_food_image(args):
    client_id = args["client_id"]
    profile_key, client = _get_profile_key(client_id)

    platforms = args.get("platforms")
    if not platforms:
        platforms = get_connected_platforms(profile_key)

    caption = args.get("caption")
    if not caption:
        captions = build_food_caption(
            args["dish_name"],
            client["name"],
            client.get("cuisine"),
        )
        # Use Instagram caption as default
        caption = captions.get("instagram", args["dish_name"])

    result = post_image(
        profile_key=profile_key,
        platforms=platforms,
        image_url=args["image_url"],
        caption=caption,
        hashtags=args.get("hashtags"),
        schedule_date=args.get("schedule_date"),
    )

    return {
        "status": "posted",
        "platforms": platforms,
        "dish": args["dish_name"],
        "restaurant": client["name"],
        "result": result,
    }


def handle_post_food_video(args):
    client_id = args["client_id"]
    profile_key, client = _get_profile_key(client_id)

    platforms = args.get("platforms", ["instagram", "tiktok"])

    caption = args.get("caption")
    if not caption:
        captions = build_food_caption(
            args["dish_name"],
            client["name"],
            client.get("cuisine"),
        )
        caption = captions.get("tiktok", args["dish_name"])

    result = post_video(
        profile_key=profile_key,
        platforms=platforms,
        video_url=args["video_url"],
        caption=caption,
        hashtags=args.get("hashtags"),
        schedule_date=args.get("schedule_date"),
    )

    return {
        "status": "posted",
        "platforms": platforms,
        "dish": args["dish_name"],
        "restaurant": client["name"],
        "result": result,
    }


def handle_post_from_record(args):
    client_id = args["client_id"]
    profile_key, client = _get_profile_key(client_id)

    record_name = args.get("record_name", client["name"])
    records = get_records_by_restaurant(record_name)

    if not records:
        return {"status": "error", "message": f"No records found for '{record_name}'"}

    # Pick the first record with generated content
    target = None
    for r in records:
        fields = r.get("fields", {})
        has_media = (
            fields.get("Generated Video 1") or fields.get("video")
            or fields.get("Generated Image 1") or fields.get("image_1")
        )
        if has_media:
            target = r
            break

    if not target:
        return {"status": "error", "message": "No records with generated content found"}

    result = post_from_airtable(
        profile_key=profile_key,
        record=target,
        platforms=args.get("platforms"),
        product_type=args.get("product_type"),
    )

    return {
        "status": "posted",
        "record": target.get("fields", {}).get("Ad Name", "unknown"),
        "result": result,
    }


def handle_schedule_week(args):
    client_id = args["client_id"]
    profile_key, _ = _get_profile_key(client_id)

    results = schedule_week(
        profile_key=profile_key,
        platforms=args["platforms"],
        content_items=args["content_items"],
    )

    return {
        "status": "scheduled",
        "posts_scheduled": len(results),
        "results": results,
    }


def handle_get_profiles(args):
    client_id = args["client_id"]
    profile_key, client = _get_profile_key(client_id)
    connected = get_connected_platforms(profile_key)

    return {
        "client": client["name"],
        "connected_platforms": [
            {"platform": p, "label": PLATFORM_LABELS.get(p, p)}
            for p in connected
        ],
        "not_connected": [
            {"platform": p, "label": PLATFORM_LABELS.get(p, p)}
            for p in PLATFORMS if p not in connected
        ],
    }


def handle_connect_profile(args):
    client_id = args["client_id"]
    profile_key, client = _get_profile_key(client_id)
    url = get_connect_url(profile_key, args["platform"])

    return {
        "client": client["name"],
        "platform": PLATFORM_LABELS.get(args["platform"], args["platform"]),
        "connect_url": url,
        "instructions": (
            f"Send this link to the restaurant owner. "
            f"They'll authorize their {PLATFORM_LABELS.get(args['platform'])} account "
            f"so CraveMode can post content on their behalf."
        ),
    }


def handle_get_stats(args):
    client_id = args["client_id"]
    profile_key, _ = _get_profile_key(client_id)
    return get_post_analytics(profile_key, args["post_id"])


def handle_suggest_hashtags(args):
    return suggest_hashtags(args["keyword"], args.get("count", 10))


def handle_list_clients(args):
    clients = list_clients(status="active")
    result = []
    for cid, client in clients.items():
        has_social = bool(client.get("ayrshare_profile_key"))
        result.append({
            "id": cid,
            "name": client["name"],
            "cuisine": client.get("cuisine", "default"),
            "tier": client.get("tier", "starter"),
            "social_connected": has_social,
        })
    return {"clients": result, "total": len(result)}


TOOL_HANDLERS = {
    "post_food_image": handle_post_food_image,
    "post_food_video": handle_post_food_video,
    "post_from_record": handle_post_from_record,
    "schedule_content_week": handle_schedule_week,
    "get_social_profiles": handle_get_profiles,
    "connect_social_profile": handle_connect_profile,
    "get_post_stats": handle_get_stats,
    "suggest_food_hashtags": handle_suggest_hashtags,
    "list_restaurant_clients": handle_list_clients,
}


# --- MCP Server Loop ---

def handle_request(msg):
    """Handle a single MCP JSON-RPC request."""
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return _success(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "cravemode-social",
                "version": "1.0.0",
            },
        })

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    elif method == "tools/list":
        return _success(req_id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return _error(req_id, -32601, f"Unknown tool: {tool_name}")

        try:
            result = handler(tool_args)
            return _success(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as e:
            return _success(req_id, {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            })

    else:
        return _error(req_id, -32601, f"Unknown method: {method}")


def main():
    """Run the MCP server via stdio."""
    while True:
        msg = _read_message()
        if msg is None:
            break

        response = handle_request(msg)
        if response is not None:
            _write_message(response)


if __name__ == "__main__":
    main()
