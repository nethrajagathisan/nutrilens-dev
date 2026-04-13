import os
import streamlit as st
from dotenv import load_dotenv

from core.database import init_db

# Load .env file at import time
load_dotenv()

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
    # Hydration target (configurable, not hardcoded)
    "hydration_target": 3000,
}


def _auto_connect_ai():
    """Load GEMINI_API_KEY from .env and auto-connect the best model."""
    if st.session_state.get("active_model"):
        return  # already connected

    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not env_key:
        return  # no key configured

    from core.ai_engine import connect_to_best_model

    model = connect_to_best_model(env_key)
    if model:
        st.session_state["api_key"] = env_key
        st.session_state["active_model"] = model


def init_session_state():
    init_db()
    for k, v in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Auto-connect AI from .env on first run
    _auto_connect_ai()
