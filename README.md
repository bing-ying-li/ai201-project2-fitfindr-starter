# FitFindr

FitFindr is a multi-tool AI agent that helps users find secondhand clothing items, style them with an existing wardrobe, and generate a short shareable outfit caption.

The agent uses a planning loop to decide which tool to call next based on the current session state. It does not call every tool blindly. If the search tool returns no listings, the agent stops early and returns a helpful error message.

---

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Project Overview

FitFindr supports a complete secondhand fashion workflow:

1. Search for a secondhand item using a natural language query.
2. Select the best matching listing from the mock dataset.
3. Suggest outfit combinations using the user's wardrobe.
4. Generate a short social-media-style fit card caption.

Example query:

```text
vintage graphic tee under $30
```

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

Then open the local Gradio URL shown in the terminal.

---

## Tool Inventory

### Tool 1: `search_listings(description, size, max_price)`

**Purpose:**
Searches the mock secondhand listings dataset for items that match the user's description, optional size, and optional maximum price.

**Inputs:**

- `description` (str): Keywords describing the item the user wants.
- `size` (str | None): Optional clothing or shoe size. If `None`, size filtering is skipped.
- `max_price` (float | None): Optional maximum price. If `None`, price filtering is skipped.

**Output:**
A list of matching listing dictionaries. Each listing includes fields such as `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

**Failure handling:**
If no listings match, the function returns an empty list `[]` instead of crashing.

---

### Tool 2: `suggest_outfit(new_item, wardrobe)`

**Purpose:**
Suggests one or two complete outfit combinations using the selected secondhand item and the user's wardrobe.

**Inputs:**

- `new_item` (dict): The selected listing returned by `search_listings`.
- `wardrobe` (dict): The user's wardrobe dictionary.

**Output:**
A non-empty string containing outfit suggestions.

**Failure handling:**
If the wardrobe is empty, the tool still returns general styling advice using common wardrobe basics. If the LLM call fails, it returns a helpful error message string instead of raising an exception.

---

### Tool 3: `create_fit_card(outfit, new_item)`

**Purpose:**
Creates a short, shareable outfit caption based on the selected item and outfit suggestion.

**Inputs:**

- `outfit` (str): The outfit suggestion returned by `suggest_outfit`.
- `new_item` (dict): The selected secondhand listing.

**Output:**
A short 2–4 sentence social-media-style fit card caption.

**Failure handling:**
If the outfit string is empty, the tool returns a clear error message instead of crashing.

---

## Planning Loop

The planning loop is implemented in `run_agent()` inside `agent.py`.

The agent follows this logic:

1. Initialize a new `session` dictionary.
2. Parse the user query into:
   - `description`
   - `size`
   - `max_price`

3. Call `search_listings(description, size, max_price)`.
4. If no search results are found:
   - Store a helpful message in `session["error"]`.
   - Return the session early.
   - Do not call `suggest_outfit()` or `create_fit_card()`.

5. If results are found:
   - Store all results in `session["search_results"]`.
   - Select the first result and store it in `session["selected_item"]`.

6. Call `suggest_outfit(selected_item, wardrobe)`.
7. Store the outfit suggestion in `session["outfit_suggestion"]`.
8. Call `create_fit_card(outfit_suggestion, selected_item)`.
9. Store the fit card in `session["fit_card"]`.
10. Return the completed session.

This means the agent's behavior changes depending on what `search_listings()` returns.

---

## State Management

The agent uses a session dictionary to pass information between tools.

The session stores:

```python
{
    "query": query,
    "parsed": {},
    "search_results": [],
    "selected_item": None,
    "wardrobe": wardrobe,
    "outfit_suggestion": None,
    "fit_card": None,
    "error": None,
}
```

The output from one tool becomes input for the next tool.

For example:

- `search_listings()` returns listings.
- The first listing is saved as `session["selected_item"]`.
- `session["selected_item"]` is passed into `suggest_outfit()`.
- `session["outfit_suggestion"]` is passed into `create_fit_card()`.

The user does not need to re-enter the item between steps.

---

## Error Handling Strategy

| Tool              | Failure mode                | Response                                                             |
| ----------------- | --------------------------- | -------------------------------------------------------------------- |
| `search_listings` | No listings match the query | Returns `[]`. The agent stores an error message and stops early.     |
| `suggest_outfit`  | Wardrobe is empty           | Returns general styling advice instead of crashing.                  |
| `suggest_outfit`  | LLM call fails              | Returns a helpful error message string.                              |
| `create_fit_card` | Outfit string is empty      | Returns a clear error message saying the fit card cannot be created. |
| `create_fit_card` | LLM call fails              | Returns a helpful error message string.                              |

Example failure test:

```text
designer ballgown size XXS under $5
```

Result:

```text
I couldn't find any listings for 'designer ballgown' in size XXS under $5. Try using broader keywords, removing the size filter, or increasing your budget.
```

In this case, the agent stops early and leaves these values as `None`:

```python
session["selected_item"] = None
session["outfit_suggestion"] = None
session["fit_card"] = None
```

---

## Testing

I wrote pytest tests in `tests/test_tools.py`.

The tests check that:

- `search_listings()` returns results for a normal query.
- `search_listings()` returns `[]` for an impossible query.
- `search_listings()` respects the max price filter.
- `suggest_outfit()` handles an empty wardrobe.
- `create_fit_card()` handles an empty outfit string.

Run tests with:

```bash
pytest tests/
```

Current result:

```text
5 passed
```

---

## Example Interaction

User query:

```text
vintage graphic tee under $30
```

The agent parses the query into:

```python
{
    "description": "vintage graphic tee",
    "size": None,
    "max_price": 30.0
}
```

Then it calls:

```python
search_listings("vintage graphic tee", size=None, max_price=30.0)
```

If a listing is found, the agent stores the top result in:

```python
session["selected_item"]
```

Then it calls:

```python
suggest_outfit(session["selected_item"], session["wardrobe"])
```

The outfit suggestion is stored in:

```python
session["outfit_suggestion"]
```

Finally, the agent calls:

```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

The result is stored in:

```python
session["fit_card"]
```

---

## Spec Reflection

One way the planning spec helped me was by separating each tool's responsibility before implementation. This made it easier to build and test `search_listings`, `suggest_outfit`, and `create_fit_card` individually before connecting them through the planning loop.

One way the implementation diverged from the spec was query parsing. Instead of using an LLM to parse the user's query, I used regular expressions to extract price and size. This was simpler, easier to test, and reliable enough for the example queries in this project.

---

## AI Usage

I used ChatGPT to help implement the individual tools in `tools.py`. I gave it my tool specifications from `planning.md`, including each tool's inputs, expected output, and failure mode. I reviewed the generated code to make sure `search_listings()` used `load_listings()` instead of re-implementing file loading, and I verified the behavior with pytest.

I also used ChatGPT to help implement the planning loop in `agent.py`. I gave it my Planning Loop, State Management, and Architecture sections from `planning.md`. I checked that the generated loop branched correctly: when `search_listings()` returned no results, the agent stopped early and did not call `suggest_outfit()` or `create_fit_card()`.

I used ChatGPT again to help implement `handle_query()` in `app.py`. I verified that it correctly maps the session values to the three Gradio output panels: top listing, outfit idea, and fit card.

---

## Demo Video Checklist

The demo video shows:

- A complete successful interaction from search to fit card.
- The selected item being passed through the session state.
- An outfit suggestion generated from the selected item and wardrobe.
- A fit card generated from the outfit suggestion.
- A failure case where no listings are found and the agent stops early.
