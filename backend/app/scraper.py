import json
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
    )
}


class ScrapeError(RuntimeError):
    pass


def scrape_recipe_page(url: str) -> dict[str, Any]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScrapeError(f"Unable to fetch recipe URL: {exc}") from exc

    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    structured = _extract_json_ld(response.text)
    title = _first_text(soup, ["h1", "meta[property='og:title']"]) or url
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return {
        "url": url,
        "title_hint": title,
        "json_ld": structured,
        "text": text[:18000],
    }


def _first_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        if node.name == "meta":
            return node.get("content", "").strip()
        return node.get_text(" ", strip=True)
    return ""


def _extract_json_ld(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    results: list[dict[str, Any]] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(data):
            item_type = item.get("@type", "")
            item_types = item_type if isinstance(item_type, list) else [item_type]
            if any(str(value).lower() == "recipe" for value in item_types):
                results.append(item)
    return results


def _flatten_json_ld(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for value in data for item in _flatten_json_ld(value)]
    if isinstance(data, dict):
        graph = data.get("@graph")
        if isinstance(graph, list):
            return [data, *[item for value in graph for item in _flatten_json_ld(value)]]
        return [data]
    return []
