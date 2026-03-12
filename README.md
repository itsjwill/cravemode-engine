# CraveMode AI — Restaurant Content Engine

Turn any restaurant's phone photo into **3 commercial-grade images + 3 scroll-stopping videos** — automated, at scale.

---

## What It Produces

Every restaurant photo goes in, **6 assets** come out:

| # | Asset | Type | Angle | Description |
|---|-------|------|-------|-------------|
| 1 | **Hero Shot** | Image | 45° | $1,500 food shoot quality, dark moody background |
| 2 | **Overhead** | Image | 90° flat lay | Same photoshoot, overhead angle |
| 3 | **Close-Up** | Image | Macro detail | Tight crop on most appetizing part |
| 4 | **Action Video** | Video (5s) | Static | Dish-specific action (cilantro scatter, cheese pull, knife slice) |
| 5 | **Interact Video** | Video (5s) | Static | Someone eating the dish naturally |
| 6 | **Plating Build** | Video (5s) | Overhead | Dish assembled piece by piece |

All 3 images share the **same surface, lighting, and mood** — they look like one photoshoot.
All 3 videos use **black food-safe gloves** on any hands touching food.

---

## Examples (Approved Outputs)

The `examples/` folder contains approved outputs showing exactly what the engine produces.

### Taqueria La Loma (Mexican — full set)

```
examples/taqueria-la-loma/
├── input.jpg              # Original restaurant phone photo
├── image_1_hero.jpg       # 45° hero shot — dark background, colorful tile surface
├── image_2_overhead.jpg   # 90° overhead flat lay — same surface, same lighting
├── image_3_closeup.jpg    # Macro close-up — texture detail, shallow DOF
├── video_1_action.mp4     # Cilantro/onion scatter + lime wedge (5s, Kling 3.0)
├── video_2_interact.mp4   # Pick up taco, tilt, bite (5s, Kling 3.0)
└── video_3_plating.mp4    # Overhead plating build assembly (5s, Kling 3.0)
```

### Seoul Kitchen (Korean — images only)

```
examples/seoul-kitchen/
├── input.jpg              # Original restaurant phone photo
├── image_1_hero.jpg       # 45° hero shot — dark slate surface, moody lighting
├── image_2_overhead.jpg   # 90° overhead flat lay
└── image_3_closeup.jpg    # Macro close-up detail
```

---

## Folder Structure

```
cravemode/
│
├── examples/                      # APPROVED SAMPLE OUTPUTS (see above)
│   ├── taqueria-la-loma/          # Full set: input + 3 images + 3 videos
│   └── seoul-kitchen/             # Images only: input + 3 images
│
├── .claude/                       # Configuration
│   ├── .env                       # API keys (NEVER commit — gitignored)
│   └── .env.example               # Template — copy to .env and fill in keys
│
├── references/
│   └── inputs/                    # DROP RESTAURANT PHOTOS HERE
│                                  # This is where all input food photos go.
│                                  # The engine reads from this folder or from Airtable.
│
├── data/                          # Client registry + usage tracking
│   └── clients.json               # Auto-created by client_manager.py
│
├── outputs/                       # Local output storage (optional)
│                                  # Downloaded generated images/videos for review
│
├── tools/                         # Core modules (the engine)
│   ├── config.py                  # Loads API keys from .env, cost constants, model defaults
│   ├── food_prompts.py            # ALL prompt templates — images, videos, dish actions, cuisines
│   ├── airtable.py                # Airtable CRUD — reads/writes to "Leads" table
│   ├── quality_gate.py            # 3-gate Gemini vision quality scoring
│   ├── client_manager.py          # Client CRUD, tier quotas, monthly usage tracking
│   ├── social_post.py             # Ayrshare social media posting (IG, TikTok, FB, GMB)
│   └── providers/                 # Provider abstraction layer
│       ├── google.py              # Google AI Studio (images + Veo 3.1)
│       ├── kie.py                 # Kie AI (Kling/Sora videos + file hosting)
│       └── wavespeed.py           # WaveSpeed AI (backup video provider)
│
├── engine.py                      # MAIN ENGINE — image gen, video gen, orchestration
├── setup.py                       # One-time setup — verify creds + create Airtable table
├── mcp_server.py                  # Social media MCP server for AI agents
└── README.md                      # This file
```

### What each folder is for

| Folder | Purpose | Who uses it |
|--------|---------|-------------|
| `examples/` | **Approved sample outputs.** Input photos + generated images + videos. See what the engine produces. | Reference for the team |
| `.claude/` | API keys and config. `.env` has all secrets — never committed to git. | Setup only |
| `references/inputs/` | **Drop restaurant food photos here.** The engine picks them up as input images. | You / the team |
| `data/` | Stores `clients.json` — client registry with tier, quota, and usage data. Auto-created. | Engine (automatic) |
| `outputs/` | Optional local folder for reviewing generated images/videos before uploading. | You / the team |
| `tools/` | All the Python modules. `food_prompts.py` is the most important file. | Engine code |
| `tools/providers/` | Multi-provider abstraction — Google, Kie, WaveSpeed. Engine routes to the right one. | Engine code |

---

## Setup

### 1. Install dependencies

```bash
cd cravemode
pip install requests python-dotenv
```

### 2. Configure API keys

```bash
cp .claude/.env.example .claude/.env
# Then edit .claude/.env with your actual keys
```

| Key | Get it from | Used for |
|-----|-------------|----------|
| `GOOGLE_API_KEY` | [AI Studio](https://aistudio.google.com/apikey) | Image generation (Nano Banana Pro) |
| `KIE_API_KEY` | [Kie.ai](https://kie.ai/api-key) | Video generation (Kling 3.0) + file hosting |
| `AIRTABLE_API_KEY` | [Airtable](https://airtable.com/create/tokens) | Data hub (needs `data.records:read/write`) |
| `AIRTABLE_BASE_ID` | Airtable base URL | The `appXXX` from your base URL |
| `WAVESPEED_API_KEY` | [WaveSpeed](https://wavespeed.ai) | Optional backup video provider |

### 3. Verify everything works

```bash
python setup.py
```

---

## How Image Generation Works

### The 3 Images

Every input photo produces 3 distinct images that look like they came from the **same photoshoot**:

```
Input Photo (restaurant's phone pic)
        │
        ▼
┌───────────────────────────────────────────────┐
│  IMAGE 1: Hero Shot (45° angle)               │
│                                               │
│  What happens:                                │
│  • Original background is REMOVED entirely    │
│  • Dish placed on cuisine-matched surface     │
│    (e.g., colorful tile for Mexican)          │
│  • Dark moody background, single key light    │
│  • Saturation cranked 2x — reds are DEEP,     │
│    greens are VIVID                           │
│  • Shot at 45° hero angle, f/2.8, 50mm lens  │
│  • Dish fills 70% of frame                    │
│                                               │
│  Prompt: build_enhancement_prompt("mexican")  │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│  IMAGE 2: Overhead (90° flat lay)             │
│                                               │
│  What happens:                                │
│  • SAME surface, SAME lighting, SAME mood     │
│  • Camera moves directly above (bird's eye)   │
│  • Looking straight down at the dish          │
│  • Must look like the same photoshoot         │
│                                               │
│  Prompt: build_alternate_angle_prompt("mex")  │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│  IMAGE 3: Close-Up (macro detail)             │
│                                               │
│  What happens:                                │
│  • SAME surface, SAME lighting, SAME mood     │
│  • Zooms in tight on the best-looking part    │
│  • 90% frame fill — just texture and detail   │
│  • f/2.0, extremely shallow depth of field    │
│  • Only the closest part is sharp, rest is    │
│    creamy bokeh                               │
│                                               │
│  Prompt: build_closeup_prompt("mexican")      │
└───────────────────────────────────────────────┘
```

### How to generate images

```python
import sys; sys.path.insert(0, '.')
from cravemode.engine import _generate_image
from cravemode.tools.food_prompts import (
    build_enhancement_prompt,
    build_alternate_angle_prompt,
    build_closeup_prompt,
)

cuisine = "mexican"  # or italian, asian, american, bbq, seafood, bakery, default
photo = "references/inputs/tacos.jpg"

# Image 1: Hero shot
url1 = _generate_image(build_enhancement_prompt(cuisine), reference_paths=[photo])

# Image 2: Overhead
url2 = _generate_image(build_alternate_angle_prompt(cuisine), reference_paths=[photo])

# Image 3: Close-up
url3 = _generate_image(build_closeup_prompt(cuisine), reference_paths=[photo])
```

### What the model does vs. doesn't do

| Does | Does NOT |
|------|----------|
| Removes the original background | Change the food itself |
| Places dish on premium surface | Add food items not in the photo |
| Adds cinematic side lighting | Add utensils, hands, drinks |
| Cranks color saturation 2x | Add steam, smoke, or heat haze |
| Applies shallow depth of field | Add cheese pulls to food without cheese |

### Using the batch engine (Airtable-connected)

```python
from cravemode.engine import CraveModeEngine

engine = CraveModeEngine()
results = engine.generate_images()  # Processes all Status="Create" records
# Cost: ~$0.13/image via Google AI Studio
```

---

## How Video Generation Works

### The 3 Videos

Each video is **5 seconds**, **static camera** (no movement), with the generated image as the start frame:

```
Image 1 (Hero Shot)
        │
        ▼
┌───────────────────────────────────────────────┐
│  VIDEO 1: Action (scroll-stopping hook)       │
│                                               │
│  What happens:                                │
│  • Camera is LOCKED, static tripod shot       │
│  • Dish sits beautifully plated for 1 second  │
│  • Then a DISH-SPECIFIC action happens:       │
│    - Tacos → cilantro/onion scattered on top  │
│    - Steak → knife slices revealing interior  │
│    - Pizza → slice pulled with cheese stretch │
│    - Burger → cut in half, halves fall apart  │
│  • Slow motion, ASMR-like                     │
│  • Black gloves on all hands                  │
│                                               │
│  Prompt: build_action_video_prompt("tacos")   │
│  Start frame: Image 1 (hero shot)             │
└───────────────────────────────────────────────┘

Image 3 (Close-Up)
        │
        ▼
┌───────────────────────────────────────────────┐
│  VIDEO 2: Interact (someone eating it)        │
│                                               │
│  What happens:                                │
│  • Close-up of the dish, camera LOCKED        │
│  • A person INTERACTS with the food:          │
│    - Tacos → picks one up, tilts to show      │
│      fillings, takes a bite                   │
│    - Steak → fork lifts a cut piece showing   │
│      pink interior                            │
│    - Pizza → slice lifted, cheese dripping    │
│    - Pasta → fork twirls perfect noodle swirl │
│  • Natural, appetizing — how real people eat  │
│  • Black gloves on all hands                  │
│                                               │
│  Prompt: build_interact_video_prompt("tacos") │
│  Start frame: Image 3 (close-up)             │
└───────────────────────────────────────────────┘

Image 1 (Hero Shot)
        │
        ▼
┌───────────────────────────────────────────────┐
│  VIDEO 3: Plating Build (assembly)            │
│                                               │
│  What happens:                                │
│  • Overhead camera looking straight down      │
│  • Empty surface → dish assembled piece by    │
│    piece by gloved hands from the edges       │
│  • Base first, then main element, then        │
│    toppings, garnishes, final touches         │
│  • Each addition is a satisfying moment       │
│  • Final frame = the complete hero shot       │
│  • Works for ALL dish types (universal)       │
│                                               │
│  Prompt: build_plating_build_video_prompt()   │
│  Start frame: Image 1 (hero shot)             │
└───────────────────────────────────────────────┘
```

### How to generate videos

```python
import sys; sys.path.insert(0, '.')
from cravemode.engine import _submit_kie_video, _poll_kie_video
from cravemode.tools.food_prompts import (
    build_action_video_prompt,
    build_interact_video_prompt,
    build_plating_build_video_prompt,
)

dish = "street tacos"
hero_image_url = "https://..."   # Image 1 URL from Airtable
closeup_image_url = "https://..."  # Image 3 URL from Airtable

# Video 1: Action (uses hero image as start frame)
task1 = _submit_kie_video(build_action_video_prompt(dish), hero_image_url)
video1 = _poll_kie_video(task1)  # Polls every 10s, ~2-5 min

# Video 2: Interact (uses close-up image as start frame)
task2 = _submit_kie_video(build_interact_video_prompt(dish), closeup_image_url)
video2 = _poll_kie_video(task2)

# Video 3: Plating Build (uses hero image as start frame)
task3 = _submit_kie_video(build_plating_build_video_prompt(dish), hero_image_url)
video3 = _poll_kie_video(task3)
```

### Video generation details

| Parameter | Value |
|-----------|-------|
| **Provider** | Kie AI → Kling 3.0 |
| **Duration** | 5 seconds |
| **Mode** | Pro (highest quality) |
| **Sound** | Enabled (native audio) |
| **Cost** | ~$0.30 per video |
| **Wait time** | ~2-5 minutes per video |
| **Start frame** | Generated image (hero or close-up) |

---

## Dish-Aware Video Actions

The engine maps dish keywords to natural, contextually correct actions. No sauce pours on tacos. No knife cuts on soup.

| Dish Type | Video 1 (Action) | Video 2 (Interact) |
|-----------|-------------------|---------------------|
| **Taco** | Cilantro/onion scatter, lime wedge placed | Pick up taco, tilt to show fillings, bite |
| **Burger** | Knife cuts in half, halves fall apart | Press down → cheese ooze, lift bun |
| **Steak** | Knife slice → medium-rare interior reveal | Fork lifts cut piece showing pink inside |
| **Pasta** | Fork twirl → slow noodle lift with sauce | Parmesan grated from above, fork twirl |
| **Pizza** | Pull slice → cheese stretch | Lift slice, tilt to show toppings |
| **Sushi** | Soy sauce pour, chopstick dip | Chopstick lift showing fish/rice layers |
| **Noodle** | Chopstick lift → noodle cascade | Chopstick pickup with meat, broth drip |
| **Soup** | Spoon lift → broth pour back | Stir revealing hidden ingredients |
| **Wing** | Dip into sauce, pull out coated | Pull apart showing juicy meat inside |
| **Fried** | Break crispy exterior → juicy interior | Dip into sauce showing crispy coating |
| **Rib/BBQ** | Basting brush paints sauce | Pull apart / knife slice → smoke ring |
| **Cake** | Knife slice → layer reveal | Fork cuts tip showing cross-section |
| **Dessert** | Sauce/chocolate drizzle from above | Spoon cracks through top layer |
| **Seafood** | Lemon squeeze + herb sprinkle | Fork flakes fish apart |
| **Salad** | Dressing drizzle from above | Tongs toss mixing dressing |
| **Burrito** | Diagonal knife cut → cross-section | Pick up and pull apart at cut |
| **Bowl** | Toppings added one by one from above | Spoon scoop mixing layers |
| **Default** | Garnish/finishing touch from above | Natural utensil interaction |

Video 3 (Plating Build) is **universal** — works for all dish types.

The dish detection works by keyword matching. If the restaurant name or dish name contains the keyword (e.g., "street **taco**s" matches `taco`), it uses that action set. Otherwise it falls back to the `default` actions.

---

## Cuisine Profiles

Each cuisine gets a matching surface and lighting treatment for the images.

| Cuisine | Surface | Mood |
|---------|---------|------|
| `italian` | Rustic wood / marble | Warm golden candlelit |
| `mexican` | Colorful tile / weathered wood | Warm vibrant sunlight |
| `asian` | Dark slate / bamboo mat | Moody dramatic spotlit |
| `american` | Butcher block / white plate | Bright clean overhead |
| `seafood` | Weathered wood / ice bed | Cool blue + warm highlight |
| `bbq` | Dark wood / cast iron | Warm amber smoky |
| `bakery` | Marble / rustic wood with flour | Soft morning light |
| `default` | Clean modern surface | Bright professional |

Pass the cuisine key to image prompts:
```python
build_enhancement_prompt("italian")    # → marble surface, warm golden light
build_enhancement_prompt("bbq")        # → cast iron, warm amber
build_enhancement_prompt()             # → defaults to "default"
```

---

## Prompt Rules (Non-Negotiable)

These are baked into every prompt automatically. Don't remove them.

### Image Rules
1. **ONLY THE FOOD** — no utensils, props, hands, drinks
2. **NO HALLUCINATIONS** — input image is truth, never invent food items
3. **$1,500 FOOD STYLING** — dark moody background, premium surface, isolated dish
4. **NO STEAM** — never add steam, smoke, or heat haze
5. **NEVER add cheese pulls** or stretchy textures to food that doesn't have them

### Video Rules
1. **BLACK GLOVES** — all hands touching food MUST wear black food-safe gloves. No bare hands.
2. **STATIC CAMERA** — camera never moves, only gloved hands and food move
3. **NO STEAM, NO SMOKE** — keep it clean
4. **DISH-AWARE ACTIONS** — each food type gets contextually correct actions
5. **PHYSICALLY REALISTIC** — meat has natural fibers (not stretchy like cheese)

---

## Costs

| Asset | Provider | Model | Cost per unit |
|-------|----------|-------|---------------|
| Image | Google AI Studio | Nano Banana Pro | ~$0.13 |
| Image | Kie AI | Nano Banana Pro | ~$0.09 |
| Video | Kie AI | Kling 3.0 Pro | ~$0.30 |
| Video | WaveSpeed | Kling 3.0 Pro | ~$0.30 |
| Video | Google AI Studio | Veo 3.1 | ~$0.50 |

**Per restaurant (3 images + 3 videos):** ~$1.29 (Google images + Kie videos)

---

## Airtable Schema

Table name: **Leads**

| Field | Type | What goes in it |
|-------|------|-----------------|
| `Name` | Text | Restaurant name |
| `Category` | Text | Cuisine type |
| `Status` | Select | Create / Done / Skip |
| `input_image` | Attachment | Original phone photo |
| `Prompt` | Long Text | Image enhancement prompt |
| `image_1` | Attachment | Generated Image 1 (hero 45°) |
| `image_2` | Attachment | Generated Image 2 (overhead) |
| `image_3` | Attachment | Generated Image 3 (close-up) |
| `transition_prompt` | Long Text | Video prompt |
| `video` | Attachment | Generated video |

---

## Key Files Reference

### `tools/food_prompts.py` — The Brain

This is where all prompt templates live. If you need to change how images or videos look, edit this file.

| What | Function | Takes |
|------|----------|-------|
| Image 1 prompt | `build_enhancement_prompt(cuisine)` | Cuisine key (e.g., "mexican") |
| Image 2 prompt | `build_alternate_angle_prompt(cuisine)` | Cuisine key |
| Image 3 prompt | `build_closeup_prompt(cuisine)` | Cuisine key |
| Video 1 prompt | `build_action_video_prompt(dish_name)` | Dish name (e.g., "street tacos") |
| Video 2 prompt | `build_interact_video_prompt(dish_name)` | Dish name |
| Video 3 prompt | `build_plating_build_video_prompt(dish_name)` | Dish name |
| Dish → action map | `_DISH_ACTIONS` | Dictionary (15+ entries) |
| Cuisine → surface | `CUISINE_STYLES` | Dictionary (8 entries) |
| Image rules | `_STRICT_RULES` | String constant (auto-injected) |

### `engine.py` — The Runner

| What | Function | Returns |
|------|----------|---------|
| Generate image | `_generate_image(prompt, reference_paths)` | Hosted image URL |
| Submit video | `_submit_kie_video(prompt, image_url)` | Task ID |
| Poll video | `_poll_kie_video(task_id)` | Video URL |
| Batch images | `CraveModeEngine().generate_images()` | List of results |
| Batch videos | `CraveModeEngine().generate_videos()` | List of results |

### `tools/config.py` — API Keys + Constants

| What | Variable |
|------|----------|
| Google key | `GOOGLE_API_KEY` |
| Kie key | `KIE_API_KEY` |
| Airtable key | `AIRTABLE_API_KEY` |
| Airtable base | `AIRTABLE_BASE_ID` |
| Cost lookup | `get_cost(model, provider)` |

---

## Quick Reference

```python
import sys; sys.path.insert(0, '.')

# Image prompts
from cravemode.tools.food_prompts import (
    build_enhancement_prompt,         # Image 1 — 45° hero
    build_alternate_angle_prompt,     # Image 2 — overhead
    build_closeup_prompt,             # Image 3 — macro close-up
    build_action_video_prompt,        # Video 1 — dish action
    build_interact_video_prompt,      # Video 2 — eating interaction
    build_plating_build_video_prompt, # Video 3 — assembly build
    CUISINE_STYLES,                   # 8 cuisine profiles
)

# Engine
from cravemode.engine import (
    _generate_image,     # prompt + reference_paths → hosted URL
    _submit_kie_video,   # prompt + image_url → task_id
    _poll_kie_video,     # task_id → video_url (~2-5 min)
    CraveModeEngine,     # Full orchestrator class
)

# Airtable
from cravemode.tools.airtable import (
    get_pending_images,  # Records with Status="Create"
    update_record,       # Update any record by ID
)

# Config
from cravemode.tools.config import (
    GOOGLE_API_KEY,
    KIE_API_KEY,
    get_cost,            # get_cost("nano-banana-pro", "google") → 0.13
)
```
