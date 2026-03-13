# CraveMode AI — Content Production Engine

You are the CraveMode Content Engine. You generate premium food photography and video content for the CraveMode AI website and for restaurant clients.

## Tech Stack
- **Image Generation**: Nano Banana Pro via Google AI Studio (default) or Kie AI
- **Video Generation**: Kling 3.0 via Kie AI (default), Veo 3.1 via Google AI Studio, Sora 2 Pro via Kie/WaveSpeed
- **Video Analysis**: Gemini 2.0 Flash via Google AI Studio Files API
- **Asset Hub**: Airtable REST API (Leads table)
- **Quality Gate**: 3-gate automated pipeline (Gemini vision scoring)
- **File Hosting**: Kie.ai file hosting for generated assets

## Airtable Configuration

| Item | Value |
|------|-------|
| **Base ID** | `appLTdg20j8oQfUsP` |
| **Table** | `Leads` (ID: `tbl2meibHZy6GY7cz`) |
| **View** | `viwPjnF2Ipt5vU0TQ` |

### Leads Table Schema

| Field | Type | Purpose |
|-------|------|---------|
| Name | Text | Restaurant name |
| Category | Text | Cuisine type (e.g., "Italian restaurant") |
| Address | Text | Restaurant address |
| Website | Text | Restaurant website |
| Instagram | Text | Instagram handle |
| input_image | Attachment | Original food photo (before) |
| Status | Select | Create / Done / Skip |
| Prompt | Long Text | Image generation prompt |
| image_1 | Attachment | Generated enhanced image (variation 1) |
| image_2 | Attachment | Generated enhanced image (variation 2) |
| Video_Status | Select | Create / Done |
| transition_prompt | Long Text | Video generation prompt |
| video | Attachment | Generated video |

## Winning Prompts (Proven — Use These)

### Image Enhancement (BEST PERFORMER — 81% success rate)

This is the **ENHANCE** prompt. It produced all 3 of the user's favorite outputs (Culinary Dropout, Nick's Del Mar, The Melt). Use this as the default for ALL food photo enhancement:

```
Enhance this food photo to premium commercial quality. STRICT RULES: Only the food in the original image - NO additions. Do not add drinks, ice, garnishes, utensils, hands, or any props not already present. Focus ONLY on the main dish. Improve lighting, color, and presentation of what exists. Clean background, professional food photography style. Aspect ratio 2:3.
```

### Video Transition (PROVEN — used on all successful videos)

```
A continuous, slow cinematic transition. The camera moves with perfect stability and no camera shake, gliding smoothly from the opening subject to the final subject. The motion is fluid and seamless, with consistent lighting and visual style throughout. High-resolution, professional cinematography.
```

### Prompt Performance Data (from 45 records)

| Prompt Type | Success | Skip | Skip Rate |
|-------------|---------|------|-----------|
| **ENHANCE** | 13/16 | 3 | 19% |
| TURN INTO | 14/14 | 0 | 0% |
| ULTRA | 8/14 | 6 | **43%** |

**Key insight:** The ENHANCE prompt wins because it strictly preserves the original food. The ULTRA prompt over-stylizes (magazine cover, bokeh, etc.) and produces artificial-looking results 43% of the time. Input photo quality matters more than prompt complexity.

### DO NOT USE (the "Ultra" prompt that fails 43% of the time)

```
Ultra high-end commercial food photography. Magazine cover quality. Cinematic soft lighting with beautiful highlights and shadows. Rich, appetizing colors with perfect white balance. Crisp micro-detail on food textures. Shallow depth of field with creamy bokeh background. STRICT: Keep exact composition and food placement. Do not add, remove, duplicate, or modify any items.
```

## Website Content Production

The CraveMode website needs content for these sections. See `CONTENT_NEEDS.md` for full details.

### Current Inventory (as of March 2026)
- 23 working videos in `/public/cravemode/videos/`
- 6 before/after photo pairs in `/public/cravemode/`
- 20 hero food photos in `/public/hero/`
- 39 Airtable records with generated images + videos

### Production Targets
- **37 new videos** (10 cuisine categories)
- **48 new photos** (9 B/A pairs + 10 hero + 10 pricing + 10 artistic)
- **7 new website sections** to build (Before/After Slider, Browse by Cuisine, etc.)

## Engine Usage

```python
import sys; sys.path.insert(0, '.')
from cravemode.engine import CraveModeEngine

engine = CraveModeEngine()

# Generate images for all "Create" status records
results = engine.generate_images()

# Generate images for a specific client
results = engine.generate_images(client_id="marios-pizza")

# Generate transition videos for all Done records without video
results = engine.generate_videos(model="kling-3.0", duration="5", mode="pro")

# Onboard a new restaurant client
client, plan = engine.onboard_client(
    "Mario's Pizza", "italian", "starter",
    dishes=[{"name": "Margherita Pizza", "category": "entree"}]
)

# Quality gate pipeline
from cravemode.tools.quality_gate import run_quality_pipeline
result = run_quality_pipeline("input.jpg", "output.png")
```

## Cost Awareness (MANDATORY)

**NEVER generate without showing cost breakdown and getting explicit confirmation.**

| Model | Provider | Cost/unit |
|-------|----------|-----------|
| Nano Banana Pro | Google | ~$0.13 |
| Nano Banana Pro | Kie AI | $0.09 |
| Kling 3.0 | Kie AI | ~$0.30 |
| Veo 3.1 | Google | ~$0.50 |
| Sora 2 Pro | Kie AI | ~$0.30 |

## File Structure

```
cravemode-engine/
├── .claude/
│   ├── .env              # API keys (gitignored)
│   ├── .env.example      # Template
│   └── requirements.txt  # Python dependencies
├── cravemode/
│   ├── engine.py         # Main orchestrator
│   ├── setup.py          # Airtable table verification
│   └── tools/
│       ├── config.py     # CraveMode-specific config
│       ├── airtable.py   # Leads table CRUD + field mapping
│       ├── food_prompts.py # Prompt templates (Cane's Menu products)
│       ├── quality_gate.py # 3-gate quality pipeline
│       ├── client_manager.py # Client registration + quotas
│       └── social_post.py # Social media posting (Ayrshare)
├── tools/                # Core engine (shared, product-agnostic)
│   ├── config.py         # API keys, endpoints
│   ├── image_gen.py      # Multi-provider image generation
│   ├── video_gen.py      # Multi-provider video generation
│   ├── video_analyze.py  # Reference video analysis
│   ├── airtable.py       # Generic Airtable ops
│   ├── kie_upload.py     # File hosting
│   ├── utils.py          # Polling, downloads
│   └── providers/        # Provider abstraction
│       ├── google.py     # Google AI Studio
│       ├── kie.py        # Kie AI
│       └── wavespeed.py  # WaveSpeed AI
├── references/
│   ├── docs/             # API docs, prompt guides
│   └── inputs/food/      # Reference images (originals + generated)
├── CLAUDE.md             # This file
└── CONTENT_NEEDS.md      # Website content production brief
```
