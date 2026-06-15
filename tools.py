"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re
from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)

def _call_llm(prompt: str, temperature: float = 0.7, max_tokens: int = 350) -> str:
    """Call Groq LLM and return the response text."""
    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FitFindr, a helpful fashion styling assistant. "
                    "Keep answers practical, specific, and natural."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation
    # return []
    listings = load_listings()

    stop_words = {
        "a", "an", "the", "for", "under", "below", "less", "than",
        "size", "in", "looking", "look", "find", "me", "i", "want",
        "with", "and", "or", "to", "wear", "mostly", "what", "out",
        "there", "how", "would", "style", "it"
    }

    def tokenize(text: str) -> list[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        return [w for w in words if w not in stop_words]

    def size_matches(item_size: str, requested_size: str | None) -> bool:
        if not requested_size:
            return True

        req = requested_size.lower().strip()
        item = item_size.lower().strip()

        aliases = {
            "xs": ["xs", "extra small"],
            "s": ["s", "small"],
            "m": ["m", "medium"],
            "l": ["l", "large"],
            "xl": ["xl", "extra large"],
        }

        if req in item:
            return True

        if req in aliases:
            return any(alias in item for alias in aliases[req])

        return False

    query_tokens = tokenize(description)
    results = []

    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue

        if not size_matches(listing["size"], size):
            continue

        searchable_text = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
            str(listing.get("brand") or ""),
            listing.get("platform", ""),
        ]).lower()

        score = 0

        if description.lower().strip() in searchable_text:
            score += 5

        for token in query_tokens:
            if token in searchable_text:
                score += 1

        if score > 0:
            result = listing.copy()
            result["_score"] = score
            results.append(result)

    results.sort(key=lambda item: item["_score"], reverse=True)

    for item in results:
        item.pop("_score", None)

    return results


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    # return ""
    wardrobe_items = wardrobe.get("items", [])

    item_summary = (
        f"Item: {new_item.get('title')}\n"
        f"Category: {new_item.get('category')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Condition: {new_item.get('condition')}\n"
        f"Price: ${new_item.get('price')}\n"
        f"Platform: {new_item.get('platform')}"
    )

    if not wardrobe_items:
        prompt = f"""
The user found this secondhand item:

{item_summary}

The user has not added any wardrobe items yet.

Suggest 1-2 practical outfit ideas using general clothing pieces someone might own.
Keep it specific, casual, and useful.
Do not say you cannot help.
"""
        return _call_llm(prompt, temperature=0.7)

    wardrobe_text = []
    for item in wardrobe_items:
        wardrobe_text.append(
            f"- {item.get('name')} | category: {item.get('category')} | "
            f"colors: {', '.join(item.get('colors', []))} | "
            f"style tags: {', '.join(item.get('style_tags', []))} | "
            f"notes: {item.get('notes')}"
        )

    prompt = f"""
The user is considering buying this thrifted item:

{item_summary}

Here is the user's wardrobe:
{chr(10).join(wardrobe_text)}

Suggest 1-2 complete outfit combinations.
Use the thrifted item and specific named pieces from the wardrobe.
Explain the vibe and give small styling details.
Keep the response concise but helpful.
"""
    return _call_llm(prompt, temperature=0.7)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    # return ""
    if not outfit or not outfit.strip():
        return (
            "Cannot create a fit card because the outfit suggestion is missing. "
            "Please generate an outfit suggestion first."
        )

    prompt = f"""
Create a short shareable outfit caption for social media.

Thrifted item:
- Title: {new_item.get('title')}
- Price: ${new_item.get('price')}
- Platform: {new_item.get('platform')}
- Style tags: {', '.join(new_item.get('style_tags', []))}
- Colors: {', '.join(new_item.get('colors', []))}

Outfit suggestion:
{outfit}

Requirements:
- 2 to 4 sentences only.
- Sound casual and authentic, like a real OOTD caption.
- Mention the item name, price, and platform naturally once.
- Capture the outfit vibe.
- Do not sound like a product advertisement.
"""
    return _call_llm(prompt, temperature=0.95, max_tokens=220)
