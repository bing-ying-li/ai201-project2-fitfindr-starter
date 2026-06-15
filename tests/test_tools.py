import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe(monkeypatch):
    def fake_llm(prompt, temperature=0.7, max_tokens=350):
        return "Pair it with loose jeans and simple sneakers for a relaxed everyday outfit."

    monkeypatch.setattr("tools._call_llm", fake_llm)

    results = search_listings("vintage graphic tee", size=None, max_price=50)
    response = suggest_outfit(results[0], get_empty_wardrobe())

    assert isinstance(response, str)
    assert len(response) > 0


def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    response = create_fit_card("", results[0])

    assert isinstance(response, str)
    assert "Cannot create a fit card" in response