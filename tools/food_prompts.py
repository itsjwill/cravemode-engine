"""
CraveMode Food Prompt Templates — The Cane's Menu.

5 fixed products. No substitutions. No freestyle.
Every restaurant gets the same premium treatment.

IMPORTANT RULES FOR ALL PROMPTS:
- ONLY enhance the food that exists in the input image
- NEVER add food items, drinks, garnishes, or elements not in the original
- NEVER change the dish — same food, same plating, just elevated quality
- Reference the input image explicitly so the model preserves the actual dish
- The input image IS the dish. Don't invent a new one.

Products:
1. Hero Shot — The signature dish, $1,000 food shoot quality
2. Menu Strip — 4-6 items in a horizontal layout
3. Sizzle Reel — Short video of food in action (steam, pour, sizzle)
4. Seasonal Promo — Holiday/seasonal themed content
5. Delivery Listing — Optimized for DoorDash/UberEats/Grubhub
"""


# --- Product Definitions (Cane's Menu) ---

PRODUCTS = {
    "hero_shot": {
        "name": "Hero Shot",
        "description": "Signature dish elevated to $1,000 commercial shoot quality",
        "type": "image",
        "aspect_ratio": "4:5",
        "variations": 2,
    },
    "menu_strip": {
        "name": "Menu Strip",
        "description": "4-6 items in a clean horizontal layout",
        "type": "image",
        "aspect_ratio": "16:9",
        "variations": 2,
    },
    "sizzle_reel": {
        "name": "Sizzle Reel",
        "description": "Short video of food in action — steam, pour, sizzle, plating",
        "type": "video",
        "aspect_ratio": "9:16",
        "duration": "6",
        "variations": 2,
    },
    "seasonal_promo": {
        "name": "Seasonal Promo",
        "description": "Holiday or seasonal themed content",
        "type": "image",
        "aspect_ratio": "1:1",
        "variations": 2,
    },
    "delivery_listing": {
        "name": "Delivery Listing",
        "description": "Optimized for DoorDash, UberEats, Grubhub listings",
        "type": "image",
        "aspect_ratio": "1:1",
        "variations": 2,
    },
}


# --- Tier Definitions ---

TIERS = {
    "starter": {
        "name": "Starter",
        "price": 297,
        "products": ["hero_shot", "menu_strip", "delivery_listing"],
        "images_per_month": 15,
        "videos_per_month": 3,
    },
    "growth": {
        "name": "Growth",
        "price": 597,
        "products": ["hero_shot", "menu_strip", "sizzle_reel", "delivery_listing"],
        "images_per_month": 30,
        "videos_per_month": 8,
    },
    "premium": {
        "name": "Premium",
        "price": 997,
        "products": ["hero_shot", "menu_strip", "sizzle_reel", "seasonal_promo", "delivery_listing"],
        "images_per_month": 60,
        "videos_per_month": 15,
    },
}


# --- Current Season Detection ---

def get_current_season():
    """Detect current season for seasonal promo templates."""
    from datetime import datetime
    month = datetime.now().month
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "fall"


SEASONAL_THEMES = {
    "winter": {
        "holidays": ["Christmas", "New Year's", "Valentine's Day", "Super Bowl"],
        "mood": "warm, cozy, festive",
        "colors": "deep reds, golds, warm amber lighting",
        "props": "candles, pine branches, snow-dusted surfaces, fairy lights",
    },
    "spring": {
        "holidays": ["Easter", "Mother's Day", "Cinco de Mayo"],
        "mood": "fresh, bright, renewal",
        "colors": "pastels, fresh greens, soft pinks",
        "props": "flowers, herbs, garden elements, natural light",
    },
    "summer": {
        "holidays": ["4th of July", "Father's Day", "Labor Day"],
        "mood": "vibrant, outdoor, refreshing",
        "colors": "bright blues, sunset oranges, tropical greens",
        "props": "outdoor settings, grills, fresh fruit, ice, condensation",
    },
    "fall": {
        "holidays": ["Halloween", "Thanksgiving", "Football Season"],
        "mood": "warm, rustic, harvest",
        "colors": "burnt orange, deep burgundy, golden brown",
        "props": "pumpkins, autumn leaves, wooden surfaces, warm lighting",
    },
}


# --- Cuisine Style Profiles ---

CUISINE_STYLES = {
    "italian": {
        "surface": "rustic wood table or marble countertop",
        "props": "olive oil drizzle, fresh basil, parmesan shavings, checkered cloth",
        "lighting": "warm golden, candlelit trattoria ambiance",
        "plating": "family-style generous portions, slightly imperfect artisan plating",
    },
    "mexican": {
        "surface": "colorful tile or weathered wood",
        "props": "lime wedges, cilantro, colorful ceramics, cast iron",
        "lighting": "warm natural sunlight, vibrant and lively",
        "plating": "generous, overflowing, colorful layers visible",
    },
    "asian": {
        "surface": "dark slate or bamboo mat",
        "props": "chopsticks, small dipping bowls, steam rising, garnish",
        "lighting": "moody dramatic, focused spot lighting",
        "plating": "precise, architectural, negative space, garnish as art",
    },
    "american": {
        "surface": "butcher block or clean white plate",
        "props": "craft paper, pickles, coleslaw sides, branded wrapper",
        "lighting": "bright, clean, appetizing overhead",
        "plating": "stacked high, cheese pull visible, juices dripping",
    },
    "seafood": {
        "surface": "weathered wood plank or ice bed",
        "props": "lemon wedges, sea salt flakes, crushed ice, seaweed accent",
        "lighting": "cool blue undertones with warm highlight on food",
        "plating": "fresh, glistening, dewy, raw ingredients visible",
    },
    "bbq": {
        "surface": "dark wood or cast iron",
        "props": "smoke wisps, charred edges, sauce drip, butcher paper",
        "lighting": "warm amber, slightly smoky atmosphere",
        "plating": "rustic, piled high, bark visible, sides family-style",
    },
    "bakery": {
        "surface": "marble slab or rustic wood with flour dusting",
        "props": "powdered sugar, fresh berries, cream, cooling rack",
        "lighting": "soft morning light, warm and inviting",
        "plating": "artful arrangement, crumbs scattered naturally",
    },
    "default": {
        "surface": "clean modern surface",
        "props": "minimal garnish, clean napkin, simple flatware",
        "lighting": "bright, even, professional food photography lighting",
        "plating": "clean, centered, appetizing presentation",
    },
}


# --- Core Prompt Rule (injected into every prompt) ---

_STRICT_RULES = (
    "FOOD RULES: The dish itself must be IDENTICAL to the input — same food items, same toppings, "
    "same garnishes, same plating. Do NOT invent, add, or remove any food. "
    "NEVER add melted cheese, cheese pulls, or stretchy textures to food that doesn't have them. "
    "Meat must look like meat — natural muscle fibers, not stretchy like cheese. "
    "No text, no watermarks, no logos. "
    "PRESENTATION RULES: You MUST dramatically transform the presentation. Remove the original "
    "background entirely. Place the dish on a clean, premium surface appropriate to the cuisine. "
    "Remove all clutter — no plastic cups, no napkins, no utensils, no menus, no other people's food. "
    "ONLY THE DISH stays. The background must be dark, moody, and out of focus. "
    "This is a $1,500 food styling shoot — the dish is isolated, lit perfectly, and the star of the frame."
)


# --- Image Prompt Builders ---

def build_hero_shot_prompt(dish_name, cuisine="default", extra_notes=""):
    """Build a Hero Shot prompt — the signature dish, $1,000 food shoot quality."""
    style = CUISINE_STYLES.get(cuisine, CUISINE_STYLES["default"])

    prompt = (
        f"4:5. Recreate the EXACT dish from the input image as a $1,000 professional food photograph. "
        f"The dish is {dish_name}. {_STRICT_RULES} "
        f"Cinematic soft lighting with beautiful highlights catching every texture — "
        f"{style['lighting']}. "
        f"Rich, saturated colors. Visible steam or heat haze rising from hot elements. "
        f"Shallow depth of field, f/2.8, sharp focus on the food with creamy bokeh background. "
        f"Surface: {style['surface']}. "
        f"Subtle props just out of focus: {style['props']}. "
        f"Camera angle: slightly elevated 30-40 degrees, close enough to see every grain and glaze. "
        f"Shot on Sony A7IV with 90mm macro lens. "
        f"The kind of photo that stops someone mid-scroll and makes them immediately hungry. "
        f"Using input image 1 as the EXACT reference for what food to show."
    )

    if extra_notes:
        prompt += f" {extra_notes}"

    return prompt


def build_menu_strip_prompt(items, cuisine="default", extra_notes=""):
    """Build a Menu Strip prompt — 4-6 items in a clean horizontal layout."""
    style = CUISINE_STYLES.get(cuisine, CUISINE_STYLES["default"])
    items_str = ", ".join(items[:6])
    count = len(items[:6])

    prompt = (
        f"16:9. Overhead flat-lay food photography of {count} dishes arranged in a clean horizontal row: "
        f"{items_str}. {_STRICT_RULES} "
        f"Bird's eye view, perfectly centered composition, equal spacing. "
        f"Each dish on matching plates against {style['surface']}. "
        f"Bright, even, editorial lighting — {style['lighting']}. "
        f"Every dish clearly identifiable, vibrant colors, sharp details. "
        f"Clean negative space between items. Menu-board ready. "
        f"Shot from directly above at exactly 90 degrees. "
        f"Professional food styling, Bon Appetit magazine quality. "
        f"Using input image 1 for food reference."
    )

    if extra_notes:
        prompt += f" {extra_notes}"

    return prompt


def build_delivery_listing_prompt(dish_name, cuisine="default", extra_notes=""):
    """Build a Delivery Listing prompt — DoorDash/UberEats/Grubhub optimized."""

    prompt = (
        f"1:1. Clean, bright, appetizing photo of {dish_name} for food delivery app. "
        f"{_STRICT_RULES} "
        f"Pure white or very light grey seamless background. "
        f"Slightly overhead 45-degree angle showing the full dish. "
        f"Bright, shadowless, even lighting from all sides. "
        f"Hyper-saturated colors — make the food pop off the screen. "
        f"Ultra-sharp focus across entire dish. High contrast. "
        f"Zero props, zero distractions — just the food centered in frame. "
        f"Dish fills exactly 75% of the square frame. "
        f"Clean plate edges, no crumbs, no drips outside the plate. "
        f"Looks like it could be on the DoorDash featured carousel right now. "
        f"Using input image 1 as the EXACT dish to show."
    )

    if extra_notes:
        prompt += f" {extra_notes}"

    return prompt


def build_seasonal_promo_prompt(dish_name, cuisine="default", season=None, holiday=None, extra_notes=""):
    """Build a Seasonal Promo prompt — holiday/seasonal themed content."""
    season = season or get_current_season()
    theme = SEASONAL_THEMES[season]
    holiday = holiday or theme["holidays"][0]
    style = CUISINE_STYLES.get(cuisine, CUISINE_STYLES["default"])

    prompt = (
        f"1:1. Stunning {holiday} themed food photography of {dish_name}. "
        f"{_STRICT_RULES} "
        f"The EXACT dish from the input image is the hero, surrounded by subtle {holiday} elements. "
        f"Mood: {theme['mood']}. Color palette: {theme['colors']}. "
        f"Seasonal styling: {theme['props']} arranged tastefully around the dish. "
        f"Surface: {style['surface']}. "
        f"Warm, inviting, Instagram-worthy composition. "
        f"Shot at a low 25-degree angle to make the food heroic. "
        f"Soft bokeh background with festive elements out of focus. "
        f"The photo that makes someone tag their friend and say 'we need to go here.' "
        f"Using input image 1 as the EXACT food reference."
    )

    if extra_notes:
        prompt += f" {extra_notes}"

    return prompt


# --- Video Prompt Builders ---

def build_sizzle_reel_prompt(dish_name, cuisine="default", action="plating", extra_notes=""):
    """Build a Sizzle Reel video prompt — ASMR food content for social."""
    style = CUISINE_STYLES.get(cuisine, CUISINE_STYLES["default"])

    actions = {
        "plating": (
            f"Extreme close-up of {dish_name} being plated. A chef's hands carefully place "
            f"each element. The final garnish drops in slow motion. Steam curls upward. "
            f"Camera holds on the finished plate for a beat."
        ),
        "cooking": (
            f"Tight shot of {dish_name} hitting a screaming hot surface. Immediate sizzle, "
            f"oil spatters, flames kiss the edges. Camera slowly pushes in through the smoke "
            f"to reveal the caramelized crust forming. Satisfying crackle sounds."
        ),
        "pouring": (
            f"Thick, glossy sauce slowly poured over {dish_name} in extreme close-up. "
            f"The sauce cascades over edges, pools in crevices. Steam rises on contact. "
            f"Camera catches the moment the pour stops with a perfect drip."
        ),
        "slicing": (
            f"A sharp knife slides through {dish_name} in one clean motion. The cross-section "
            f"reveals perfect layers, juices flow out. Camera lingers on the satisfying "
            f"interior texture. The two halves slowly separate."
        ),
        "steam": (
            f"Macro close-up of {dish_name} with delicate steam wisps rising from the surface. "
            f"Camera slowly orbits the dish at table level. Every texture, every grain of salt, "
            f"every bubble of cheese visible in sharp detail."
        ),
    }

    action_desc = actions.get(action, actions["plating"])

    prompt = (
        f"{action_desc} "
        f"Cinematic food videography shot on RED Komodo. Shallow depth of field, anamorphic flares. "
        f"{style['lighting']}. Surface: {style['surface']}. "
        f"Pure ASMR — natural cooking sounds only, no music, no voice. "
        f"Slow motion 120fps moments for the most satisfying details. "
        f"TikTok viral food content energy. Makes viewer's mouth water instantly."
    )

    if extra_notes:
        prompt += f" {extra_notes}"

    return prompt


# --- The Universal Enhancement Prompt (for existing Airtable records) ---

def build_enhancement_prompt(cuisine="default"):
    """
    The go-to prompt for enhancing an existing food photo from the Airtable.
    This is what gets used for the 18 'Create' status records (Image 1).
    """
    style = CUISINE_STYLES.get(cuisine, CUISINE_STYLES["default"])
    return (
        f"Recreate this EXACT dish as a stunning $1,500 commercial food photograph. "
        f"{_STRICT_RULES} "
        f"LIGHTING: Cinematic single key light from the side, strong highlights catching every "
        f"texture and glaze. Deep shadows. Warm golden color temperature. The food GLOWS. "
        f"SURFACE: Place the dish on {style['surface']}. Nothing else on the surface. "
        f"BACKGROUND: Pitch dark or deep moody blur. Total isolation. The dish floats in light. "
        f"COLOR: Crank saturation — reds are DEEP red, greens are VIVID, golden tones are RICH. "
        f"Every color should be 2x more vibrant than the input photo. "
        f"TEXTURE: Razor sharp. Every grain of rice, every herb leaf, every char mark is crisp. "
        f"Shallow depth of field — f/2.8, 50mm lens. "
        f"NO STEAM — do not add any steam, smoke, or heat haze. Keep it clean. "
        f"FRAMING: The dish fills 70% of the frame. Shot at 45° hero angle. "
        f"This must look like a Bon Appetit cover that makes people stop scrolling and feel HUNGRY. "
        f"Using input image 1 as the EXACT dish — transform the presentation, not the food."
    )


def build_alternate_angle_prompt(cuisine="default"):
    """
    Image 2 prompt — same photoshoot setup, different camera angle.
    Must be visually consistent with Image 1 (same surface, same presentation).
    """
    style = CUISINE_STYLES.get(cuisine, CUISINE_STYLES["default"])
    return (
        f"Recreate this EXACT dish as a $1,500 commercial food photograph from a different angle. "
        f"{_STRICT_RULES} "
        f"CRITICAL: This must look like it was shot in the SAME photoshoot as the previous image. "
        f"Same surface ({style['surface']}), same dark moody background, same lighting style. "
        f"ANGLE: Shoot from direct overhead (90° flat lay) looking straight down at the dish. "
        f"Same cinematic side lighting with strong highlights. Same warm golden color temperature. "
        f"Same color grade, same saturation level, same mood. "
        f"NO STEAM. Keep everything about the presentation identical — just move the camera above. "
        f"TEXTURE: Razor sharp. Shallow depth of field still applies. "
        f"Using input image 1 as the EXACT dish — same setup, overhead angle."
    )


def build_closeup_prompt(cuisine="default"):
    """
    Image 3 prompt — tight close-up detail of the most appetizing part.
    Same photoshoot as Images 1 and 2, just zoomed in.
    """
    style = CUISINE_STYLES.get(cuisine, CUISINE_STYLES["default"])
    return (
        f"Shoot a tight close-up of the most appetizing part of this EXACT dish. "
        f"{_STRICT_RULES} "
        f"CRITICAL: Same photoshoot as the hero shot — same surface ({style['surface']}), "
        f"same dark moody background, same warm cinematic side lighting. "
        f"FRAMING: Fill 90% of the frame with one section of the dish. Show the texture up close — "
        f"the char, the glaze, the layers, the ingredients piled together. "
        f"Extremely shallow depth of field — f/2.0. Only the closest part is tack sharp, "
        f"the rest falls into creamy bokeh. "
        f"NO STEAM. Same color grade and saturation as the hero shot. "
        f"This is the detail shot that makes someone zoom in and stare. "
        f"Using input image 1 as the EXACT food reference — same dish, just zoomed in tight."
    )


# --- Video Prompt Builders ---
# 3 action-based styles optimized for Instagram Reels / TikTok engagement.
# Research shows: action > camera movement. People stop scrolling for
# something HAPPENING to the food, not a camera moving around it.
# Optimal length: 7-15 seconds. First 3 seconds = the hook.
#
# CRITICAL: Prompts are DISH-AWARE. Each dish type gets actions that
# make sense for that food. No sauce pours on tacos, no knife cuts on soup.

# Maps dish keywords to natural actions
_DISH_ACTIONS = {
    # Tacos / Mexican
    "taco": {
        "action": "A gloved hand enters from above and scatters a generous pinch of fresh chopped cilantro "
                  "and finely diced white onion over the tacos. The pieces tumble and land across "
                  "the meat and toppings in slow motion. A few pieces bounce off the edges. "
                  "Then a visible lime WEDGE (bright green, triangular) is placed beside the tacos on the plate.",
        "interact": "A gloved hand picks up one taco from the plate, tilts it toward camera showing "
                    "all the fillings inside — the meat, the toppings, the layers visible from the side. "
                    "A bite is taken, revealing the cross-section.",
    },
    "burrito": {
        "action": "A knife slowly slices the burrito in half diagonally, revealing the perfect "
                  "cross-section — layers of rice, beans, meat, cheese, and toppings visible inside.",
        "interact": "The burrito is picked up and tilted to show the stuffed end, then slowly "
                    "pulled apart at the cut revealing all the layers inside.",
    },
    # Burgers
    "burger": {
        "action": "A knife slowly presses down through the center of the burger, cutting it in half. "
                  "The two halves fall apart revealing the layers — bun, patty, cheese, toppings.",
        "interact": "A gloved hand presses down on the burger slightly, melted cheese oozes from the sides. "
                    "Then lifts the top bun briefly revealing the stacked layers inside.",
    },
    # Steak / Meat
    "steak": {
        "action": "A knife slices slowly through the steak revealing a perfect medium-rare interior. "
                  "The meat fibers separate naturally, juices pool on the cutting surface. "
                  "The blade pulls away to show the pink gradient from crust to center.",
        "interact": "A fork pierces a cut piece, lifts it to show the pink interior glistening with juices. "
                    "The meat has a perfect sear on the outside, tender pink inside.",
    },
    # Pasta / Noodles
    "pasta": {
        "action": "A fork twirls into the pasta, slowly lifting a perfect swirl of noodles "
                  "with sauce clinging to every strand. The lift is slow and satisfying.",
        "interact": "Parmesan is grated from above, snowing down onto the pasta. "
                    "Then a fork twirls and lifts a perfect bite.",
    },
    "noodle": {
        "action": "Chopsticks lift a tangle of noodles high above the bowl, letting them cascade "
                  "back down slowly. Broth drips, noodles stretch and fall.",
        "interact": "Chopsticks pick up noodles with a piece of meat, lift to show the texture, "
                    "broth dripping back into the bowl.",
    },
    # Pizza
    "pizza": {
        "action": "A gloved hand slowly pulls a slice away from the pie — cheese stretches in long strings "
                  "between the slice and the rest. The pull is slow and dramatic.",
        "interact": "The slice is lifted, cheese dripping, tilted toward camera to show the toppings.",
    },
    # Sushi
    "sushi": {
        "action": "Soy sauce is slowly poured into a small dish beside the sushi. "
                  "Then chopsticks pick up one piece, dip it gently into the sauce.",
        "interact": "Chopsticks pick up a single piece, lift it to camera showing the layers of "
                    "fish, rice, and nori. A gentle dip into soy sauce.",
    },
    # Soup / Bowls
    "soup": {
        "action": "A spoon dips into the bowl and slowly lifts, revealing the broth and ingredients. "
                  "The liquid pours back down in a slow, satisfying stream.",
        "interact": "A ladle or spoon stirs slowly through the bowl, revealing hidden ingredients "
                    "rising to the surface.",
    },
    "bowl": {
        "action": "Toppings are added one by one from above — a drizzle of sauce, a sprinkle of seeds, "
                  "a handful of fresh herbs landing on top.",
        "interact": "A spoon scoops from the edge, mixing layers together, lifting to show the combination.",
    },
    # Salad
    "salad": {
        "action": "Dressing drizzles slowly from above, coating the leaves and toppings. "
                  "The pour catches the light beautifully.",
        "interact": "Tongs or forks toss the salad gently, mixing the dressing through, "
                    "lifting ingredients to show the variety.",
    },
    # Dessert / Cake / Pastry
    "cake": {
        "action": "A knife slices down through the cake, pulling away to reveal the layers inside — "
                  "frosting, sponge, filling, all perfectly stacked.",
        "interact": "A fork cuts the tip of a slice and lifts it, showing the cross-section of layers.",
    },
    "dessert": {
        "action": "A sauce or chocolate drizzle pours slowly over the dessert from above, "
                  "cascading over the edges and pooling on the plate.",
        "interact": "A spoon cracks through the top layer revealing what's inside.",
    },
    # Fried / Wings / Chicken
    "wing": {
        "action": "A gloved hand picks up a wing and dips it slowly into a thick sauce, "
                  "pulling it out coated and glistening.",
        "interact": "A wing is pulled apart with two gloved hands, showing the juicy meat inside. "
                    "The meat pulls away cleanly from the bone.",
    },
    "fried": {
        "action": "A gloved hand breaks the crispy exterior, revealing the juicy interior. "
                  "The crunch is visible — the breading cracks and separates.",
        "interact": "A piece is dipped into sauce, lifted showing the crispy texture coated in sauce.",
    },
    # Seafood
    "seafood": {
        "action": "A lemon wedge is squeezed over the seafood, juice dripping down. "
                  "Then a sprinkle of herbs from above.",
        "interact": "A fork flakes the fish apart slowly, revealing the tender interior.",
    },
    # BBQ / Ribs
    "rib": {
        "action": "Sauce is brushed slowly across the ribs with a basting brush, "
                  "coating every ridge and crevice. The glaze catches the light.",
        "interact": "Two gloved hands pull a rib apart from the rack, the meat separating from the bone "
                    "with natural muscle fibers — NOT stretchy like cheese.",
    },
    "bbq": {
        "action": "A basting brush paints thick BBQ sauce across the meat in slow, deliberate strokes.",
        "interact": "A knife slices through revealing a smoke ring and juicy pink interior.",
    },
    # Default fallback
    "default": {
        "action": "A garnish or finishing touch is added from above — a drizzle of sauce, "
                  "a sprinkle of herbs, or a squeeze of citrus. The final touch that completes the dish.",
        "interact": "A utensil interacts with the dish in the most natural way — cutting, lifting, "
                    "scooping, or pulling apart to reveal textures and layers inside.",
    },
}


def _get_dish_action(dish_name):
    """Match a dish name to its natural action set."""
    name_lower = dish_name.lower()
    for keyword, actions in _DISH_ACTIONS.items():
        if keyword == "default":
            continue
        if keyword in name_lower:
            return actions
    return _DISH_ACTIONS["default"]


def build_action_video_prompt(dish_name="the dish"):
    """
    Video 1: Natural Action — the scroll-stopping hook.
    Dish-aware: tacos get lime squeeze, steaks get sauce pour, etc.
    Uses Image 1 (hero) as start frame.
    """
    actions = _get_dish_action(dish_name)
    return (
        f"The camera is locked off, static, perfectly framed on {dish_name}. "
        f"The dish sits beautifully plated for 1 second, then: "
        f"{actions['action']} "
        f"The motion is slow, deliberate, satisfying. Almost ASMR-like. "
        f"Camera does NOT move. Static tripod shot. "
        f"Warm cinematic side lighting. Dark moody background. Shallow depth of field. "
        f"All textures physically realistic. No steam, no smoke. "
        f"HANDS: Any hands touching food MUST wear black food-safe gloves. No bare hands. "
        f"This is the first 3 seconds that stop someone mid-scroll."
    )


def build_interact_video_prompt(dish_name="the dish"):
    """
    Video 2: Natural Interaction — someone engaging with the dish.
    Dish-aware: tacos get picked up, pasta gets twirled, etc.
    Uses Image 3 (close-up) as start frame.
    """
    actions = _get_dish_action(dish_name)
    return (
        f"Close-up of {dish_name}. Camera is static. "
        f"{actions['interact']} "
        f"The interaction is natural and appetizing — the way a real person would eat this. "
        f"Camera stays LOCKED. Only gloved hands and food move. "
        f"Warm cinematic lighting. Dark moody background. Shallow depth of field. "
        f"All textures physically realistic — meat has natural fibers, not stretchy like cheese. "
        f"No steam, no smoke. "
        f"HANDS: Any hands touching food MUST wear black food-safe gloves. No bare hands. "
        f"This makes the viewer want to reach through the screen."
    )


def build_orbit_video_prompt(dish_name="the dish"):
    """
    Video 3: Cinematic Orbit — camera sweeps around the dish.
    Uses Image 1 (hero) as start frame.
    Works universally for all dish types.
    """
    return (
        f"Cinematic food video. The camera slowly orbits around {dish_name} in a smooth arc, "
        f"starting from one side and sweeping to the other. The camera is at a slight elevated angle. "
        f"As it moves, you see the dish from changing angles — the parallax reveals depth, "
        f"the toppings shift perspective, the textures catch light differently as the camera passes. "
        f"The orbit is slow, smooth, and continuous like a professional dolly on a curved track. "
        f"The dish stays centered while the world rotates around it. "
        f"Soft bright natural lighting. Clean surface. Shallow depth of field. "
        f"The background gently blurs and shifts as the camera moves, creating real cinematic depth. "
        f"NO zoom. NO push-in. The camera MOVES laterally around the food. "
        f"NO hands. NO interaction. NO steam. NO smoke. "
        f"Professional food cinematography. Elegant and appetizing."
    )


# Legacy aliases
def build_transition_video_prompt(dish_name="the dish"):
    return build_action_video_prompt(dish_name)

def build_sauce_pour_video_prompt(dish_name="the dish"):
    return build_action_video_prompt(dish_name)

def build_cut_reveal_video_prompt(dish_name="the dish"):
    return build_interact_video_prompt(dish_name)

def build_slow_reveal_video_prompt(dish_name="the dish"):
    return build_interact_video_prompt(dish_name)

def build_plating_build_video_prompt(dish_name="the dish"):
    return build_orbit_video_prompt(dish_name)

def build_sizzle_video_prompt(dish_name="the dish"):
    return build_action_video_prompt(dish_name)


# --- Batch Template Generator ---

def generate_content_plan(restaurant_name, dishes, cuisine="default", tier="starter"):
    """
    Generate a full content plan for a restaurant based on their tier.

    Args:
        restaurant_name: Name of the restaurant
        dishes: List of dish dicts [{"name": "...", "category": "appetizer|entree|dessert|drink"}]
        cuisine: Cuisine style key
        tier: Plan tier key from TIERS

    Returns:
        list of dicts ready for Airtable batch creation
    """
    plan_config = TIERS.get(tier, TIERS["starter"])
    records = []
    index = 1

    # Hero Shots — top dishes
    hero_dishes = dishes[:3] if tier == "starter" else dishes[:5]
    for dish in hero_dishes:
        records.append({
            "Index": index,
            "Ad Name": f"{restaurant_name} - Hero Shot - {dish['name']}",
            "Product": "Hero Shot",
            "Restaurant": restaurant_name,
            "Cuisine": cuisine,
            "Image Prompt": build_hero_shot_prompt(dish["name"], cuisine),
            "Image Model": "Nano Banana Pro",
            "Image Status": "Pending",
        })
        index += 1

    # Menu Strip — group items
    if "menu_strip" in plan_config["products"]:
        entrees = [d["name"] for d in dishes if d.get("category") == "entree"][:6]
        if not entrees:
            entrees = [d["name"] for d in dishes[:6]]
        records.append({
            "Index": index,
            "Ad Name": f"{restaurant_name} - Menu Strip",
            "Product": "Menu Strip",
            "Restaurant": restaurant_name,
            "Cuisine": cuisine,
            "Image Prompt": build_menu_strip_prompt(entrees, cuisine),
            "Image Model": "Nano Banana Pro",
            "Image Status": "Pending",
        })
        index += 1

    # Delivery Listings — all dishes for delivery apps
    if "delivery_listing" in plan_config["products"]:
        delivery_dishes = dishes[:5] if tier == "starter" else dishes[:10]
        for dish in delivery_dishes:
            records.append({
                "Index": index,
                "Ad Name": f"{restaurant_name} - Delivery - {dish['name']}",
                "Product": "Delivery Listing",
                "Restaurant": restaurant_name,
                "Cuisine": cuisine,
                "Image Prompt": build_delivery_listing_prompt(dish["name"], cuisine),
                "Image Model": "Nano Banana Pro",
                "Image Status": "Pending",
            })
            index += 1

    # Seasonal Promos
    if "seasonal_promo" in plan_config["products"]:
        season = get_current_season()
        promo_dish = dishes[0]
        records.append({
            "Index": index,
            "Ad Name": f"{restaurant_name} - {SEASONAL_THEMES[season]['holidays'][0]} Promo",
            "Product": "Seasonal Promo",
            "Restaurant": restaurant_name,
            "Cuisine": cuisine,
            "Image Prompt": build_seasonal_promo_prompt(promo_dish["name"], cuisine),
            "Image Model": "Nano Banana Pro",
            "Image Status": "Pending",
        })
        index += 1

    # Sizzle Reels
    if "sizzle_reel" in plan_config["products"]:
        sizzle_dishes = dishes[:2] if tier == "growth" else dishes[:4]
        actions = ["cooking", "plating", "pouring", "slicing"]
        for i, dish in enumerate(sizzle_dishes):
            action = actions[i % len(actions)]
            records.append({
                "Index": index,
                "Ad Name": f"{restaurant_name} - Sizzle - {dish['name']}",
                "Product": "Sizzle Reel",
                "Restaurant": restaurant_name,
                "Cuisine": cuisine,
                "Video Prompt": build_sizzle_reel_prompt(dish["name"], cuisine, action),
                "Video Model": "Veo 3.1",
                "Video Status": "Pending",
            })
            index += 1

    return records
