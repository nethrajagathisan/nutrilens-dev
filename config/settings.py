import streamlit as st
from core.database import init_db, get_or_create_user, get_hydration_today

PAGE_CONFIG = {
    "page_title": "NutriLens",
    "page_icon": "🥑",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

SESSION_DEFAULTS = {
    "page": "Home",
    "scan_data": None,
    "api_key": "",
    "active_model": None,
    "chat_history": [],
    "recipe_result": None,
}


def init_session_state():
    # Create tables on first run
    init_db()

    for k, v in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Load user from DB
    if "user_id" not in st.session_state:
        user = get_or_create_user("default")
        st.session_state["user_id"] = user["id"]
        st.session_state["daily_goal"] = user["daily_goal"]
        st.session_state["bmi"] = user["bmi"]
        st.session_state["user_diet"] = user["diet"]
        st.session_state["water_ml"] = get_hydration_today(user["id"])
