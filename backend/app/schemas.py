from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ExtractRequest(BaseModel):
    url: HttpUrl


class Ingredient(BaseModel):
    quantity: str = ""
    unit: str = ""
    item: str


class NutritionEstimate(BaseModel):
    calories: int = 0
    protein: str = "Unknown"
    carbs: str = "Unknown"
    fat: str = "Unknown"


class RecipePayload(BaseModel):
    title: str
    cuisine: str = "Unknown"
    prep_time: str = "Unknown"
    cook_time: str = "Unknown"
    total_time: str = "Unknown"
    servings: int = Field(default=1, ge=1)
    difficulty: str = "easy"
    ingredients: list[Ingredient] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    nutrition_estimate: NutritionEstimate = Field(default_factory=NutritionEstimate)
    substitutions: list[str] = Field(default_factory=list)
    shopping_list: dict[str, list[str]] = Field(default_factory=dict)
    related_recipes: list[str] = Field(default_factory=list)


class RecipeResponse(RecipePayload):
    id: int
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryRecipe(BaseModel):
    id: int
    url: str
    title: str
    cuisine: str
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True


class MealPlanRequest(BaseModel):
    recipe_ids: list[int] = Field(min_length=3, max_length=5)


class MealPlanResponse(BaseModel):
    recipes: list[HistoryRecipe]
    combined_shopping_list: dict[str, list[str]]
    notes: list[str]
