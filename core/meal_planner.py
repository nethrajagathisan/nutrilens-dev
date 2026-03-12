"""
AI Weekly Meal Planner engine.

Combines:
  • LSTM eating-pattern predictions  (what the user *actually* likes)
  • RAG nutrition knowledge           (evidence-based dietary guidance)
  • Gemini AI generation              (creative structured meal plans)
  • Local fallback templates          (works without an API key)

Public API
──────────
  generate_meal_plan(user_id, preferences)  →  plan dict
"""

import json
import datetime
import random

import streamlit as st

from core.database import (
    get_all_food_logs_range,
    get_user_by_id,
    save_lstm_weights,
    get_lstm_weights,
)
from core.lstm_model import (
    MealPatternLSTM,
    FOOD_CATEGORIES,
    MEAL_TYPES,
    categorize_food,
)
from core.rag_engine import build_rag_context, get_user_log_snapshot

DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


# ── LSTM helper ─────────────────────────────────────────────────────────────

def _get_or_train_lstm(user_id: int) -> MealPatternLSTM:
    model = MealPatternLSTM()
    saved = get_lstm_weights(user_id)
    if saved:
        try:
            model.load(json.loads(saved))
        except Exception:
            pass

    food_logs = get_all_food_logs_range(user_id, days=60)
    if len(food_logs) >= 5:
        model.train(food_logs, epochs=30, lr=0.01)
        save_lstm_weights(user_id, json.dumps(model.serialize()))
    return model


def _build_lstm_context(model: MealPatternLSTM, food_logs: list[dict]) -> str:
    lines = ["LSTM EATING-PATTERN ANALYSIS:"]

    top_foods = model.get_top_foods_by_meal(food_logs)
    for meal, foods in top_foods.items():
        if foods:
            lines.append(f"  {meal} favourites: {', '.join(foods[:3])}")

    avg_macros = model.get_avg_macros_by_meal(food_logs)
    for meal, m in avg_macros.items():
        if m["avg_calories"] > 0:
            lines.append(
                f"  {meal} avg: {m['avg_calories']}cal, "
                f"{m['avg_protein']}g prot, "
                f"{m['avg_carbs']}g carbs, "
                f"{m['avg_fat']}g fat"
            )

    lines.append("  Weekly category preferences (top-3 per slot):")
    for dow in range(7):
        for meal in ("Breakfast", "Lunch", "Dinner"):
            prefs = model.predict_preferences(food_logs, target_meal=meal, target_dow=dow)
            top = sorted(prefs.items(), key=lambda kv: kv[1], reverse=True)[:3]
            top_str = ", ".join(f"{c}({s:.0%})" for c, s in top if s > 0.05)
            if top_str:
                lines.append(f"    {DAYS_OF_WEEK[dow]} {meal}: {top_str}")

    return "\n".join(lines)


# ── Gemini-powered generation ───────────────────────────────────────────────

def _generate_with_ai(diet, daily_goal, meal_targets, week_start,
                      lstm_context, rag_context, allergies, cuisine, user):
    import google.generativeai as genai

    try:
        genai.configure(api_key=st.session_state["api_key"])
        ai = genai.GenerativeModel(st.session_state["active_model"])

        allergy_note = f"\nALLERGIES/RESTRICTIONS: {allergies}" if allergies else ""
        cuisine_note = f"\nPREFERRED CUISINES: {cuisine}" if cuisine else ""

        dates = [(week_start + datetime.timedelta(days=i)).isoformat() for i in range(7)]

        prompt = (
            f"Generate a detailed 7-day meal plan.  Return ONLY valid JSON — no markdown fences.\n\n"
            f"{rag_context}\n\n"
            f"{lstm_context}\n\n"
            f"USER: {user.get('age',25)}y {user.get('gender','Male')}, "
            f"{user.get('weight_kg',70)}kg, activity {user.get('activity','Active')}\n"
            f"DIET: {diet}\n"
            f"DAILY TARGET: {daily_goal} kcal\n"
            f"MEAL SPLIT: Breakfast ~{meal_targets['Breakfast']}cal, "
            f"Lunch ~{meal_targets['Lunch']}cal, "
            f"Dinner ~{meal_targets['Dinner']}cal, "
            f"Snack ~{meal_targets['Snack']}cal\n"
            f"{allergy_note}{cuisine_note}\n"
            f"WEEK: {dates[0]} (Mon) → {dates[6]} (Sun)\n\n"
            "Use the LSTM eating-pattern data to align the plan with the user's "
            "actual preferences and habits.  Respect their diet type and the "
            "knowledge-base nutrition guidelines.\n\n"
            "Return exactly this JSON structure:\n"
            "{\n"
            '  "days": [\n'
            "    {\n"
            '      "day": "Monday",\n'
            f'      "date": "{dates[0]}",\n'
            '      "meals": {\n'
            '        "Breakfast": {"name":"…","ingredients":["…"],"calories":0,'
            '"carbs":0,"protein":0,"fat":0,"description":"…"},\n'
            '        "Lunch": {…}, "Dinner": {…}, "Snack": {…}\n'
            "      }\n"
            "    }\n"
            "    … (all 7 days Monday–Sunday)\n"
            "  ],\n"
            '  "grocery_list": {\n'
            '    "Produce":["…"], "Protein":["…"], "Dairy":["…"],\n'
            '    "Grains":["…"], "Pantry":["…"]\n'
            "  }\n"
            "}\n"
        )

        resp = ai.generate_content(prompt)
        text = resp.text.replace("```json", "").replace("```", "").strip()
        plan = json.loads(text)

        plan["week_start"] = dates[0]
        plan["diet"] = diet
        plan["daily_goal"] = daily_goal

        for day in plan.get("days", []):
            meals = day.get("meals", {})
            day["total_calories"] = sum(m.get("calories", 0) for m in meals.values())
            day["total_protein"]  = sum(m.get("protein", 0)  for m in meals.values())
            day["total_carbs"]    = sum(m.get("carbs", 0)    for m in meals.values())
            day["total_fat"]      = sum(m.get("fat", 0)      for m in meals.values())

        return plan
    except Exception:
        return None


# ── Local fallback templates ────────────────────────────────────────────────

_TEMPLATES: dict[str, dict[str, list[dict]]] = {
    "Balanced": {
        "Breakfast": [
            {"name": "Greek Yogurt Parfait",      "ingredients": ["Greek yogurt", "mixed berries", "granola", "honey"],          "calories": 350, "carbs": 45, "protein": 20, "fat": 10, "description": "Layer yogurt with berries and crunchy granola"},
            {"name": "Scrambled Eggs & Toast",     "ingredients": ["eggs", "whole-wheat bread", "butter", "spinach"],            "calories": 400, "carbs": 30, "protein": 24, "fat": 20, "description": "Fluffy eggs with sautéed spinach on toast"},
            {"name": "Oatmeal with Banana",        "ingredients": ["rolled oats", "banana", "almond milk", "cinnamon"],          "calories": 320, "carbs": 55, "protein": 10, "fat": 6,  "description": "Warm oats topped with sliced banana"},
            {"name": "Smoothie Bowl",              "ingredients": ["frozen berries", "banana", "protein powder", "granola"],     "calories": 380, "carbs": 50, "protein": 22, "fat": 8,  "description": "Thick smoothie bowl with crunchy toppings"},
            {"name": "Avocado Toast with Egg",     "ingredients": ["sourdough bread", "avocado", "egg", "cherry tomatoes"],      "calories": 420, "carbs": 35, "protein": 18, "fat": 24, "description": "Smashed avo with a fried egg on top"},
            {"name": "Banana Pancakes",            "ingredients": ["banana", "eggs", "oat flour", "maple syrup"],                "calories": 380, "carbs": 52, "protein": 16, "fat": 12, "description": "Fluffy banana pancakes with maple drizzle"},
            {"name": "Overnight Chia Pudding",     "ingredients": ["chia seeds", "almond milk", "mango", "coconut flakes"],      "calories": 310, "carbs": 38, "protein": 10, "fat": 14, "description": "Creamy chia pudding with fresh mango"},
        ],
        "Lunch": [
            {"name": "Grilled Chicken Salad",      "ingredients": ["chicken breast", "mixed greens", "cucumber", "olive oil", "feta"], "calories": 480, "carbs": 15, "protein": 42, "fat": 28, "description": "Lean chicken over a bed of fresh greens"},
            {"name": "Turkey & Veggie Wrap",        "ingredients": ["whole-wheat tortilla", "turkey slices", "lettuce", "tomato", "hummus"], "calories": 420, "carbs": 38, "protein": 30, "fat": 16, "description": "Protein-packed wrap with creamy hummus"},
            {"name": "Quinoa Buddha Bowl",          "ingredients": ["quinoa", "chickpeas", "roasted vegetables", "tahini"],      "calories": 500, "carbs": 60, "protein": 20, "fat": 18, "description": "Colourful bowl with tahini dressing"},
            {"name": "Tuna Sandwich",               "ingredients": ["whole-wheat bread", "canned tuna", "Greek yogurt", "celery", "lettuce"], "calories": 440, "carbs": 35, "protein": 35, "fat": 16, "description": "Classic tuna sandwich with a lighter twist"},
            {"name": "Chicken Stir-Fry with Rice",  "ingredients": ["chicken breast", "brown rice", "bell peppers", "broccoli", "soy sauce"], "calories": 520, "carbs": 55, "protein": 38, "fat": 14, "description": "Quick stir-fry with colourful veggies"},
            {"name": "Lentil Soup & Bread",         "ingredients": ["red lentils", "carrots", "onion", "cumin", "whole-wheat bread"], "calories": 450, "carbs": 60, "protein": 24, "fat": 10, "description": "Hearty spiced lentil soup"},
            {"name": "Mediterranean Pasta",         "ingredients": ["penne pasta", "cherry tomatoes", "olives", "basil", "parmesan"], "calories": 490, "carbs": 62, "protein": 18, "fat": 18, "description": "Light pasta with Mediterranean flavours"},
        ],
        "Dinner": [
            {"name": "Baked Salmon & Vegetables",   "ingredients": ["salmon fillet", "asparagus", "lemon", "olive oil", "sweet potato"], "calories": 520, "carbs": 30, "protein": 40, "fat": 26, "description": "Oven-baked salmon with roasted veggies"},
            {"name": "Chicken Tikka with Rice",      "ingredients": ["chicken thigh", "yogurt", "spices", "basmati rice", "cucumber raita"], "calories": 550, "carbs": 50, "protein": 38, "fat": 20, "description": "Spiced grilled chicken with fragrant rice"},
            {"name": "Beef Stir-Fry & Noodles",     "ingredients": ["lean beef strips", "egg noodles", "bok choy", "garlic", "sesame oil"], "calories": 530, "carbs": 48, "protein": 36, "fat": 20, "description": "Savoury beef with tender noodles"},
            {"name": "Stuffed Bell Peppers",         "ingredients": ["bell peppers", "ground turkey", "brown rice", "tomato sauce", "cheese"], "calories": 450, "carbs": 35, "protein": 32, "fat": 18, "description": "Colourful peppers loaded with filling"},
            {"name": "Grilled Fish Tacos",           "ingredients": ["white fish", "corn tortillas", "cabbage slaw", "lime", "avocado"], "calories": 460, "carbs": 38, "protein": 34, "fat": 18, "description": "Light fish tacos with zesty slaw"},
            {"name": "Chicken & Vegetable Curry",    "ingredients": ["chicken breast", "coconut milk", "spinach", "chickpeas", "basmati rice"], "calories": 540, "carbs": 50, "protein": 36, "fat": 22, "description": "Creamy curry with a side of rice"},
            {"name": "Pasta Bolognese",              "ingredients": ["spaghetti", "lean ground beef", "tomato sauce", "onion", "parmesan"], "calories": 520, "carbs": 55, "protein": 34, "fat": 18, "description": "Classic bolognese with lean meat"},
        ],
        "Snack": [
            {"name": "Apple & Peanut Butter",        "ingredients": ["apple", "peanut butter"],               "calories": 200, "carbs": 22, "protein": 6, "fat": 12, "description": "Crunchy apple slices with PB"},
            {"name": "Trail Mix",                    "ingredients": ["almonds", "cashews", "dried cranberries", "dark chocolate chips"], "calories": 220, "carbs": 20, "protein": 6, "fat": 14, "description": "Energising nut and berry mix"},
            {"name": "Protein Smoothie",             "ingredients": ["protein powder", "banana", "almond milk"],  "calories": 230, "carbs": 28, "protein": 20, "fat": 4, "description": "Quick post-workout shake"},
            {"name": "Hummus & Veggie Sticks",       "ingredients": ["hummus", "carrot sticks", "celery", "cucumber"], "calories": 180, "carbs": 18, "protein": 6,  "fat": 10, "description": "Crunchy veggies with creamy hummus"},
            {"name": "Greek Yogurt & Honey",         "ingredients": ["Greek yogurt", "honey", "walnuts"],       "calories": 200, "carbs": 20, "protein": 14, "fat": 8,  "description": "Creamy yogurt with a drizzle of honey"},
            {"name": "Dark Chocolate & Almonds",     "ingredients": ["dark chocolate", "almonds"],              "calories": 210, "carbs": 16, "protein": 5,  "fat": 15, "description": "Rich chocolate paired with crunchy almonds"},
            {"name": "Rice Cakes with Avocado",      "ingredients": ["rice cakes", "avocado", "sea salt"],      "calories": 190, "carbs": 20, "protein": 3,  "fat": 12, "description": "Light and creamy rice cake topping"},
        ],
    },
    "Keto": {
        "Breakfast": [
            {"name": "Bacon & Eggs",                "ingredients": ["bacon", "eggs", "avocado"],                 "calories": 450, "carbs": 3,  "protein": 28, "fat": 36, "description": "Classic keto breakfast"},
            {"name": "Keto Omelette",               "ingredients": ["eggs", "cheese", "mushrooms", "spinach"],   "calories": 420, "carbs": 4,  "protein": 30, "fat": 32, "description": "Cheesy veggie omelette"},
            {"name": "Bulletproof Coffee & Eggs",   "ingredients": ["coffee", "butter", "MCT oil", "eggs"],      "calories": 400, "carbs": 1,  "protein": 14, "fat": 38, "description": "Energy-boosting coffee with eggs"},
            {"name": "Smoked Salmon Cream Cheese",  "ingredients": ["smoked salmon", "cream cheese", "cucumber", "capers"], "calories": 380, "carbs": 3, "protein": 24, "fat": 30, "description": "Elegant low-carb plate"},
            {"name": "Avocado Egg Cups",            "ingredients": ["avocado", "eggs", "bacon bits", "cheese"],  "calories": 430, "carbs": 5,  "protein": 22, "fat": 36, "description": "Baked eggs in avocado halves"},
        ],
        "Lunch": [
            {"name": "Caesar Salad (no croutons)",   "ingredients": ["romaine", "chicken breast", "parmesan", "Caesar dressing", "bacon"], "calories": 500, "carbs": 6, "protein": 40, "fat": 36, "description": "Crunchy keto Caesar"},
            {"name": "Lettuce-Wrap Burger",          "ingredients": ["ground beef patty", "lettuce", "cheese", "tomato", "pickles"], "calories": 520, "carbs": 5, "protein": 38, "fat": 40, "description": "Juicy burger in crisp lettuce"},
            {"name": "Tuna Salad Stuffed Avocado",   "ingredients": ["canned tuna", "avocado", "mayo", "celery"], "calories": 480, "carbs": 6, "protein": 32, "fat": 38, "description": "Creamy tuna in avocado boat"},
            {"name": "Zucchini Noodle Alfredo",      "ingredients": ["zucchini", "heavy cream", "parmesan", "garlic", "chicken"], "calories": 490, "carbs": 8, "protein": 34, "fat": 36, "description": "Creamy alfredo on zoodles"},
            {"name": "Grilled Chicken & Broccoli",   "ingredients": ["chicken thigh", "broccoli", "butter", "cheese"], "calories": 470, "carbs": 7, "protein": 40, "fat": 32, "description": "Simple cheesy chicken and broccoli"},
        ],
        "Dinner": [
            {"name": "Steak with Garlic Butter",     "ingredients": ["ribeye steak", "butter", "garlic", "asparagus"],  "calories": 580, "carbs": 4, "protein": 42, "fat": 44, "description": "Seared steak with herb butter"},
            {"name": "Salmon with Cauliflower Mash",  "ingredients": ["salmon", "cauliflower", "cream cheese", "butter", "dill"], "calories": 540, "carbs": 8, "protein": 38, "fat": 40, "description": "Flaky salmon on creamy cauli mash"},
            {"name": "Pork Chops & Sautéed Spinach",  "ingredients": ["pork chops", "spinach", "garlic", "olive oil", "mushrooms"], "calories": 500, "carbs": 5, "protein": 40, "fat": 36, "description": "Juicy chops with garlicky greens"},
            {"name": "Chicken Thigh Curry (no rice)", "ingredients": ["chicken thigh", "coconut cream", "curry paste", "spinach"], "calories": 520, "carbs": 8, "protein": 36, "fat": 40, "description": "Rich coconut curry"},
            {"name": "Shrimp Scampi (zoodles)",       "ingredients": ["shrimp", "zucchini noodles", "garlic", "butter", "white wine"], "calories": 460, "carbs": 7, "protein": 36, "fat": 32, "description": "Garlic butter shrimp on zoodles"},
        ],
        "Snack": [
            {"name": "Cheese & Olives",              "ingredients": ["cheddar cheese", "olives"],             "calories": 200, "carbs": 2, "protein": 10, "fat": 18, "description": "Simple savoury snack"},
            {"name": "Keto Fat Bombs",               "ingredients": ["coconut oil", "cocoa powder", "almond butter"], "calories": 210, "carbs": 3, "protein": 4, "fat": 22, "description": "Chocolate energy bites"},
            {"name": "Pork Rinds & Guacamole",       "ingredients": ["pork rinds", "avocado", "lime", "salt"],  "calories": 230, "carbs": 4, "protein": 10, "fat": 20, "description": "Crispy rinds with fresh guac"},
            {"name": "Celery with Cream Cheese",     "ingredients": ["celery", "cream cheese"],                "calories": 150, "carbs": 3, "protein": 4,  "fat": 14, "description": "Crunchy and creamy"},
            {"name": "Beef Jerky",                   "ingredients": ["beef jerky"],                            "calories": 160, "carbs": 3, "protein": 20, "fat": 8,  "description": "Protein-packed portable snack"},
        ],
    },
    "Vegan": {
        "Breakfast": [
            {"name": "Tofu Scramble & Toast",        "ingredients": ["firm tofu", "turmeric", "spinach", "whole-wheat toast", "nutritional yeast"], "calories": 380, "carbs": 35, "protein": 24, "fat": 16, "description": "Savoury tofu scramble on toast"},
            {"name": "Overnight Oats (vegan)",       "ingredients": ["rolled oats", "oat milk", "chia seeds", "banana", "maple syrup"], "calories": 340, "carbs": 56, "protein": 10, "fat": 8, "description": "Creamy overnight oats with chia"},
            {"name": "Smoothie Bowl",                "ingredients": ["frozen açai", "banana", "almond butter", "granola", "coconut flakes"], "calories": 400, "carbs": 52, "protein": 10, "fat": 18, "description": "Vibrant açai bowl with toppings"},
            {"name": "Peanut Butter Banana Toast",   "ingredients": ["whole-wheat bread", "peanut butter", "banana", "chia seeds"], "calories": 360, "carbs": 44, "protein": 12, "fat": 16, "description": "Simple energising toast"},
            {"name": "Chickpea Flour Pancakes",      "ingredients": ["chickpea flour", "water", "spinach", "tomato", "spices"], "calories": 320, "carbs": 38, "protein": 16, "fat": 10, "description": "Savoury protein-rich pancakes"},
        ],
        "Lunch": [
            {"name": "Lentil & Veggie Bowl",         "ingredients": ["green lentils", "roasted sweet potato", "kale", "tahini dressing"], "calories": 480, "carbs": 58, "protein": 22, "fat": 16, "description": "Hearty lentil power bowl"},
            {"name": "Falafel Wrap",                 "ingredients": ["falafel", "whole-wheat wrap", "hummus", "lettuce", "tomato"], "calories": 460, "carbs": 50, "protein": 18, "fat": 20, "description": "Crunchy falafel with creamy hummus"},
            {"name": "Black Bean Burrito Bowl",      "ingredients": ["black beans", "brown rice", "corn", "avocado", "salsa"], "calories": 500, "carbs": 65, "protein": 20, "fat": 16, "description": "Loaded Mexican-style bowl"},
            {"name": "Tofu Stir-Fry & Rice",         "ingredients": ["firm tofu", "brown rice", "broccoli", "soy sauce", "sesame oil"], "calories": 470, "carbs": 54, "protein": 24, "fat": 18, "description": "Crispy tofu with Asian veggies"},
            {"name": "Mediterranean Chickpea Salad",  "ingredients": ["chickpeas", "cucumber", "tomato", "red onion", "lemon-tahini dressing"], "calories": 420, "carbs": 48, "protein": 18, "fat": 18, "description": "Fresh and filling salad"},
        ],
        "Dinner": [
            {"name": "Chickpea & Spinach Curry",     "ingredients": ["chickpeas", "spinach", "coconut milk", "tomato sauce", "basmati rice"], "calories": 520, "carbs": 60, "protein": 20, "fat": 22, "description": "Creamy coconut curry with rice"},
            {"name": "Stuffed Sweet Potatoes",        "ingredients": ["sweet potatoes", "black beans", "corn", "avocado", "salsa"], "calories": 480, "carbs": 62, "protein": 16, "fat": 18, "description": "Loaded sweet potato boats"},
            {"name": "Pasta Primavera (vegan)",       "ingredients": ["penne pasta", "zucchini", "bell peppers", "cherry tomatoes", "olive oil"], "calories": 460, "carbs": 62, "protein": 14, "fat": 16, "description": "Pasta loaded with fresh veggies"},
            {"name": "Teriyaki Tofu & Noodles",       "ingredients": ["tofu", "soba noodles", "edamame", "carrots", "teriyaki sauce"], "calories": 500, "carbs": 56, "protein": 26, "fat": 18, "description": "Sweet and savoury noodle bowl"},
            {"name": "Mushroom & Lentil Shepherd's Pie", "ingredients": ["lentils", "mushrooms", "potatoes", "peas", "onion"], "calories": 490, "carbs": 60, "protein": 22, "fat": 16, "description": "Comforting plant-based pie"},
        ],
        "Snack": [
            {"name": "Hummus & Veggie Sticks",       "ingredients": ["hummus", "carrot", "celery", "cucumber"],  "calories": 180, "carbs": 18, "protein": 6, "fat": 10, "description": "Crunchy fresh veggies and hummus"},
            {"name": "Energy Balls",                  "ingredients": ["dates", "oats", "peanut butter", "cocoa"],  "calories": 200, "carbs": 28, "protein": 6, "fat": 8,  "description": "No-bake date and oat bites"},
            {"name": "Mixed Nuts & Dried Fruit",      "ingredients": ["almonds", "cashews", "raisins"],           "calories": 220, "carbs": 20, "protein": 6, "fat": 14, "description": "Energising trail mix"},
            {"name": "Edamame",                       "ingredients": ["frozen edamame", "sea salt"],              "calories": 190, "carbs": 14, "protein": 18, "fat": 8,  "description": "Protein-packed soy beans"},
            {"name": "Fruit & Nut Butter",            "ingredients": ["apple", "almond butter"],                  "calories": 200, "carbs": 24, "protein": 4,  "fat": 12, "description": "Sweet fruit with creamy nut butter"},
        ],
    },
}


def _pick_template_meal(templates: list[dict], preferred_cats: dict[str, float],
                        used_names: set) -> dict:
    """Select a template meal biased toward LSTM-preferred food categories."""
    scored = []
    for t in templates:
        if t["name"] in used_names:
            continue
        cat = categorize_food(t["name"])
        score = preferred_cats.get(cat, 0.05)
        scored.append((score, t))

    if not scored:
        scored = [(0.1, t) for t in templates]

    scored.sort(key=lambda x: x[0], reverse=True)
    # Weighted random from top half
    top = scored[:max(len(scored) // 2, 1)]
    weights = [s for s, _ in top]
    total = sum(weights) or 1
    probs = [w / total for w in weights]
    choice = random.choices(top, weights=probs, k=1)[0][1]
    return choice


def _scale_meal(meal: dict, target_cal: int) -> dict:
    """Scale a template meal's macros to approximately match a calorie target."""
    if meal["calories"] <= 0:
        return meal
    ratio = target_cal / meal["calories"]
    return {
        **meal,
        "calories": target_cal,
        "carbs": round(meal["carbs"] * ratio),
        "protein": round(meal["protein"] * ratio),
        "fat": round(meal["fat"] * ratio),
    }


def _generate_local_plan(diet, daily_goal, meal_targets, week_start,
                         model: MealPatternLSTM, food_logs, user):
    """Template-based fallback when Gemini is unavailable."""
    diet_key = "Balanced"
    if "Keto" in diet:
        diet_key = "Keto"
    elif "Vegan" in diet:
        diet_key = "Vegan"

    templates = _TEMPLATES[diet_key]
    days = []
    all_ingredients: list[str] = []
    used_per_meal: dict[str, set] = {m: set() for m in MEAL_TYPES}

    for dow in range(7):
        day_date = (week_start + datetime.timedelta(days=dow)).isoformat()
        meals_out: dict[str, dict] = {}

        for meal_type in MEAL_TYPES:
            prefs = model.predict_preferences(food_logs, target_meal=meal_type, target_dow=dow)
            choice = _pick_template_meal(templates[meal_type], prefs, used_per_meal[meal_type])
            used_per_meal[meal_type].add(choice["name"])
            scaled = _scale_meal(choice, meal_targets[meal_type])
            meals_out[meal_type] = scaled
            all_ingredients.extend(choice["ingredients"])

        total_cal  = sum(m["calories"] for m in meals_out.values())
        total_prot = sum(m["protein"]  for m in meals_out.values())
        total_carb = sum(m["carbs"]    for m in meals_out.values())
        total_fat  = sum(m["fat"]      for m in meals_out.values())

        days.append({
            "day": DAYS_OF_WEEK[dow],
            "date": day_date,
            "meals": meals_out,
            "total_calories": total_cal,
            "total_protein": total_prot,
            "total_carbs": total_carb,
            "total_fat": total_fat,
        })

    grocery = _build_grocery_list(all_ingredients)

    return {
        "week_start": week_start.isoformat(),
        "diet": diet,
        "daily_goal": daily_goal,
        "days": days,
        "grocery_list": grocery,
    }


# ── Grocery list builder ────────────────────────────────────────────────────

_GROCERY_CATEGORIES: dict[str, list[str]] = {
    "Produce": [
        "apple", "banana", "berry", "berries", "blueberry", "strawberry", "mango",
        "avocado", "tomato", "spinach", "kale", "lettuce", "broccoli", "carrot",
        "cucumber", "pepper", "onion", "garlic", "mushroom", "asparagus", "celery",
        "zucchini", "cabbage", "corn", "pea", "sweet potato", "potato", "lemon",
        "lime", "cherry", "edamame", "bok choy", "cauliflower", "eggplant", "fruit",
        "vegetable", "romaine",
    ],
    "Protein": [
        "chicken", "beef", "turkey", "pork", "salmon", "fish", "shrimp", "tuna",
        "egg", "tofu", "tempeh", "lentil", "chickpea", "black bean", "bean",
        "bacon", "steak", "lamb", "prawn", "sausage", "falafel", "jerky",
    ],
    "Dairy": [
        "milk", "cheese", "yogurt", "butter", "cream", "paneer", "whey",
        "cream cheese", "feta", "parmesan", "curd", "mozzarella",
    ],
    "Grains": [
        "rice", "bread", "pasta", "oat", "tortilla", "noodle", "quinoa",
        "bagel", "cereal", "couscous", "flour", "wrap", "pita", "spaghetti",
        "penne", "granola", "rice cake",
    ],
    "Pantry": [
        "oil", "honey", "maple syrup", "soy sauce", "spice", "salt", "pepper",
        "cumin", "turmeric", "cinnamon", "cocoa", "chocolate", "nut butter",
        "peanut butter", "almond butter", "tahini", "hummus", "salsa",
        "vinegar", "coconut", "chia", "flaxseed", "nutritional yeast",
        "protein powder", "MCT oil", "sesame oil", "teriyaki",
    ],
}


def _classify_ingredient(name: str) -> str:
    lower = name.lower()
    for category, keywords in _GROCERY_CATEGORIES.items():
        if any(kw in lower for kw in keywords):
            return category
    return "Pantry"


def _build_grocery_list(ingredients: list[str]) -> dict[str, list[str]]:
    unique = sorted(set(i.strip() for i in ingredients if i.strip()))
    grocery: dict[str, list[str]] = {cat: [] for cat in _GROCERY_CATEGORIES}
    for item in unique:
        cat = _classify_ingredient(item)
        grocery[cat].append(item)
    return {k: v for k, v in grocery.items() if v}


# ── Public API ──────────────────────────────────────────────────────────────

def generate_meal_plan(user_id: int, preferences: dict | None = None) -> dict:
    """
    Generate a structured 7-day meal plan.

    Parameters
    ----------
    user_id : int
    preferences : dict, optional
        Keys: diet, daily_goal, allergies, cuisine
    """
    preferences = preferences or {}
    user = get_user_by_id(user_id)
    if not user:
        return {"error": "User not found"}

    diet       = preferences.get("diet",       user.get("diet", "Balanced"))
    daily_goal = preferences.get("daily_goal", user.get("daily_goal", 2000))
    allergies  = preferences.get("allergies",  "")
    cuisine    = preferences.get("cuisine",    "")

    food_logs = get_all_food_logs_range(user_id, days=60)
    model = _get_or_train_lstm(user_id)

    lstm_context = _build_lstm_context(model, food_logs) if food_logs else "No eating history available."

    rag_query  = f"weekly meal plan {diet} diet {daily_goal} calories balanced nutrition meal prep"
    rag_context = build_rag_context(rag_query, top_k=4, user_id=user_id, days=7)

    meal_targets = {
        "Breakfast": int(daily_goal * 0.25),
        "Lunch":     int(daily_goal * 0.35),
        "Dinner":    int(daily_goal * 0.30),
        "Snack":     int(daily_goal * 0.10),
    }

    today = datetime.date.today()
    days_ahead = (7 - today.weekday()) % 7 or 7
    week_start = today + datetime.timedelta(days=days_ahead)

    # Try AI-powered generation first
    if st.session_state.get("api_key") and st.session_state.get("active_model"):
        plan = _generate_with_ai(
            diet, daily_goal, meal_targets, week_start,
            lstm_context, rag_context, allergies, cuisine, user,
        )
        if plan and "error" not in plan:
            return plan

    # Fallback to local templates
    return _generate_local_plan(
        diet, daily_goal, meal_targets, week_start,
        model, food_logs, user,
    )
