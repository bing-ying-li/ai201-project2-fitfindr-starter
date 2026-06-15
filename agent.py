"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""
import re
from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }
# ── query parsing helper ──────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query.

    Example:
        "vintage graphic tee under $30, size M"

    Returns:
        {
            "description": "vintage graphic tee",
            "size": "M",
            "max_price": 30.0
        }
    """
    original_query = query.strip()
    working_text = original_query

    # Extract max price from phrases like:
    # under $30, below 40, less than $25, max $50
    max_price = None
    price_match = re.search(
        r"(?:under|below|less than|max|maximum)\s*\$?\s*(\d+(?:\.\d+)?)",
        working_text,
        flags=re.IGNORECASE,
    )
    if price_match:
        max_price = float(price_match.group(1))
        working_text = re.sub(
            r"(?:under|below|less than|max|maximum)\s*\$?\s*\d+(?:\.\d+)?",
            "",
            working_text,
            flags=re.IGNORECASE,
        )

    # Extract size from phrases like:
    # size M, in size M, sz 8
    size = None
    size_match = re.search(
        r"(?:in\s+)?(?:size|sz)\s+([a-zA-Z0-9./-]+)",
        working_text,
        flags=re.IGNORECASE,
    )
    if size_match:
        size = size_match.group(1).upper()
        working_text = re.sub(
            r"(?:in\s+)?(?:size|sz)\s+[a-zA-Z0-9./-]+",
            "",
            working_text,
            flags=re.IGNORECASE,
        )

    # Remove common filler phrases so search_listings receives cleaner keywords.
    filler_phrases = [
        "i'm looking for",
        "i am looking for",
        "looking for",
        "find me",
        "can you find",
        "i want",
        "what's out there",
        "what is out there",
        "show me",
    ]

    description = working_text.lower()

    for phrase in filler_phrases:
        description = description.replace(phrase, "")

    description = description.strip(" ,.-")

    # Fallback: if parsing removed too much, use the original query.
    if not description:
        description = original_query

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop
    # session = _new_session(query, wardrobe)
    # session["error"] = "Planning loop not yet implemented."
    # return session
    # Step 1: Initialize session.
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query.
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search listings.
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results

    # Branch path: if search returns nothing, stop early.
    # This is the important planning-loop behavior.
    if not results:
        size_text = f" in size {parsed['size']}" if parsed["size"] else ""
        price_text = (
            f" under ${parsed['max_price']:.0f}"
            if parsed["max_price"] is not None
            else ""
        )

        session["error"] = (
            f"I couldn't find any listings for '{parsed['description']}'"
            f"{size_text}{price_text}. Try using broader keywords, removing "
            "the size filter, or increasing your budget."
        )

        return session

    # Step 4: Select the top result and store it in state.
    selected_item = results[0]
    session["selected_item"] = selected_item

    # Step 5: Pass selected_item into suggest_outfit.
    outfit_suggestion = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit_suggestion

    # Step 6: Pass outfit_suggestion and selected_item into create_fit_card.
    fit_card = create_fit_card(outfit_suggestion, selected_item)
    session["fit_card"] = fit_card

    # Step 7: Return completed session.
    return session



# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print("Selected item stored in session['selected_item']:")
        print(f"Found: {session['selected_item']['title']}")
        print("Outfit suggestion stored in session['outfit_suggestion']:")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card stored in session['fit_card']:")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
    print("Parsed query:")
    print(session2["parsed"])
    print()

    print(f"Error message: {session2['error']}")
    print(f"Selected item: {session2['selected_item']}")
    print(f"Outfit suggestion: {session2['outfit_suggestion']}")
    print(f"Fit card: {session2['fit_card']}")