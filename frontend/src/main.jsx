import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ChefHat,
  ClipboardList,
  History,
  Loader2,
  Search,
  ShoppingBasket,
  X,
  Sparkles,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function App() {
  const [activeTab, setActiveTab] = useState("extract");
  const [url, setUrl] = useState(
    "https://www.allrecipes.com/recipe/23891/grilled-cheese-sandwich/",
  );
  const [currentRecipe, setCurrentRecipe] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [mealPlan, setMealPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "Request failed");
    }
    return response.json();
  }

  async function extractRecipe(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const recipe = await request("/api/recipes/extract", {
        method: "POST",
        body: JSON.stringify({ url }),
      });
      setCurrentRecipe(recipe);
      await loadHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const recipes = await request("/api/recipes");
      setHistory(recipes);
    } catch (err) {
      setError(err.message);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function openDetails(id) {
    setError("");
    try {
      setSelectedRecipe(await request(`/api/recipes/${id}`));
    } catch (err) {
      setError(err.message);
    }
  }

  async function createMealPlan() {
    setError("");
    setMealPlan(null);
    try {
      setMealPlan(
        await request("/api/meal-plan", {
          method: "POST",
          body: JSON.stringify({ recipe_ids: selectedIds }),
        }),
      );
    } catch (err) {
      setError(err.message);
    }
  }

  function toggleRecipe(id) {
    setSelectedIds((ids) => {
      if (ids.includes(id)) return ids.filter((v) => v !== id);
      if (ids.length >= 5) return ids;
      return [...ids, id];
    });
  }

  const canPlan = selectedIds.length >= 3 && selectedIds.length <= 5;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <h1>
            <em>Extract</em> &amp; Sauté: <span className="subtitle">Our Meal Planner</span>
          </h1>
        </div>
      </header>

      <nav className="tabs" aria-label="Recipe tabs">
        <button
          className={activeTab === "extract" ? "active" : ""}
          onClick={() => setActiveTab("extract")}
        >
          <Search size={16} />
          Extract Recipe
        </button>
        <button
          className={activeTab === "history" ? "active" : ""}
          onClick={() => setActiveTab("history")}
        >
          <History size={16} />
          Saved Recipes
        </button>
      </nav>

      {error && <div className="alert">⚠️ {error}</div>}

      {activeTab === "extract" && (
        <section className="workspace">
          <form className="extract-form" onSubmit={extractRecipe}>
            <label htmlFor="recipe-url">Paste a recipe blog URL</label>
            <div className="input-row">
              <input
                id="recipe-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/my-favourite-recipe"
                required
              />
              <button className="primary-button" disabled={loading}>
                {loading ? (
                  <Loader2 className="spin" size={16} />
                ) : (
                  <Sparkles size={16} />
                )}
                {loading ? "Extracting…" : "Extract Recipe"}
              </button>
            </div>
          </form>

          {currentRecipe ? (
            <RecipeDetails recipe={currentRecipe} />
          ) : (
            <EmptyState />
          )}
        </section>
      )}

      {activeTab === "history" && (
        <section className="workspace">
          <HistoryTable
            recipes={history}
            selectedIds={selectedIds}
            loading={historyLoading}
            onDetails={openDetails}
            onToggle={toggleRecipe}
          />
          <MealPlannerPanel
            canPlan={canPlan}
            selectedCount={selectedIds.length}
            mealPlan={mealPlan}
            onCreate={createMealPlan}
          />
        </section>
      )}

      {selectedRecipe && (
        <RecipeModal
          recipe={selectedRecipe}
          onClose={() => setSelectedRecipe(null)}
        />
      )}
    </main>
  );
}

function EmptyState() {
  return (
    <section className="empty-state">
      <div className="empty-icon">🍜</div>
      <h2>Drop in a recipe URL to get started</h2>
      <p>
        We'll pull out ingredients, step-by-step instructions, nutrition
        estimates, smart substitutions, and a ready-to-shop grocery list — all
        in seconds.
      </p>
    </section>
  );
}

function RecipeDetails({ recipe }) {
  const nutrition = recipe.nutrition_estimate || {};
  return (
    <section className="recipe-grid">
      <article className="panel recipe-hero">
        <p className="eyebrow">{recipe.cuisine}</p>
        <h2>{recipe.title}</h2>
        <div className="meta-grid">
          <Meta label="Prep" value={recipe.prep_time} />
          <Meta label="Cook" value={recipe.cook_time} />
          <Meta label="Total" value={recipe.total_time} />
          <Meta label="Serves" value={recipe.servings} />
          <Meta label="Difficulty" value={recipe.difficulty} />
        </div>
      </article>

      <article className="panel">
        <h3>🛒 Ingredients</h3>
        <ul className="ingredient-list">
          {recipe.ingredients?.map((ing, i) => (
            <li key={`${ing.item}-${i}`}>
              <span>{[ing.quantity, ing.unit].filter(Boolean).join(" ")}</span>
              {ing.item}
            </li>
          ))}
        </ul>
      </article>

      <article className="panel wide">
        <h3>👨‍🍳 Instructions</h3>
        <ol className="step-list">
          {recipe.instructions?.map((step, i) => (
            <li key={`step-${i}`}>{step}</li>
          ))}
        </ol>
      </article>

      <article className="panel">
        <h3>📊 Nutrition per serving</h3>
        <div className="nutrition-grid">
          <Meta label="Calories" value={nutrition.calories || "—"} />
          <Meta label="Protein" value={nutrition.protein || "—"} />
          <Meta label="Carbs" value={nutrition.carbs || "—"} />
          <Meta label="Fat" value={nutrition.fat || "—"} />
        </div>
      </article>

      <ListPanel title="✨ Substitutions" items={recipe.substitutions} />
      <ShoppingList shoppingList={recipe.shopping_list} />
      <ListPanel title="📖 Related Recipes" items={recipe.related_recipes} />
    </section>
  );
}

function Meta({ label, value }) {
  return (
    <div className="meta-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ListPanel({ title, items = [], embedded = false }) {
  const content = (
    <>
      <h3>{title}</h3>
      <ul className="plain-list">
        {items.map((item, i) => (
          <li key={`${item}-${i}`}>{item}</li>
        ))}
      </ul>
    </>
  );
  if (embedded) return <div className="embedded-block">{content}</div>;
  return <article className="panel">{content}</article>;
}

function ShoppingList({ shoppingList = {}, embedded = false }) {
  const content = (
    <>
      <h3>🛍️ Shopping List</h3>
      <div className="shopping-groups">
        {Object.entries(shoppingList).map(([category, items]) => (
          <div key={category}>
            <h4>{category}</h4>
            <ul className="plain-list">
              {items.map((item, i) => (
                <li key={`${item}-${i}`}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
  if (embedded) return <div className="embedded-block">{content}</div>;
  return <article className="panel">{content}</article>;
}

function HistoryTable({ recipes, selectedIds, loading, onDetails, onToggle }) {
  return (
    <article className="panel history-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Your collection</p>
          <h2>Saved Recipes</h2>
        </div>
        {loading && <Loader2 className="spin" size={18} />}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Plan</th>
              <th>Title</th>
              <th>Cuisine</th>
              <th>Difficulty</th>
              <th>Date Extracted</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {recipes.map((recipe) => (
              <tr key={recipe.id}>
                <td>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(recipe.id)}
                    onChange={() => onToggle(recipe.id)}
                    aria-label={`Select ${recipe.title}`}
                  />
                </td>
                <td>
                  <strong>{recipe.title}</strong>
                </td>
                <td>{recipe.cuisine}</td>
                <td>
                  <span className="badge">{recipe.difficulty}</span>
                </td>
                <td>{new Date(recipe.created_at).toLocaleString()}</td>
                <td>
                  <button
                    className="ghost-button"
                    onClick={() => onDetails(recipe.id)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
            {!recipes.length && (
              <tr>
                <td colSpan="6" className="empty-cell">
                  🍽️ No saved recipes yet — extract one to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function MealPlannerPanel({ canPlan, selectedCount, mealPlan, onCreate }) {
  return (
    <article className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Weekly planning</p>
          <h2>Meal Planner</h2>
        </div>
        <button
          className="primary-button"
          disabled={!canPlan}
          onClick={onCreate}
        >
          <ShoppingBasket size={16} />
          Build Shopping List
        </button>
      </div>
      <p className="muted">
        Select 3–5 saved recipes to generate a combined grocery list. Currently
        selected: <strong>{selectedCount}</strong>
      </p>
      {mealPlan && (
        <div className="meal-plan-output">
          <ShoppingList
            shoppingList={mealPlan.combined_shopping_list}
            embedded
          />
          <ListPanel
            title="📋 Planning Notes"
            items={mealPlan.notes}
            embedded
          />
        </div>
      )}
    </article>
  );
}

function RecipeModal({ recipe, onClose }) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close details"
        >
          <X size={18} />
        </button>
        <RecipeDetails recipe={recipe} />
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
