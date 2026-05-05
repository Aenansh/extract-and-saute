Given 3 to 5 saved recipes, create a combined shopping list grouped by category.

Merge duplicate ingredients by normalized item name. Preserve quantities when compatible, otherwise list both quantities clearly. Add brief planning notes only when they help the user shop or prep efficiently.

Return valid JSON only:
{
  "combined_shopping_list": {
    "category": ["quantity unit item"]
  },
  "notes": ["brief note"]
}
