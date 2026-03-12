import streamlit as st

from core.database import init_db

PAGE_CONFIG = {
    "page_title": "NutriLens",
    "page_icon": "🥑",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}

SESSION_DEFAULTS = {
    "logged_in": False,
    "user_id": None,
    "username": "",
    "page": "Home",
    "food_log": [],
    "scan_data": None,
    "api_key": "",
    "active_model": None,
    "daily_goal": 2000,
    "bmi": 0.0,
    "chat_history": [],
    "user_diet": "Balanced",
    "water_ml": 0,
    "recipe_result": None,
    "fridge_items": None,
    "fridge_recipes": None,
    "barcode_result": None,
    "rag_chat_history": [],
    "coach_last_insight": "",
    "coach_last_sources": [],
    "current_meal_plan": None,
    # Onboarding state
    "onboarding_step": 1,
    "onboarding_data": {},
    "onboarding_done": False,
    # Goal tracking
    "target_weight": 0.0,
    "goal_type": "maintain",
    "goal_pace": "medium",
}


def init_session_state():
    init_db()
    for k, v in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
