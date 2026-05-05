import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Recipe
from .schemas import (
    ExtractRequest,
    HistoryRecipe,
    MealPlanRequest,
    MealPlanResponse,
    RecipeResponse,
)
from .scraper import ScrapeError
from .services import build_combined_shopping_list, extract_and_store_recipe

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Recipe Extractor & Meal Planner API")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/recipes/extract", response_model=RecipeResponse)
def extract_recipe(request: ExtractRequest, db: Session = Depends(get_db)):
    try:
        return extract_and_store_recipe(str(request.url), db)
    except ScrapeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Recipe extraction failed: {exc}") from exc


@app.get("/api/recipes", response_model=list[HistoryRecipe])
def list_recipes(db: Session = Depends(get_db)):
    return db.scalars(select(Recipe).order_by(Recipe.created_at.desc())).all()


@app.get("/api/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.post("/api/meal-plan", response_model=MealPlanResponse)
def create_meal_plan(request: MealPlanRequest, db: Session = Depends(get_db)):
    recipes = db.scalars(select(Recipe).where(Recipe.id.in_(request.recipe_ids))).all()
    if len(recipes) != len(set(request.recipe_ids)):
        raise HTTPException(status_code=404, detail="One or more recipes were not found")
    return {
        "recipes": recipes,
        "combined_shopping_list": build_combined_shopping_list(recipes),
        "notes": [
            "Quantities are merged by ingredient name where possible.",
            "Review pantry staples before shopping.",
        ],
    }
