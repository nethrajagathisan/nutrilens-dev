import streamlit as st

from config.settings import PAGE_CONFIG, init_session_state
from config.styles import inject_css
from components.sidebar import render_topnav, render_sidebar
from app.auth import render_auth
from app.home import render_home
from app.log_section import render_log_section
from app.insights_section import render_insights_section
from app.plans_section import render_plans_section
from app.profile_section import render_profile_section

# Legacy imports — still used when navigating to specific sub-pages
from app.scanner import render_scanner
from app.tracker import render_tracker
from app.recipes import render_recipes
from app.diary import render_diary
from app.analytics import render_analytics
from app.fingerprint import render_fingerprint
from app.rl_dashboard import render_rl_dashboard
from app.rag_chat import render_rag_chat
from app.meal_planner import render_meal_planner
from app.micronutrients import render_micronutrients
from app.exercise_logger import render_exercise_logger
from app.voice_logger import render_voice_logger
from app.data_export import render_data_export
from app.achievements import render_achievements

# --- Bootstrap ---
st.set_page_config(**PAGE_CONFIG)
inject_css()
init_session_state()

# --- Auth Gate ---
if not st.session_state["logged_in"]:
    render_auth()
    st.stop()

# --- Top Navigation Bar ---
render_topnav()

# --- Sidebar (AI, hydration, coach) ---
render_sidebar()

# --- Page Router ---
page = st.session_state.get("page", "Home")

# Primary section routing
if page == "Home":
    render_home()
elif page == "Log":
    render_log_section()
elif page == "Insights":
    render_insights_section()
elif page == "Plans":
    render_plans_section()
elif page == "Profile":
    render_profile_section()

# Legacy page routing (for quick-action buttons that link to specific pages)
elif "Scan" in page:
    render_scanner()
elif "Tracker" in page:
    render_tracker()
elif "Recipe" in page:
    render_recipes()
elif "Diary" in page:
    render_diary()
elif "Analytics" in page:
    render_analytics()
elif "Fingerprint" in page:
    render_fingerprint()
elif "Adaptive" in page:
    render_rl_dashboard()
elif "Meal Planner" in page:
    render_meal_planner()
elif "Coach" in page or "Nutrition" in page:
    render_rag_chat()
elif "Micronutrient" in page:
    render_micronutrients()
elif "Exercise" in page:
    render_exercise_logger()
elif "Voice" in page:
    render_voice_logger()
elif "Export" in page:
    render_data_export()
elif "Achievement" in page:
    render_achievements()
else:
    render_home()
