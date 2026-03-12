"""Plans section — groups Meal Planner, Adaptive Goals, and Recipes."""

import streamlit as st

from app.meal_planner import render_meal_planner
from app.rl_dashboard import render_rl_dashboard
from app.recipes import render_recipes


def render_plans_section():
    st.markdown(
        '<div class="section-header" style="font-size:1.4rem;">📋 Plans</div>',
        unsafe_allow_html=True,
    )

    tab_meals, tab_adaptive, tab_recipes = st.tabs(
        ["🗓️ Meal Planner", "🔁 Adaptive Goals", "🍽️ Saved Recipes"]
    )

    with tab_meals:
        render_meal_planner()

    with tab_adaptive:
        render_rl_dashboard()

    with tab_recipes:
        render_recipes()
