import streamlit as st

PAGE_CONFIG = {
    "page_title": "NutriLens",
    "page_icon": "🥑",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

SESSION_DEFAULTS = {
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
}


def init_session_state():
    for k, v in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
