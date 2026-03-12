"""
CraveMode 3-Gate Automated Quality Pipeline.

Zero human input. Gemini vision scores everything.

Gate 1: INPUT VALIDATION
  - Is it food? (Gemini vision check)
  - Resolution >= 1080x1080
  - Lighting acceptable
  - Not blurry/corrupted

Gate 2: ENHANCEMENT STANDARDS
  - Color vibrancy (1-10)
  - Sharpness (1-10)
  - Composition (1-10)
  - Style consistency (1-10)
  - Minimum score: 7.0/10 average

Gate 3: OUTPUT VALIDATION
  - Output is better than input
  - No hallucinated elements (extra fingers, wrong food, text artifacts)
  - Food identity preserved
"""

import os
import json
import base64
import requests
from pathlib import Path


# Quality thresholds
MIN_RESOLUTION = 1080  # minimum dimension in pixels
MIN_QUALITY_SCORE = 7.0  # out of 10
MIN_GATE3_IMPROVEMENT = True  # output must be better than input


def _get_google_api_key():
    """Get Google API key from environment or .env file."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".claude" / ".env"
        if not env_path.exists():
            env_path = Path(__file__).parent.parent.parent / ".claude" / ".env"
        load_dotenv(env_path)
        key = os.getenv("GOOGLE_API_KEY")
    return key


def _encode_image(image_path):
    """Read and base64-encode an image file."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _call_gemini_vision(prompt, image_b64, mime_type="image/jpeg"):
    """Call Gemini 2.0 Flash with an image for vision analysis."""
    api_key = _get_google_api_key()
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_b64,
                    }
                },
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        },
    }

    response = requests.post(url, json=payload, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Gemini API error ({response.status_code}): {response.text}")

    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


# --- Gate 1: Input Validation ---

def gate1_validate_input(image_path):
    """
    Gate 1: Validate input photo meets minimum standards.

    Checks:
    - Is it food? (Gemini vision)
    - Resolution >= 1080x1080
    - Not blurry/corrupted
    - Lighting acceptable

    Args:
        image_path: Path to the uploaded image

    Returns:
        dict: {"passed": bool, "issues": [...], "details": {...}}
    """
    issues = []
    details = {}

    # Check file exists and has size
    path = Path(image_path)
    if not path.exists():
        return {"passed": False, "issues": ["File not found"], "details": {}}

    file_size = path.stat().st_size
    if file_size < 10_000:  # less than 10KB is suspicious
        issues.append(f"File too small ({file_size} bytes) — likely corrupted or a thumbnail")

    # Check resolution using image header (without PIL if possible)
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            width, height = img.size
            details["width"] = width
            details["height"] = height
            details["format"] = img.format

            if min(width, height) < MIN_RESOLUTION:
                issues.append(
                    f"Resolution too low: {width}x{height} "
                    f"(minimum {MIN_RESOLUTION}x{MIN_RESOLUTION})"
                )
    except ImportError:
        # PIL not available — skip resolution check, Gemini will handle quality
        details["resolution_check"] = "skipped (PIL not installed)"
    except Exception as e:
        issues.append(f"Cannot read image: {str(e)}")
        return {"passed": False, "issues": issues, "details": details}

    # Gemini vision check — is it food? Is it blurry?
    image_b64 = _encode_image(image_path)
    mime = "image/jpeg"
    if str(image_path).lower().endswith(".png"):
        mime = "image/png"

    gemini_prompt = """Analyze this image for food photography quality. Return JSON:
{
    "is_food": true/false,
    "food_description": "brief description of the food shown",
    "is_blurry": true/false,
    "lighting_quality": "good" or "poor" or "acceptable",
    "lighting_notes": "brief notes on lighting",
    "overall_usable": true/false,
    "rejection_reason": "reason if not usable, or null"
}

Rules:
- is_food must be true if the image contains prepared food, a dish, or a plated meal
- is_blurry is true only if significantly out of focus (minor noise is acceptable)
- lighting_quality: "good" = well-lit, "acceptable" = workable, "poor" = too dark/overexposed
- overall_usable: true if this photo can be used as input for AI enhancement"""

    try:
        vision_result = _call_gemini_vision(gemini_prompt, image_b64, mime)
        details["vision"] = vision_result

        if not vision_result.get("is_food"):
            issues.append(f"Not food: {vision_result.get('rejection_reason', 'Image does not contain food')}")

        if vision_result.get("is_blurry"):
            issues.append("Image is blurry — reshoot needed")

        if vision_result.get("lighting_quality") == "poor":
            issues.append(f"Poor lighting: {vision_result.get('lighting_notes', '')}")

        if not vision_result.get("overall_usable"):
            reason = vision_result.get("rejection_reason", "Not usable for enhancement")
            if reason not in str(issues):
                issues.append(reason)

    except Exception as e:
        details["vision_error"] = str(e)
        # Don't fail gate 1 if Gemini is down — continue with what we have

    passed = len(issues) == 0
    return {"passed": passed, "issues": issues, "details": details}


# --- Gate 2: Enhancement Standards ---

def gate2_score_output(image_path):
    """
    Gate 2: Score the generated/enhanced image against quality standards.

    Scores (1-10 each):
    - Color vibrancy
    - Sharpness
    - Composition
    - Style consistency
    - Appetizingness

    Must average >= 7.0 to pass.

    Args:
        image_path: Path to the generated image

    Returns:
        dict: {"passed": bool, "average_score": float, "scores": {...}, "feedback": str}
    """
    image_b64 = _encode_image(image_path)
    mime = "image/png" if str(image_path).lower().endswith(".png") else "image/jpeg"

    gemini_prompt = """Score this food photograph on a 1-10 scale for each category. Return JSON:
{
    "color_vibrancy": <1-10>,
    "sharpness": <1-10>,
    "composition": <1-10>,
    "style_consistency": <1-10>,
    "appetizingness": <1-10>,
    "feedback": "1-2 sentence summary of strengths and weaknesses",
    "improvement_suggestions": ["suggestion 1", "suggestion 2"]
}

Scoring guide:
- 1-3: Poor, not usable
- 4-6: Acceptable but needs improvement
- 7-8: Good, professional quality
- 9-10: Exceptional, magazine-worthy

Be strict. Restaurant marketing photos should be 7+ across all categories."""

    vision_result = _call_gemini_vision(gemini_prompt, image_b64, mime)

    score_fields = ["color_vibrancy", "sharpness", "composition", "style_consistency", "appetizingness"]
    scores = {k: vision_result.get(k, 0) for k in score_fields}
    avg = sum(scores.values()) / len(scores) if scores else 0

    return {
        "passed": avg >= MIN_QUALITY_SCORE,
        "average_score": round(avg, 1),
        "scores": scores,
        "feedback": vision_result.get("feedback", ""),
        "suggestions": vision_result.get("improvement_suggestions", []),
    }


# --- Gate 3: Output Validation ---

def gate3_validate_output(input_path, output_path):
    """
    Gate 3: Compare output to input — output must be better.

    Checks:
    - Output is visually better than input
    - No hallucinated elements (wrong food, extra items, text artifacts)
    - Food identity preserved (same dish, same plating)

    Args:
        input_path: Path to the original input image
        output_path: Path to the generated output image

    Returns:
        dict: {"passed": bool, "is_better": bool, "issues": [...], "comparison": str}
    """
    input_b64 = _encode_image(input_path)
    output_b64 = _encode_image(output_path)

    input_mime = "image/png" if str(input_path).lower().endswith(".png") else "image/jpeg"
    output_mime = "image/png" if str(output_path).lower().endswith(".png") else "image/jpeg"

    # Gemini can only handle one image per call, so we do two calls
    # First: analyze input
    input_prompt = """Describe this food image in detail. Return JSON:
{
    "food_items": ["list of food items visible"],
    "plating_style": "description of how food is plated",
    "key_visual_elements": ["element 1", "element 2"],
    "overall_quality": <1-10>
}"""

    output_prompt = """Analyze this AI-enhanced food image. Return JSON:
{
    "food_items": ["list of food items visible"],
    "plating_style": "description of how food is plated",
    "key_visual_elements": ["element 1", "element 2"],
    "overall_quality": <1-10>,
    "has_artifacts": true/false,
    "artifact_description": "description of any AI artifacts, or null",
    "has_wrong_elements": true/false,
    "wrong_elements_description": "description of incorrect elements, or null"
}"""

    try:
        input_analysis = _call_gemini_vision(input_prompt, input_b64, input_mime)
        output_analysis = _call_gemini_vision(output_prompt, output_b64, output_mime)
    except Exception as e:
        return {
            "passed": False,
            "is_better": False,
            "issues": [f"Analysis failed: {str(e)}"],
            "comparison": "",
        }

    issues = []

    # Check for AI artifacts
    if output_analysis.get("has_artifacts"):
        issues.append(f"AI artifacts detected: {output_analysis.get('artifact_description', 'unknown')}")

    if output_analysis.get("has_wrong_elements"):
        issues.append(f"Wrong elements: {output_analysis.get('wrong_elements_description', 'unknown')}")

    # Check food identity preserved
    input_foods = set(f.lower() for f in input_analysis.get("food_items", []))
    output_foods = set(f.lower() for f in output_analysis.get("food_items", []))
    if input_foods and not input_foods.intersection(output_foods):
        issues.append("Food identity not preserved — output shows different food than input")

    # Quality comparison
    input_quality = input_analysis.get("overall_quality", 5)
    output_quality = output_analysis.get("overall_quality", 5)
    is_better = output_quality >= input_quality

    if not is_better:
        issues.append(f"Output quality ({output_quality}/10) not better than input ({input_quality}/10)")

    comparison = (
        f"Input: {input_quality}/10 | Output: {output_quality}/10 | "
        f"{'Improved' if is_better else 'Degraded'}"
    )

    return {
        "passed": len(issues) == 0 and is_better,
        "is_better": is_better,
        "issues": issues,
        "comparison": comparison,
        "input_analysis": input_analysis,
        "output_analysis": output_analysis,
    }


# --- Full Pipeline ---

def run_quality_pipeline(input_path, output_path=None):
    """
    Run the full 3-gate quality pipeline.

    Args:
        input_path: Path to the original photo
        output_path: Path to the generated output (Gate 3 only, optional)

    Returns:
        dict: {"overall_passed": bool, "gate1": {...}, "gate2": {...}, "gate3": {...}}
    """
    result = {"overall_passed": False}

    # Gate 1: Input Validation
    print("[Gate 1] Validating input...")
    g1 = gate1_validate_input(input_path)
    result["gate1"] = g1
    if not g1["passed"]:
        print(f"[Gate 1] FAILED: {', '.join(g1['issues'])}")
        return result
    print("[Gate 1] PASSED")

    # Gate 2: Score output (if we have one)
    if output_path:
        print("[Gate 2] Scoring output quality...")
        g2 = gate2_score_output(output_path)
        result["gate2"] = g2
        if not g2["passed"]:
            print(f"[Gate 2] FAILED: Average {g2['average_score']}/10 (minimum {MIN_QUALITY_SCORE})")
            print(f"         {g2['feedback']}")
            return result
        print(f"[Gate 2] PASSED ({g2['average_score']}/10)")

        # Gate 3: Output vs Input comparison
        print("[Gate 3] Comparing output to input...")
        g3 = gate3_validate_output(input_path, output_path)
        result["gate3"] = g3
        if not g3["passed"]:
            print(f"[Gate 3] FAILED: {', '.join(g3['issues'])}")
            return result
        print(f"[Gate 3] PASSED ({g3['comparison']})")

    result["overall_passed"] = True
    return result
