import json
import os
import re
from pathlib import Path
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from .schemas import RecipePayload

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def generate_recipe_data(scraped: dict[str, Any]) -> RecipePayload:
    if os.getenv("GEMINI_API_KEY"):
        try:
            return _generate_with_gemini(scraped)
        except Exception:
            pass
    return _generate_fallback(scraped)


def _generate_with_gemini(scraped: dict[str, Any]) -> RecipePayload:
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt_text = (PROMPTS_DIR / "recipe_extraction_prompt.md").read_text(encoding="utf-8")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_text),
            (
                "human",
                "Title hint: {title_hint}\nJSON-LD: {json_ld}\nPage text:\n{text}",
            ),
        ]
    )
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
    message = (prompt | model).invoke(
        {
            "title_hint": scraped["title_hint"],
            "json_ld": json.dumps(scraped["json_ld"])[:12000],
            "text": scraped["text"],
        }
    )
    content = _strip_json_fence(str(message.content))
    return RecipePayload.model_validate_json(content)


def _generate_fallback(scraped: dict[str, Any]) -> RecipePayload:
    recipe = scraped.get("json_ld", [{}])[0] if scraped.get("json_ld") else {}
    ingredients = [_parse_ingredient(value) for value in recipe.get("recipeIngredient", [])]
    instructions = _parse_instructions(recipe.get("recipeInstructions", []))
    title = recipe.get("name") or scraped.get("title_hint") or "Untitled Recipe"
    cuisine = recipe.get("recipeCuisine") or "Unknown"
    servings = _parse_servings(recipe.get("recipeYield"))

    if not ingredients:
        ingredients = [{"quantity": "", "unit": "", "item": "Ingredients unavailable"}]
    if not instructions:
        instructions = ["Instructions were not clearly available on the scraped page."]

    shopping = _group_shopping_list(ingredients)
    return RecipePayload(
        title=str(title),
        cuisine=str(cuisine if not isinstance(cuisine, list) else cuisine[0]),
        prep_time=_human_time(recipe.get("prepTime")) or "Unknown",
        cook_time=_human_time(recipe.get("cookTime")) or "Unknown",
        total_time=_human_time(recipe.get("totalTime")) or "Unknown",
        servings=servings,
        difficulty=_difficulty(instructions, ingredients),
        ingredients=ingredients,
        instructions=instructions,
        nutrition_estimate=_estimate_nutrition(ingredients),
        substitutions=[
            "Swap butter with olive oil for a dairy-free option.",
            "Use whole grain bread or pasta for extra fiber when it fits the dish.",
            "Reduce salt and add lemon juice or herbs for a brighter lower-sodium version.",
        ],
        shopping_list=shopping,
        related_recipes=[
            "Simple side salad",
            "Roasted seasonal vegetables",
            "Light soup pairing",
        ],
    )


def _strip_json_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def _parse_ingredient(raw: str) -> dict[str, str]:
    text = re.sub(r"\s+", " ", str(raw)).strip()
    match = re.match(r"^(?P<quantity>[\d./\s-]+)?\s*(?P<unit>[A-Za-z]+)?\s*(?P<item>.*)$", text)
    if not match:
        return {"quantity": "", "unit": "", "item": text}
    quantity = (match.group("quantity") or "").strip()
    unit = (match.group("unit") or "").strip()
    item = (match.group("item") or text).strip(" ,")
    return {"quantity": quantity, "unit": unit, "item": item}


def _parse_instructions(raw: Any) -> list[str]:
    steps: list[str] = []
    if isinstance(raw, str):
        return [raw]
    for item in raw or []:
        if isinstance(item, str):
            steps.append(item)
        elif isinstance(item, dict):
            text = item.get("text") or item.get("name")
            if text:
                steps.append(str(text))
            nested = item.get("itemListElement")
            if nested:
                steps.extend(_parse_instructions(nested))
    return [re.sub(r"\s+", " ", step).strip() for step in steps if step]


def _parse_servings(value: Any) -> int:
    if isinstance(value, list):
        value = value[0] if value else 1
    match = re.search(r"\d+", str(value or "1"))
    return max(1, int(match.group(0))) if match else 1


def _human_time(value: Any) -> str:
    if not value:
        return ""
    text = str(value)
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", text)
    if not match:
        return text
    hours, minutes = match.groups()
    parts = []
    if hours:
        parts.append(f"{hours} hr")
    if minutes:
        parts.append(f"{minutes} mins")
    return " ".join(parts)


def _difficulty(instructions: list[str], ingredients: list[dict[str, str]]) -> str:
    score = len(instructions) + len(ingredients)
    if score <= 12:
        return "easy"
    if score <= 24:
        return "medium"
    return "hard"


def _estimate_nutrition(ingredients: list[dict[str, str]]) -> dict[str, Any]:
    count = max(1, len(ingredients))
    return {
        "calories": min(900, 120 + count * 45),
        "protein": f"{max(6, count * 2)}g",
        "carbs": f"{max(12, count * 5)}g",
        "fat": f"{max(5, count * 3)}g",
    }


def _group_shopping_list(ingredients: list[dict[str, str]]) -> dict[str, list[str]]:
    categories = {"dairy": [], "produce": [], "pantry": [], "protein": [], "bakery": []}
    for ingredient in ingredients:
        item = ingredient["item"].lower()
        target = "pantry"
        if any(word in item for word in ["cheese", "milk", "butter", "cream", "yogurt"]):
            target = "dairy"
        elif any(word in item for word in ["onion", "tomato", "garlic", "lettuce", "pepper", "lemon"]):
            target = "produce"
        elif any(word in item for word in ["chicken", "beef", "egg", "fish", "tofu", "pork"]):
            target = "protein"
        elif any(word in item for word in ["bread", "bun", "roll", "tortilla"]):
            target = "bakery"
        categories[target].append(ingredient["item"])
    return {key: values for key, values in categories.items() if values}
