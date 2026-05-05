from collections import defaultdict

from sqlalchemy.orm import Session

from .llm import generate_recipe_data
from .models import Recipe
from .scraper import scrape_recipe_page


def extract_and_store_recipe(url: str, db: Session) -> Recipe:
    scraped = scrape_recipe_page(url)
    payload = generate_recipe_data(scraped)
    recipe = Recipe(
        url=url,
        raw_text=scraped["text"],
        **payload.model_dump(mode="json"),
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def build_combined_shopping_list(recipes: list[Recipe]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for recipe in recipes:
        for category, items in recipe.shopping_list.items():
            for item in items:
                key = (category, item.lower())
                if key not in seen:
                    grouped[category].append(item)
                    seen.add(key)
    return dict(grouped)
