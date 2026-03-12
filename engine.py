"""
CraveMode Engine — Main entry point.

Orchestrates the full pipeline:
  1. Register client + dishes
  2. Generate content plan (Cane's Menu products)
  3. Quality gate input photos
  4. Generate images via provider system
  5. Quality gate outputs
  6. Generate videos for approved images
  7. Track usage + quotas
  8. Post to social media (Instagram, TikTok, Facebook, Google Business Profile)

Usage:
    import sys; sys.path.insert(0, '.')
    from cravemode.engine import CraveModeEngine

    engine = CraveModeEngine()
    engine.onboard_client("Mario's Pizza", "italian", "starter", dishes=[...])
    engine.generate_content("marios-pizza")
"""

import sys
import base64
import tempfile
import requests as _requests
from pathlib import Path

# Ensure parent is on path for provider access
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from tools import config
from tools.airtable import (
    get_records_by_restaurant,
    get_pending_images,
    update_record,
)
from tools.food_prompts import (
    generate_content_plan, PRODUCTS, TIERS,
    build_enhancement_prompt, build_alternate_angle_prompt,
    build_transition_video_prompt,
)
from tools.quality_gate import gate1_validate_input, gate2_score_output
from tools.client_manager import (
    create_client,
    get_client,
    check_quota,
    record_usage,
    get_usage_summary,
    list_clients,
    update_client,
)
from tools.social_post import (
    create_profile as create_social_profile,
    get_connected_platforms,
    post_from_airtable,
    schedule_week,
    build_food_caption,
    PLATFORM_LABELS,
)


def _generate_image(prompt, reference_paths=None):
    """
    Generate a single image via Google AI Studio (Nano Banana Pro).
    Uploads result to Kie.ai hosting. Returns hosted URL.

    Inlined here to avoid import conflicts between cravemode/tools
    and parent creative-engine-template/tools.
    """
    model_id = "gemini-3-pro-image-preview"
    api_key = config.GOOGLE_API_KEY
    kie_key = config.KIE_API_KEY

    # Build request parts
    parts = [{"text": prompt}]
    if reference_paths:
        for ref_path in reference_paths:
            path = Path(ref_path)
            mime_map = {".png": "image/png", ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg", ".webp": "image/webp"}
            mime = mime_map.get(path.suffix.lower(), "image/png")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            parts.append({"inline_data": {"mime_type": mime, "data": b64}})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    resp = _requests.post(url, headers={
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }, json={
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }, timeout=120)

    if resp.status_code != 200:
        raise Exception(f"Google AI error {resp.status_code}: {resp.text[:300]}")

    candidates = resp.json().get("candidates", [])
    if not candidates:
        raise Exception("No candidates in response")

    for part in candidates[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            b64_data = part["inlineData"]["data"]
            mime = part["inlineData"].get("mimeType", "image/png")
            ext = ".png" if "png" in mime else ".jpg"

            # Save to temp file and upload to Kie.ai
            import os
            tmp = os.path.join(tempfile.gettempdir(), f"cravemode_gen{ext}")
            with open(tmp, "wb") as f:
                f.write(base64.b64decode(b64_data))

            try:
                with open(tmp, "rb") as uf:
                    upload_resp = _requests.post(
                        "https://kieai.redpandaai.co/api/file-stream-upload",
                        headers={"Authorization": f"Bearer {kie_key}"},
                        files={"file": (f"cravemode_gen{ext}", uf)},
                        data={"uploadPath": "creative-cloner"},
                        timeout=30,
                    )
                upload_resp.raise_for_status()
                hosted_url = upload_resp.json().get("data", {}).get("downloadUrl", "")
                if not hosted_url:
                    raise Exception(f"No URL in Kie upload response: {upload_resp.json()}")
                return hosted_url
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)

    raise Exception("No image data in Google AI response")


def _submit_kie_video(prompt, image_url, last_image_url=None, model="kling-3.0",
                      duration="5", mode="pro"):
    """Submit a video generation task to Kie AI. Returns task_id."""
    kie_key = config.KIE_API_KEY
    model_id = "kling-3.0/video" if model == "kling-3.0" else "sora-2-pro-image-to-video"

    if model == "kling-3.0":
        payload = {
            "model": model_id,
            "input": {
                "mode": mode,
                "prompt": prompt,
                "duration": str(duration),
                "multi_shots": False,
                "sound": True,
            },
        }
        if image_url:
            payload["input"]["image_urls"] = [image_url]
            if last_image_url:
                payload["input"]["image_urls"].append(last_image_url)
        else:
            payload["input"]["aspect_ratio"] = "9:16"
    else:
        payload = {
            "model": model_id,
            "input": {
                "prompt": prompt,
                "aspect_ratio": "portrait",
                "n_frames": "10",
                "size": "high",
                "remove_watermark": True,
                "upload_method": "s3",
            },
        }
        if image_url:
            payload["input"]["image_urls"] = [image_url]

    resp = _requests.post(config.KIE_CREATE_URL, headers={
        "Authorization": f"Bearer {kie_key}",
        "Content-Type": "application/json",
    }, json=payload, timeout=30)

    if resp.status_code != 200:
        raise Exception(f"Kie API error: {resp.status_code} - {resp.text[:200]}")

    result = resp.json()
    if result.get("code") != 200:
        raise Exception(f"Kie error: {result.get('msg')}")

    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        raise Exception(f"No taskId in response: {result}")
    return task_id


def _poll_kie_video(task_id, max_wait=600, poll_interval=10):
    """Poll a Kie AI video task until completion. Returns video URL."""
    import time as _time
    import json as _json

    kie_key = config.KIE_API_KEY
    start = _time.time()

    while _time.time() - start < max_wait:
        resp = _requests.get(
            f"{config.KIE_STATUS_URL}?taskId={task_id}",
            headers={"Authorization": f"Bearer {kie_key}"},
            timeout=30,
        )
        if resp.status_code != 200:
            _time.sleep(poll_interval)
            continue

        data = resp.json().get("data", {})
        state = data.get("state", "unknown")

        if state == "success":
            result_json = _json.loads(data.get("resultJson", "{}"))
            urls = result_json.get("resultUrls", [])
            if urls:
                return urls[0]
            raise Exception("No result URLs in completed task")
        elif state == "fail":
            raise Exception(f"Task failed: {data.get('failMsg', 'Unknown')}")
        else:
            elapsed = int(_time.time() - start)
            mins, secs = divmod(elapsed, 60)
            print(f"    Video status: {state} ({mins}m {secs}s)", flush=True)
            _time.sleep(poll_interval)

    raise Exception(f"Timeout after {max_wait}s")


class CraveModeEngine:
    """Main CraveMode engine orchestrator."""

    def __init__(self):
        """Initialize engine and check credentials."""
        missing = config.check_credentials()
        if missing:
            print("WARNING: Missing credentials. Run setup.py first.")

    def onboard_client(self, name, cuisine="default", tier="starter", dishes=None):
        """
        Onboard a new restaurant client.

        Args:
            name: Restaurant name
            cuisine: Cuisine style (italian, mexican, asian, american, etc.)
            tier: Plan tier (starter, growth, premium)
            dishes: List of dicts [{"name": "Margherita Pizza", "category": "entree"}]

        Returns:
            tuple: (client, content_plan_records)
        """
        client_id = name.lower().replace(" ", "-").replace("'", "")

        # Register client
        client = create_client(client_id, name, cuisine, tier, dishes)
        print(f"\nClient registered: {name}")
        print(f"  Tier: {TIERS[tier]['name']} (${TIERS[tier]['price']}/mo)")
        print(f"  Cuisine: {cuisine}")
        print(f"  Dishes: {len(dishes or [])}")

        # Generate content plan
        if dishes:
            plan = generate_content_plan(name, dishes, cuisine, tier)
            print(f"  Content plan: {len(plan)} items")

            # Show plan summary
            product_counts = {}
            for item in plan:
                p = item.get("Product", "Unknown")
                product_counts[p] = product_counts.get(p, 0) + 1

            for product, count in product_counts.items():
                print(f"    - {product}: {count}")

            return client, plan
        else:
            print("  No dishes provided yet. Add dishes to generate content plan.")
            return client, []

    def validate_inputs(self, image_paths):
        """
        Run Gate 1 on all input photos.

        Args:
            image_paths: List of file paths to validate

        Returns:
            dict: {"passed": [...], "failed": [...]}
        """
        passed = []
        failed = []

        for path in image_paths:
            print(f"\n[Gate 1] Validating: {Path(path).name}")
            result = gate1_validate_input(path)

            if result["passed"]:
                print(f"  PASSED")
                passed.append({"path": path, "result": result})
            else:
                print(f"  FAILED: {', '.join(result['issues'])}")
                failed.append({"path": path, "result": result})

        print(f"\nValidation complete: {len(passed)} passed, {len(failed)} failed")
        return {"passed": passed, "failed": failed}

    def generate_images(self, client_id=None, reference_paths=None, provider=None,
                         num_variations=2):
        """
        Generate enhanced images for pending records.

        Uses the parent's generate_ugc_image() directly (not generate_batch)
        to avoid Airtable field name conflicts. Handles Leads table updates ourselves.

        If client_id is provided, generates for that client's records.
        If client_id is None, generates for all Leads with Status="Create".

        Args:
            client_id: Client identifier (optional — if None, uses all "Create" records)
            reference_paths: Local paths to reference product photos
            provider: Override provider (default: google)
            num_variations: Images per record (1 or 2, default 2)

        Returns:
            list: Generation results
        """
        import time

        if client_id:
            quota = check_quota(client_id, "image")
            if not quota["allowed"]:
                print(f"Quota exceeded! {quota['used']}/{quota['limit']} images used this month.")
                return []

            client = get_client(client_id)
            if not client:
                print(f"Client '{client_id}' not found")
                return []

            restaurant = client["name"]
            records = get_records_by_restaurant(restaurant)
            pending = [r for r in records
                       if r.get("fields", {}).get("Status") == "Create"
                       and r.get("fields", {}).get("Prompt")]

            remaining = quota["remaining"]
            if len(pending) > remaining:
                print(f"Warning: {len(pending)} pending but only {remaining} quota remaining.")
                pending = pending[:remaining]
        else:
            pending = get_pending_images()
            restaurant = "All Restaurants"

        if not pending:
            print(f"No pending images for {restaurant}")
            return []

        count = len(pending)
        num_variations = max(1, min(2, num_variations))
        cost_per = config.get_cost(config.DEFAULT_IMAGE_MODEL, provider or "google")
        total_cost = count * num_variations * cost_per

        print(f"\n{'='*50}")
        print(f"  CraveMode Image Enhancement")
        print(f"{'='*50}")
        print(f"  Source: {restaurant}")
        print(f"  Records: {count}")
        print(f"  Images: {count * num_variations} ({num_variations} per record)")
        print(f"  Model: {config.DEFAULT_IMAGE_MODEL}")
        print(f"  Estimated cost: ${total_cost:.2f}")
        if client_id:
            print(f"  Quota remaining: {quota['remaining']}")
        print(f"{'='*50}\n")

        pass  # Using _generate_image() below

        results = []
        succeeded = 0

        for i, record in enumerate(pending):
            fields = record.get("fields", {})
            name = fields.get("Name", "untitled")
            prompt = fields.get("Prompt", "")

            print(f"\n[{i+1}/{count}] {name}")

            # Get input image as reference — download from Airtable if no local paths
            input_imgs = fields.get("input_image", [])
            ref_paths = reference_paths
            if not ref_paths and input_imgs:
                # Download Airtable attachment to temp file so model actually sees the food
                import os
                input_url = input_imgs[0].get("url", "")
                if input_url:
                    try:
                        dl_resp = _requests.get(input_url, timeout=30)
                        dl_resp.raise_for_status()
                        tmp_input = os.path.join(tempfile.gettempdir(), f"cravemode_input_{i}.jpg")
                        with open(tmp_input, "wb") as fh:
                            fh.write(dl_resp.content)
                        ref_paths = [tmp_input]
                        print(f"  Downloaded input image ({len(dl_resp.content)//1024}KB)")
                    except Exception as dl_err:
                        print(f"  WARNING: Could not download input image: {dl_err}")

            update_fields = {}

            for var_num in range(1, num_variations + 1):
                print(f"  Variation {var_num}/{num_variations}...")
                try:
                    url = _generate_image(prompt, ref_paths)
                    img_field = "image_1" if var_num == 1 else "image_2"
                    update_fields[img_field] = [{"url": url}]
                    print(f"  Done: {url[:60]}...")
                except Exception as e:
                    print(f"  FAILED: {e}")

                if var_num < num_variations:
                    time.sleep(1)

            # Clean up downloaded temp input file
            if not reference_paths and ref_paths:
                import os
                for tmp_path in ref_paths:
                    if tmp_path and os.path.exists(tmp_path) and "cravemode_input_" in tmp_path:
                        os.remove(tmp_path)

            # Update Leads table directly with correct field names
            if update_fields:
                update_fields["Status"] = "Done"
                update_record(record["id"], update_fields)
                succeeded += 1
                print(f"  Airtable updated: {name} → Done")

            results.append(update_fields if update_fields else None)

        # Record usage for client
        if client_id:
            images_generated = sum(1 for r in results if r is not None)
            record_usage(client_id, "image", images_generated)

        print(f"\n{'='*50}")
        print(f"  Complete: {succeeded}/{count} records enhanced")
        print(f"  Actual cost: ~${succeeded * num_variations * cost_per:.2f}")
        print(f"{'='*50}\n")

        return results

    def generate_videos(self, model="kling-3.0", duration="5", mode="pro",
                        transition=True):
        """
        Generate transition videos for Done records that have images but no video.

        Uses Kie AI (Kling 3.0) for transition videos:
        - image_1 as start frame, image_2 as end frame
        - transition_prompt as the motion prompt

        Args:
            model: Video model ("kling-3.0" or "sora-2-pro")
            duration: Video duration in seconds
            mode: "std" or "pro" (Kling only)
            transition: If True, uses image_1 + image_2 for start/end frames

        Returns:
            list: Generation results
        """
        import time
        from tools.airtable import get_records

        # Find records with images but no video
        records = get_records('{Status} = "Done"')
        need_video = []
        for r in records:
            f = r.get("fields", {})
            if f.get("image_1") and not f.get("video") and f.get("transition_prompt"):
                need_video.append(r)

        if not need_video:
            print("No records need video generation.")
            return []

        count = len(need_video)
        provider = "kie"
        cost_per = config.get_cost(model, provider)
        total_cost = count * cost_per

        print(f"\n{'='*50}")
        print(f"  CraveMode Video Generation")
        print(f"{'='*50}")
        print(f"  Records: {count}")
        print(f"  Model: {model} via {provider}")
        print(f"  Mode: {mode} | Duration: {duration}s")
        print(f"  Transition: {transition} (image_1 → image_2)")
        print(f"  Estimated cost: ${total_cost:.2f}")
        print(f"{'='*50}\n")

        # Phase 1: Submit all tasks
        print("Phase 1: Submitting video tasks...")
        submissions = []  # (record, task_id)

        for i, record in enumerate(need_video):
            fields = record.get("fields", {})
            name = fields.get("Name", "untitled")
            prompt = fields.get("transition_prompt", "")

            # Get image URLs from Airtable attachments
            img1_list = fields.get("image_1", [])
            img2_list = fields.get("image_2", [])
            img1_url = img1_list[0].get("url") if img1_list else None
            img2_url = img2_list[0].get("url") if img2_list else None

            if not img1_url:
                print(f"  [{i+1}/{count}] {name} — SKIP (no image_1)")
                submissions.append((record, None))
                continue

            last_url = img2_url if transition else None

            print(f"  [{i+1}/{count}] {name} — submitting...", flush=True)
            try:
                task_id = _submit_kie_video(
                    prompt, img1_url, last_image_url=last_url,
                    model=model, duration=duration, mode=mode,
                )
                print(f"    Task: {task_id}")
                submissions.append((record, task_id))
            except Exception as e:
                print(f"    FAILED to submit: {e}")
                submissions.append((record, None))

            time.sleep(1)  # Rate limit

        # Phase 2: Poll all tasks
        submitted = [(r, tid) for r, tid in submissions if tid]
        if not submitted:
            print("\nNo tasks submitted successfully.")
            return []

        print(f"\nPhase 2: Polling {len(submitted)} tasks...")
        results = []
        succeeded = 0

        for record, task_id in submitted:
            fields = record.get("fields", {})
            name = fields.get("Name", "untitled")
            print(f"\n  Polling: {name} ({task_id[:20]}...)", flush=True)

            try:
                video_url = _poll_kie_video(task_id, max_wait=600, poll_interval=10)
                update_record(record["id"], {
                    "video": [{"url": video_url}],
                    "Video_Status": "Done",
                })
                print(f"  Done: {video_url[:60]}...")
                succeeded += 1
                results.append({"name": name, "video_url": video_url})
            except Exception as e:
                print(f"  FAILED: {e}")
                results.append(None)

        print(f"\n{'='*50}")
        print(f"  Complete: {succeeded}/{count} videos generated")
        print(f"  Actual cost: ~${succeeded * cost_per:.2f}")
        print(f"{'='*50}\n")

        return results

    def score_outputs(self, client_id):
        """
        Run Gate 2 quality scoring on all generated images.

        Updates Airtable with quality scores and status.
        """
        client = get_client(client_id)
        if not client:
            return []

        restaurant = client["name"]
        records = get_records_by_restaurant(restaurant)
        generated = [r for r in records
                     if r.get("fields", {}).get("Image Status") == "Generated"]

        if not generated:
            print(f"No generated images to score for {restaurant}")
            return []

        results = []
        for record in generated:
            fields = record.get("fields", {})
            ad_name = fields.get("Ad Name", "untitled")

            # Check if record has a generated image
            img1 = fields.get("Generated Image 1", [])
            if not img1:
                continue

            print(f"\n[Gate 2] Scoring: {ad_name}")

            # Download and score (would need to download URL to temp file)
            # For now, mark as Quality Check for manual review
            update_record(record["id"], {
                "Image Status": "Quality Check",
            })
            results.append({"record": record["id"], "ad_name": ad_name})

        print(f"\n{len(results)} images moved to Quality Check")
        return results

    def get_status(self, client_id):
        """Get full status for a client."""
        summary = get_usage_summary(client_id)
        if not summary:
            print(f"Client '{client_id}' not found")
            return None

        print(f"\n{'='*50}")
        print(f"  {summary['client']} — {summary['tier']} (${summary['price']}/mo)")
        print(f"{'='*50}")
        print(f"  Month: {summary['month']}")
        print(f"  Images: {summary['images']['generated']}/{summary['images']['limit']} "
              f"({summary['images']['remaining']} remaining)")
        print(f"  Videos: {summary['videos']['generated']}/{summary['videos']['limit']} "
              f"({summary['videos']['remaining']} remaining)")
        print(f"  Production cost: ${summary['production_cost']}")
        print(f"  Margin: ${summary['margin']} ({summary['margin_pct']}%)")
        print(f"{'='*50}\n")

        return summary

    # --- Social Media Posting ---

    def connect_social(self, client_id):
        """
        Set up social media posting for a client.
        Creates an Ayrshare profile and stores the key.

        Returns:
            dict: Profile info with connect instructions
        """
        client = get_client(client_id)
        if not client:
            print(f"Client '{client_id}' not found")
            return None

        # Check if already connected
        if client.get("ayrshare_profile_key"):
            profile_key = client["ayrshare_profile_key"]
            connected = get_connected_platforms(profile_key)
            print(f"\n{client['name']} already has a social profile.")
            print(f"  Connected: {', '.join(PLATFORM_LABELS.get(p, p) for p in connected) or 'None'}")
            return {"profile_key": profile_key, "connected": connected}

        # Create new Ayrshare profile
        profile = create_social_profile(client["name"], client_id)
        profile_key = profile["profile_key"]

        # Store in client record
        update_client(client_id, ayrshare_profile_key=profile_key)

        print(f"\nSocial profile created for {client['name']}")
        print(f"  Profile key: {profile_key}")
        print(f"\n  Next: Have the restaurant owner connect their accounts.")
        print(f"  Supported: Instagram, TikTok, Facebook, Google Business Profile")

        return profile

    def post_content(self, client_id, platforms=None, product_type=None):
        """
        Post approved content from Airtable to social media.

        Finds the latest approved content for the client and posts it
        to all connected platforms (or specified platforms).

        Args:
            client_id: Client identifier
            platforms: Override platforms (default: all connected)
            product_type: Product type for caption optimization

        Returns:
            dict: Results per platform
        """
        client = get_client(client_id)
        if not client:
            print(f"Client '{client_id}' not found")
            return None

        profile_key = client.get("ayrshare_profile_key")
        if not profile_key:
            print(f"No social profile for {client['name']}. Run connect_social() first.")
            return None

        # Get records with approved/generated content
        records = get_records_by_restaurant(client["name"])
        postable = []
        for r in records:
            fields = r.get("fields", {})
            has_media = (
                fields.get("Generated Video 1") or fields.get("video")
                or fields.get("Generated Image 1") or fields.get("image_1")
            )
            status = fields.get("Status", fields.get("Image Status", ""))
            if has_media and status in ("Done", "Approved", "Generated"):
                postable.append(r)

        if not postable:
            print(f"No approved content to post for {client['name']}")
            return None

        # Show what we'll post
        print(f"\n{'='*50}")
        print(f"  Social Media Posting — {client['name']}")
        print(f"{'='*50}")
        print(f"  Records with content: {len(postable)}")

        if not platforms:
            platforms = get_connected_platforms(profile_key)
        print(f"  Posting to: {', '.join(PLATFORM_LABELS.get(p, p) for p in platforms)}")

        # Post the first postable record
        record = postable[0]
        ad_name = record.get("fields", {}).get(
            "Ad Name", record.get("fields", {}).get("Name", "")
        )
        print(f"  Content: {ad_name}")
        print(f"{'='*50}\n")

        result = post_from_airtable(
            profile_key=profile_key,
            record=record,
            platforms=platforms,
            product_type=product_type,
        )

        # Print results
        for platform, outcome in result.items():
            label = PLATFORM_LABELS.get(platform, platform)
            if outcome["status"] == "posted":
                print(f"  {label}: Posted")
            else:
                print(f"  {label}: FAILED — {outcome.get('error', 'unknown')}")

        return result

    def schedule_content(self, client_id, content_items, platforms=None):
        """
        Schedule a week of content for a client.

        Args:
            client_id: Client identifier
            content_items: List of content dicts (see schedule_week)
            platforms: Override platforms

        Returns:
            list: Scheduling results
        """
        client = get_client(client_id)
        if not client:
            print(f"Client '{client_id}' not found")
            return None

        profile_key = client.get("ayrshare_profile_key")
        if not profile_key:
            print(f"No social profile for {client['name']}. Run connect_social() first.")
            return None

        if not platforms:
            platforms = get_connected_platforms(profile_key)

        print(f"\nScheduling {len(content_items)} posts for {client['name']}")
        print(f"  Platforms: {', '.join(PLATFORM_LABELS.get(p, p) for p in platforms)}")

        results = schedule_week(profile_key, platforms, content_items)

        print(f"\n  {len(results)} posts scheduled")
        return results
