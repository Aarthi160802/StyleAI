"""
tools.py – StyleAI custom tool functions (called by the agent loop).

Tools:
  1. get_weather          – live weather for an event location + date
  2. get_fashion_news     – latest fashion / trend headlines
  3. get_outfit_images    – Unsplash outfit inspiration images
  4. get_color_palette    – derives a seasonal color palette
  5. get_dress_code_guide – returns dress-code rules for an event type
"""

import requests
import re
from datetime import datetime
from code.config import (
    OPENWEATHER_API_KEY, OPENWEATHER_BASE,
    NEWS_API_KEY, NEWS_API_BASE,
    PEXELS_API_KEY, PEXELS_BASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# Tool 1 – Weather
# ─────────────────────────────────────────────────────────────────────────────

def get_weather(city: str, date_str: str) -> dict:
    """
    Fetch weather for *city* on *date_str* (YYYY-MM-DD).
    Falls back to current weather when the date is beyond the free 5-day forecast.
    Returns a dict with keys: city, date, temp_c, feels_like_c, description,
    humidity_pct, wind_kph, advice.
    """
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY not set. Please add it to your .env file."}

    try:
        # Current weather (always available on free tier)
        url = f"{OPENWEATHER_BASE}/weather"
        resp = requests.get(url, params={
            "q":     city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        temp       = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        desc       = data["weather"][0]["description"].capitalize()
        humidity   = data["main"]["humidity"]
        wind_kph   = round(data["wind"]["speed"] * 3.6, 1)

        # Simple styling advice based on temperature
        if temp >= 30:
            advice = "Very hot – opt for light, breathable fabrics like linen or cotton."
        elif temp >= 22:
            advice = "Warm – light layers work great; avoid heavy materials."
        elif temp >= 15:
            advice = "Mild – a light jacket or cardigan is a good idea."
        elif temp >= 8:
            advice = "Cool – layering is key; mid-weight fabrics recommended."
        else:
            advice = "Cold – wear warm layers; consider a coat and thermal underlayer."

        return {
            "city":         city,
            "date":         date_str,
            "temp_c":       round(temp, 1),
            "feels_like_c": round(feels_like, 1),
            "description":  desc,
            "humidity_pct": humidity,
            "wind_kph":     wind_kph,
            "advice":       advice,
        }
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2 – Fashion News
# ─────────────────────────────────────────────────────────────────────────────

def get_fashion_news(query: str = "fashion trends 2026", max_articles: int = 5) -> dict:
    """
    Fetch the latest fashion & trend news headlines via NewsAPI.
    Returns a list of articles with title, source, url, publishedAt.
    """
    if not NEWS_API_KEY:
        return {"error": "NEWS_API_KEY not set. Please add it to your .env file."}

    try:
        url = f"{NEWS_API_BASE}/everything"
        resp = requests.get(url, params={
            "q":        query,
            "language": "en",
            "sortBy":   "publishedAt",
            "pageSize": max_articles,
            "apiKey":   NEWS_API_KEY,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for art in data.get("articles", []):
            articles.append({
                "title":       art.get("title", ""),
                "source":      art.get("source", {}).get("name", ""),
                "url":         art.get("url", ""),
                "publishedAt": art.get("publishedAt", ""),
                "description": art.get("description", ""),
            })
        return {"query": query, "articles": articles}
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3 – Outfit Inspiration Images (Pexels – free, no OAuth)
# ─────────────────────────────────────────────────────────────────────────────

def get_outfit_images(query: str, count: int = 4) -> dict:
    """
    Search Pexels for outfit inspiration images matching *query*.
    Falls back to Unsplash Source (no key needed) if PEXELS_API_KEY is unset.
    Returns a list of dicts: thumb_url, full_url, alt, photographer, height, width.
    """
    if not PEXELS_API_KEY:
        # Graceful fallback – Unsplash Source endpoint (no auth, no 401)
        images = [
            {
                "thumb_url":    f"https://source.unsplash.com/400x600/?{query.replace(' ', ',')}&sig={i}",
                "full_url":     f"https://source.unsplash.com/800x1200/?{query.replace(' ', ',')}&sig={i}",
                "alt":          f"{query} inspiration {i+1}",
                "photographer": "Unsplash",
                "height":       600,
                "width":        400,
            }
            for i in range(count)
        ]
        return {"query": query, "images": images, "note": "PEXELS_API_KEY not set – using Unsplash Source fallback"}

    try:
        resp = requests.get(
            f"{PEXELS_BASE}/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": count, "orientation": "portrait"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        images = []
        for photo in data.get("photos", []):
            images.append({
                "thumb_url":    photo["src"]["medium"],
                "full_url":     photo["src"]["large"],
                "alt":          photo.get("alt", query),
                "photographer": photo["photographer"],
                "height":       photo["height"],
                "width":        photo["width"],
            })
        return {"query": query, "images": images}
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Pinterest board helper – extract outfit item queries from Gemini output
# ─────────────────────────────────────────────────────────────────────────────

_FASHION_KW = [
    "dress", "gown", "skirt", "blouse", "shirt", "top", "pants", "trousers",
    "jeans", "jacket", "coat", "blazer", "suit", "saree", "lehenga", "kurta",
    "anarkali", "dupatta", "sherwani", "dhoti",
    "shoes", "heels", "sandals", "boots", "sneakers", "loafers", "flats", "mules",
    "bag", "clutch", "handbag", "purse", "tote",
    "jewellery", "jewelry", "necklace", "earrings", "bracelet", "watch",
    "scarf", "shawl", "stole", "jumpsuit", "romper", "co-ord", "cardigan",
    "outfit", "look", "ensemble",
]


def extract_outfit_queries(final_text: str, max_items: int = 8) -> list:
    """
    Parse Gemini's final recommendation and extract concise, image-search-ready
    queries for each outfit piece (max 5 words each).
    Strategy:
      1. Find lines that contain a fashion keyword.
      2. Extract the 2-5 words around that keyword to form a tight query.
      3. Deduplicate and return up to max_items queries.
    """
    queries = []
    seen    = set()

    for line in final_text.split("\n"):
        stripped = line.strip()
        if len(stripped) < 6:
            continue
        # Strip markdown noise
        clean_line = re.sub(r"[*#\-–•→\[\]:`]", "", stripped).strip()
        lower      = clean_line.lower()

        for kw in _FASHION_KW:
            if kw in lower:
                # Extract a window of words centred on the keyword
                words    = clean_line.split()
                kw_idx   = next(
                    (i for i, w in enumerate(words) if kw in w.lower()), None
                )
                if kw_idx is None:
                    continue
                # Take up to 2 words before and 2 after → max 5-word query
                start  = max(0, kw_idx - 2)
                end    = min(len(words), kw_idx + 3)
                query  = " ".join(words[start:end]).strip(" ,.:;")
                # Keep only printable ASCII, 4-60 chars
                query  = re.sub(r"[^\x20-\x7E]", "", query).strip()
                if 4 <= len(query) <= 60:
                    key = query.lower()
                    if key not in seen:
                        queries.append(query)
                        seen.add(key)
                break  # one match per line

        if len(queries) >= max_items:
            break

    # Fallback: generic queries based on common pieces
    if not queries:
        queries = ["elegant outfit", "fashion look", "stylish dress", "outfit inspiration"]

    return queries


# ─────────────────────────────────────────────────────────────────────────────
# Tool 4 – Seasonal Color Palette
# ─────────────────────────────────────────────────────────────────────────────

_SEASON_PALETTES = {
    "spring": {
        "colors":      ["Blush Pink", "Mint Green", "Lavender", "Butter Yellow", "Sky Blue"],
        "hex":         ["#FFB7C5", "#98FF98", "#E6E6FA", "#FFFACD", "#87CEEB"],
        "description": "Fresh, soft pastels that mirror blooming nature.",
        "avoid":       ["Heavy blacks", "Dark burgundy", "Neon tones"],
    },
    "summer": {
        "colors":      ["Coral", "Turquoise", "White", "Bright Fuchsia", "Lemon Yellow"],
        "hex":         ["#FF6B6B", "#40E0D0", "#FFFFFF", "#FF00AA", "#FFF44F"],
        "description": "Vibrant, energetic tones that pop in bright sunlight.",
        "avoid":       ["Heavy wools", "Dark navy"],
    },
    "autumn": {
        "colors":      ["Burnt Orange", "Mustard", "Forest Green", "Burgundy", "Camel"],
        "hex":         ["#CC5500", "#FFDB58", "#228B22", "#800020", "#C19A6B"],
        "description": "Rich, earthy tones inspired by falling leaves.",
        "avoid":       ["Neons", "Icy pastels"],
    },
    "winter": {
        "colors":      ["Midnight Navy", "Emerald", "Crimson", "Charcoal", "Ivory"],
        "hex":         ["#003153", "#50C878", "#DC143C", "#36454F", "#FFFFF0"],
        "description": "Bold, saturated colours and classic neutrals for cold days.",
        "avoid":       ["Washed-out pastels", "Overly light tones"],
    },
}


def get_color_palette(event_date: str, skin_tone: str = "neutral") -> dict:
    """
    Derive a seasonal colour palette from *event_date* (YYYY-MM-DD) and
    *skin_tone* (fair / medium / olive / dark / neutral).
    Returns palette colours, hex codes, and skin-tone tweaks.
    """
    try:
        month = datetime.strptime(event_date, "%Y-%m-%d").month
    except ValueError:
        month = datetime.now().month

    if month in (3, 4, 5):
        season = "spring"
    elif month in (6, 7, 8):
        season = "summer"
    elif month in (9, 10, 11):
        season = "autumn"
    else:
        season = "winter"

    palette = _SEASON_PALETTES[season].copy()
    palette["season"] = season.capitalize()

    # Skin-tone complementary tip
    skin_tips = {
        "fair":    "Cool undertones like lavender, blue-based reds, and soft pinks work best.",
        "medium":  "Warm earth tones, camel, terracotta, and warm whites suit you beautifully.",
        "olive":   "Rich jewel tones – emerald, plum, cobalt – make your complexion glow.",
        "dark":    "Bold, saturated colours and bright whites create a stunning contrast.",
        "neutral": "You can carry most colour families – experiment freely!",
    }
    palette["skin_tone_tip"] = skin_tips.get(skin_tone.lower(), skin_tips["neutral"])
    return palette


# ─────────────────────────────────────────────────────────────────────────────
# Tool 5 – Dress Code Guide
# ─────────────────────────────────────────────────────────────────────────────

_DRESS_CODES = {
    "wedding": {
        "formality":  "Formal / Black Tie Optional",
        "men":        ["Suit or Tuxedo", "Dress shirt + tie", "Leather oxford shoes"],
        "women":      ["Formal gown or midi dress", "Elegant heels or dressy flats", "Minimal jewellery"],
        "avoid":      ["White or ivory (reserved for the bride)", "Overly casual wear", "Flip-flops"],
        "tips":       "Match the venue vibe – garden weddings allow florals; ballroom events call for gowns.",
    },
    "cocktail party": {
        "formality":  "Semi-formal",
        "men":        ["Dark trousers + blazer", "Dress shirt (no tie needed)", "Loafers or oxfords"],
        "women":      ["Cocktail dress (knee-length)", "Jumpsuit", "Block heels or strappy sandals"],
        "avoid":      ["Full-length gowns", "Casual jeans", "Sports footwear"],
        "tips":       "A little black dress is always a safe, chic choice.",
    },
    "business meeting": {
        "formality":  "Business Professional",
        "men":        ["Tailored suit (navy/grey)", "Crisp white/light-blue shirt", "Conservative tie", "Oxford shoes"],
        "women":      ["Blazer + tailored trousers or pencil skirt", "Blouse", "Court shoes or block heels"],
        "avoid":      ["Loud patterns", "Overly casual footwear", "Excessive accessories"],
        "tips":       "Fit is everything – well-tailored basics always project confidence.",
    },
    "casual outing": {
        "formality":  "Casual",
        "men":        ["Chinos or dark jeans", "Polo or casual shirt", "Sneakers or loafers"],
        "women":      ["Jeans + top", "Sundress", "Sneakers, sandals, or ankle boots"],
        "avoid":      ["Formal wear", "Overly dressy shoes on cobblestone streets"],
        "tips":       "Comfort is key; layer up if the weather is unpredictable.",
    },
    "beach / pool": {
        "formality":  "Resort Casual",
        "men":        ["Swim shorts", "Linen shirt (open)", "Flip-flops or espadrilles"],
        "women":      ["Swimsuit + cover-up", "Sarong or beach dress", "Sandals"],
        "avoid":      ["Heavy fabrics", "Suede or leather footwear near water"],
        "tips":       "Opt for UV-protective fabrics; pack a wide-brim hat.",
    },
    "festival": {
        "formality":  "Creative / Boho",
        "men":        ["Graphic tee", "Cargo shorts or relaxed trousers", "Comfortable boots or sneakers"],
        "women":      ["Flowy dress or denim shorts", "Crop top + high-waist bottoms", "Boots, sneakers, or strappy sandals"],
        "avoid":      ["Formal shoes (heels sink in grass)", "Expensive bags in crowds"],
        "tips":       "Embrace colour, patterns, and accessories – festivals reward bold styling!",
    },
    "date night": {
        "formality":  "Smart Casual to Semi-formal",
        "men":        ["Dark jeans or chinos", "Button-down or smart polo", "Chelsea boots or loafers"],
        "women":      ["Midi dress or tailored jumpsuit", "Wrap dress", "Heels or chic flats"],
        "avoid":      ["Overly casual athleisure", "Uncomfortable footwear if you'll be walking"],
        "tips":       "Choose an outfit that makes YOU feel confident – confidence is the best accessory.",
    },
    "gym / workout": {
        "formality":  "Athletic",
        "men":        ["Performance shorts or leggings", "Moisture-wicking tee", "Athletic trainers"],
        "women":      ["Sports bra + leggings", "Tank top", "Supportive athletic shoes"],
        "avoid":      ["Cotton (stays wet)", "Restrictive clothing"],
        "tips":       "Invest in quality activewear – it improves both performance and motivation.",
    },
}


def get_dress_code_guide(event_type: str) -> dict:
    """
    Return a detailed dress-code guide for *event_type*.
    Fuzzy-matches against known event types; falls back to 'casual outing'.
    """
    key = event_type.lower().strip()
    # Fuzzy match
    for known in _DRESS_CODES:
        if known in key or key in known:
            return {"event_type": event_type, **_DRESS_CODES[known]}

    # Fallback
    return {
        "event_type": event_type,
        "note":       f"No specific guide for '{event_type}'. Showing smart-casual defaults.",
        **_DRESS_CODES["casual outing"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tool registry (used by the agent to discover available tools)
# ─────────────────────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "get_weather": {
        "fn":          get_weather,
        "description": "Get live weather data for a city on a given date.",
        "params":      ["city (str)", "date_str (YYYY-MM-DD)"],
        "emoji":       "🌤️",
    },
    "get_fashion_news": {
        "fn":          get_fashion_news,
        "description": "Fetch the latest fashion & trend news headlines.",
        "params":      ["query (str)", "max_articles (int, default 5)"],
        "emoji":       "📰",
    },
    "get_outfit_images": {
        "fn":          get_outfit_images,
        "description": "Search Pexels for outfit inspiration images.",
        "params":      ["query (str)", "count (int, default 4)"],
        "emoji":       "🖼️",
    },
    "get_color_palette": {
        "fn":          get_color_palette,
        "description": "Derive a seasonal colour palette for the event date and skin tone.",
        "params":      ["event_date (YYYY-MM-DD)", "skin_tone (fair/medium/olive/dark/neutral)"],
        "emoji":       "🎨",
    },
    "get_dress_code_guide": {
        "fn":          get_dress_code_guide,
        "description": "Return dress-code rules and tips for a specific event type.",
        "params":      ["event_type (str)"],
        "emoji":       "👗",
    },
}
