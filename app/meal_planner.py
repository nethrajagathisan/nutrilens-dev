"""
AI Weekly Meal Planner page.

Generates personalised 7-day meal plans using LSTM pattern prediction,
RAG nutrition knowledge, and Gemini AI.  Displays structured plans with
macro breakdowns and categorised grocery lists.
"""

import json
import streamlit as st
import plotly.graph_objects as go

from core.meal_planner import generate_meal_plan, DAYS_OF_WEEK
from core.database import save_meal_plan, get_meal_plans, delete_meal_plan

# ── Chart theme (matches the rest of the app) ──────────────────────────────

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(20,20,30,0.6)",
    font=dict(color="white", family="Poppins, sans-serif"),
    margin=dict(t=30, b=20, l=10, r=10),
)

_MEAL_COLOURS = {
    "Breakfast": "#FFD700",
    "Lunch":     "#85E3FF",
    "Dinner":    "#B9FBC0",
    "Snack":     "#FFABAB",
}


def render_meal_planner():
    st.markdown(
        "<h2 style='color:#FFD700;'>🗓️ AI Weekly Meal Planner</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Generate a personalised 7-day meal plan powered by your eating patterns (LSTM), "
        "nutrition science (RAG), and AI creativity."
    )

    uid = st.session_state.get("user_id")
    if not uid:
        st.warning("Please log in first.")
        return

    tab_gen, tab_saved, tab_grocery = st.tabs(
        ["📝 Generate Plan", "📂 Saved Plans", "🛒 Grocery List"]
    )

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 1 — Generate
    # ════════════════════════════════════════════════════════════════════════
    with tab_gen:
        _render_generate(uid)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 2 — Saved Plans
    # ════════════════════════════════════════════════════════════════════════
    with tab_saved:
        _render_saved(uid)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 3 — Grocery List
    # ════════════════════════════════════════════════════════════════════════
    with tab_grocery:
        _render_grocery()


# ── Generate tab ────────────────────────────────────────────────────────────

def _render_generate(uid: int):
    c1, c2 = st.columns(2)
    diet = c1.selectbox("🥗 Diet", ["Balanced ⚖️", "Keto 🥩", "Vegan 🥗"], key="mp_diet")
    daily_goal = c2.number_input(
        "🎯 Daily Calorie Goal", 1200, 5000,
        value=st.session_state.get("daily_goal", 2000), step=50, key="mp_goal",
    )
    c3, c4 = st.columns(2)
    allergies = c3.text_input("⚠️ Allergies / Restrictions (optional)", key="mp_allergy")
    cuisine = c4.text_input("🌍 Preferred Cuisine (optional)", key="mp_cuisine")

    if st.button("✨ Generate 7-Day Plan", type="primary", use_container_width=True):
        with st.spinner("Training LSTM on your eating patterns & building your plan…"):
            plan = generate_meal_plan(uid, {
                "diet": diet,
                "daily_goal": daily_goal,
                "allergies": allergies,
                "cuisine": cuisine,
            })

        if "error" in plan:
            st.error(f"Could not generate plan: {plan['error']}")
            return

        st.session_state["current_meal_plan"] = plan
        st.success("Meal plan ready! 🎉")

    plan = st.session_state.get("current_meal_plan")
    if not plan:
        st.info("Configure your preferences above and tap **Generate** to create a personalised plan.")
        return

    # ── plan display ────────────────────────────────────────────────────────
    _display_plan(plan)

    # ── save button ─────────────────────────────────────────────────────────
    st.write("---")
    scol1, scol2 = st.columns([3, 1])
    title = scol1.text_input("Plan title", value=f"Meal Plan – {plan.get('week_start', '')}", key="mp_save_title")
    if scol2.button("💾 Save Plan", use_container_width=True):
        save_meal_plan(
            uid,
            title=title,
            week_start=plan.get("week_start", ""),
            diet=plan.get("diet", ""),
            daily_goal=plan.get("daily_goal", 2000),
            plan_json=json.dumps(plan.get("days", [])),
            grocery_json=json.dumps(plan.get("grocery_list", {})),
        )
        st.success("Plan saved! ✅")


# ── Saved plans tab ─────────────────────────────────────────────────────────

def _render_saved(uid: int):
    plans = get_meal_plans(uid)
    if not plans:
        st.info("No saved plans yet.  Generate one in the first tab!")
        return

    st.caption(f"{len(plans)} saved plan(s)")
    for p in plans:
        with st.expander(f"📋 {p['title']}  •  {p['week_start']}  •  {p['diet']}", expanded=False):
            try:
                days = json.loads(p["plan_json"])
                grocery = json.loads(p["grocery_json"])
                full_plan = {
                    "days": days,
                    "grocery_list": grocery,
                    "diet": p["diet"],
                    "daily_goal": p["daily_goal"],
                    "week_start": p["week_start"],
                }
                _display_plan(full_plan)
            except Exception:
                st.warning("Could not parse this plan.")

            bcol1, bcol2 = st.columns([3, 1])
            if bcol1.button("📋 Load as Active Plan", key=f"mp_load_{p['id']}"):
                st.session_state["current_meal_plan"] = full_plan
                st.success("Plan loaded!")
                st.rerun()
            if bcol2.button("🗑️ Delete", key=f"mp_del_{p['id']}"):
                delete_meal_plan(p["id"], uid)
                st.rerun()


# ── Grocery list tab ────────────────────────────────────────────────────────

_GROCERY_EMOJI = {
    "Produce": "🥬", "Protein": "🥩", "Dairy": "🧀",
    "Grains": "🌾", "Pantry": "🫙",
}


def _render_grocery():
    plan = st.session_state.get("current_meal_plan")
    if not plan or "grocery_list" not in plan:
        st.info("Generate or load a meal plan first to see the grocery list.")
        return

    grocery = plan["grocery_list"]
    if not grocery:
        st.info("No grocery items in this plan.")
        return

    st.markdown(
        f"<h4 style='color:#85E3FF;'>🛒 Grocery List — {plan.get('week_start', '')}</h4>",
        unsafe_allow_html=True,
    )

    total_items = sum(len(v) for v in grocery.values())
    st.caption(f"{total_items} items across {len(grocery)} categories")

    cols = st.columns(min(len(grocery), 3))
    for idx, (category, items) in enumerate(grocery.items()):
        with cols[idx % len(cols)]:
            emoji = _GROCERY_EMOJI.get(category, "📦")
            st.markdown(
                f"<div style='background:rgba(30,30,45,0.85); border-radius:14px; "
                f"padding:1rem 1.2rem; margin-bottom:0.8rem;'>"
                f"<h4 style='margin:0 0 0.5rem 0;'>{emoji} {category}</h4>"
                + "".join(f"<div style='padding:2px 0; color:#ccc;'>• {item}</div>" for item in items)
                + "</div>",
                unsafe_allow_html=True,
            )


# ── Plan display helper ────────────────────────────────────────────────────

def _display_plan(plan: dict):
    days = plan.get("days", [])

    # ── Weekly overview bar chart ───────────────────────────────────────────
    if days:
        _render_weekly_overview(days, plan.get("daily_goal", 2000))

    # ── Day-by-day cards ────────────────────────────────────────────────────
    for day in days:
        day_name = day.get("day", "")
        date_str = day.get("date", "")
        meals = day.get("meals", {})

        with st.expander(f"📅 {day_name}  •  {date_str}  —  {day.get('total_calories', 0)} kcal", expanded=False):
            # Macro summary row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🔥 Calories", f"{day.get('total_calories', 0)} kcal")
            m2.metric("🥩 Protein",  f"{day.get('total_protein', 0)}g")
            m3.metric("🌾 Carbs",    f"{day.get('total_carbs', 0)}g")
            m4.metric("🧈 Fat",      f"{day.get('total_fat', 0)}g")

            # Meal cards
            for meal_type in ("Breakfast", "Lunch", "Dinner", "Snack"):
                meal = meals.get(meal_type, {})
                if not meal:
                    continue
                colour = _MEAL_COLOURS.get(meal_type, "#ccc")
                ingredients = meal.get("ingredients", [])
                if isinstance(ingredients, list):
                    ingr_str = ", ".join(ingredients)
                else:
                    ingr_str = str(ingredients)

                st.markdown(
                    f"<div style='background:rgba(30,30,45,0.85); border-left:4px solid {colour}; "
                    f"border-radius:12px; padding:0.8rem 1.1rem; margin:0.4rem 0;'>"
                    f"<strong style='color:{colour};'>{meal_type}</strong> — "
                    f"<span style='color:white; font-weight:600;'>{meal.get('name', '')}</span>"
                    f"<br><span style='color:#aaa; font-size:0.88rem;'>{meal.get('description', '')}</span>"
                    f"<br><span style='color:#888; font-size:0.82rem;'>🧾 {ingr_str}</span>"
                    f"<br><span style='font-size:0.82rem; color:#ccc;'>"
                    f"  {meal.get('calories', 0)} kcal  •  "
                    f"  P {meal.get('protein', 0)}g  •  "
                    f"  C {meal.get('carbs', 0)}g  •  "
                    f"  F {meal.get('fat', 0)}g"
                    f"</span></div>",
                    unsafe_allow_html=True,
                )

            # Day donut chart
            if any(meals.get(m, {}).get("calories", 0) for m in MEAL_COLOURS):
                fig = go.Figure(data=[go.Pie(
                    labels=[m for m in _MEAL_COLOURS if meals.get(m)],
                    values=[meals.get(m, {}).get("calories", 0) for m in _MEAL_COLOURS if meals.get(m)],
                    hole=0.55,
                    marker_colors=[_MEAL_COLOURS[m] for m in _MEAL_COLOURS if meals.get(m)],
                    textinfo="label+percent",
                )])
                fig.update_layout(**_LAYOUT, height=200, showlegend=False)
                st.plotly_chart(fig, use_container_width=True,
                                key=f"mp_pie_{day_name}")


def _render_weekly_overview(days: list[dict], daily_goal: int):
    """Stacked bar chart: calories per meal type across the week."""
    day_labels = [d.get("day", "")[:3] for d in days]

    fig = go.Figure()
    for meal_type in ("Breakfast", "Lunch", "Dinner", "Snack"):
        vals = [d.get("meals", {}).get(meal_type, {}).get("calories", 0) for d in days]
        fig.add_trace(go.Bar(
            name=meal_type, x=day_labels, y=vals,
            marker_color=_MEAL_COLOURS.get(meal_type, "#ccc"),
        ))

    fig.add_trace(go.Scatter(
        x=day_labels, y=[daily_goal] * len(day_labels),
        mode="lines", name="Goal",
        line=dict(color="#FF5252", width=2, dash="dash"),
    ))

    fig.update_layout(
        **_LAYOUT, barmode="stack", height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        yaxis_title="Calories",
    )
    st.plotly_chart(fig, use_container_width=True, key="mp_overview")


# fix the reference — MEAL_COLOURS used inside _display_plan
MEAL_COLOURS = _MEAL_COLOURS
