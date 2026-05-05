# Recipe Extractor & Meal Planner

Full-stack recipe extractor built with FastAPI, PostgreSQL, LangChain/Gemini, BeautifulSoup, and React.

## Features

- Extracts recipe data from recipe blog HTML pages.
- Uses BeautifulSoup for scraping and LangChain with Gemini when `GEMINI_API_KEY` is configured.
- Falls back to JSON-LD parsing when no LLM key is available, so the app remains testable.
- Stores extracted recipes in PostgreSQL.
- Shows saved recipe history with a details modal.
- Optional meal planner combines shopping lists for 3 to 5 saved recipes.

## Project Structure

```text
backend/
  app/
    main.py
    models.py
    schemas.py
    scraper.py
    llm.py
    services.py
  requirements.txt
frontend/
  src/
    main.jsx
    styles.css
prompts/
sample_data/
screenshots/
docker-compose.yml
```

## Backend Setup

1. Start PostgreSQL:

```bash
docker compose up -d
```

2. Create and activate a Python virtual environment:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment:

```bash
copy .env.example .env
```

Set `GEMINI_API_KEY` in `backend/.env` to enable LLM extraction. Without it, the app uses the deterministic JSON-LD fallback.

5. Run the API:

```bash
uvicorn app.main:app --reload
```

API runs at `http://127.0.0.1:8000`.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`.

## API Endpoints

- `GET /health` - health check.
- `POST /api/recipes/extract` - scrape, extract, generate, store, and return a recipe.

```json
{
  "url": "https://www.allrecipes.com/recipe/23891/grilled-cheese-sandwich/"
}
```

- `GET /api/recipes` - list saved recipe history.
- `GET /api/recipes/{recipe_id}` - get full saved recipe details.
- `POST /api/meal-plan` - combine shopping lists for 3 to 5 saved recipes.

```json
{
  "recipe_ids": [1, 2, 3]
}
```

## Prompts

Prompt templates are stored in `prompts/`:

- `recipe_extraction_prompt.md`
- `nutrition_prompt.md`
- `substitution_prompt.md`
- `meal_planning_prompt.md`

The main extraction prompt instructs the LLM to return strict JSON, ground factual fields in scraped text/JSON-LD, separate ingredient quantity/unit/item, and use conservative estimates for generated fields.

## Sample Data

`sample_data/example_urls.txt` contains tested recipe URLs.

`sample_data/grilled_cheese_output.json` contains representative API output for the required sample recipe.

## Screenshots

Submission screenshots are documented in [screenshots/README.md](screenshots/README.md).

## Testing Steps

1. Start PostgreSQL with Docker Compose.
2. Run the FastAPI server.
3. Run the React dev server.
4. Open `http://127.0.0.1:5173`.
5. Extract a recipe URL from `sample_data/example_urls.txt`.
6. Confirm the recipe appears in Tab 1.
7. Open Tab 2 and verify the saved history row.
8. Click `Details` and verify the modal.
9. Save at least three recipes, select them in history, and click `Build List`.

## Error Handling

- Invalid URLs are rejected by request validation.
- Network and scraping failures return `422` with a clear message.
- Missing recipes return `404`.
- General extraction failures return `500`.
- Missing page fields fall back to `Unknown` or conservative generated values.
