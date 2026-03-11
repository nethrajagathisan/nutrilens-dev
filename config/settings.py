import streamlit as st
from core.database import init_db

PAGE_CONFIG = {
    "page_title": "NutriLens",
    "page_icon": "🥑",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

SESSION_DEFAULTS = {
    # Auth
    "logged_in": False,
    "user_id": None,
    "username": "",
    # App state
    "page": "Home",
    "scan_data": None,
    "api_key": "",
    "active_model": None,
    "chat_history": [],
    "recipe_result": None,
    # User profile (populated after login)
    "daily_goal": 2000,
    "bmi": 0.0,
    "user_diet": "Balanced",
    "water_ml": 0,
}


def init_session_state():
    # Create tables on first run
    init_db()

    for k, v in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
