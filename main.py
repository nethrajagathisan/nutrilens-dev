import streamlit as st

from config.settings import PAGE_CONFIG, init_session_state
from config.styles import inject_css
from components.sidebar import render_sidebar
from app.auth import render_auth

# Import page render functions
from app.home import render_home
from app.log_section import render_log_section
from app.insights_section import render_insights_section
from app.plans_section import render_plans_section
from app.profile_section import render_profile_section

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

# --- Sidebar Widgets (AI, hydration, coach) ---
# Note: Streamlit's native navigation will automatically append itself to the sidebar.
render_sidebar()

# --- Page Router using st.navigation and st.Page ---
pages = {
    "Main Dashboard": [
        st.Page(render_home, title="Overview", icon=":material/home:", default=True),
        st.Page(render_profile_section, title="User Profile", icon=":material/person:"),
    ],
    "Logging & Tracking": [
        st.Page(render_log_section, title="Log Hub", icon=":material/edit_document:"),
        st.Page(render_tracker, title="Food Tracker", icon=":material/restaurant:"),
        st.Page(render_scanner, title="Fast Scanner", icon=":material/qr_code_scanner:"),
        st.Page(render_voice_logger, title="Voice Logger", icon=":material/mic:"),
        st.Page(render_exercise_logger, title="Exercise", icon=":material/fitness_center:"),
        st.Page(render_diary, title="Diary", icon=":material/book:"),
    ],
    "Insights & AI Coach": [
        st.Page(render_insights_section, title="Insights Hub", icon=":material/lightbulb:"),
        st.Page(render_analytics, title="Analytics", icon=":material/analytics:"),
        st.Page(render_fingerprint, title="Metabolic Fingerprint", icon=":material/fingerprint:"),
        st.Page(render_rl_dashboard, title="Adaptive Dashboard", icon=":material/tune:"),
        st.Page(render_rag_chat, title="Nutrition Coach", icon=":material/chat:"),
    ],
    "Plans & Nutrition": [
        st.Page(render_plans_section, title="Plans Hub", icon=":material/list_alt:"),
        st.Page(render_meal_planner, title="Meal Planner", icon=":material/calendar_today:"),
        st.Page(render_recipes, title="Recipes", icon=":material/local_dining:"),
        st.Page(render_micronutrients, title="Micronutrients", icon=":material/science:"),
    ],
    "Extras": [
        st.Page(render_achievements, title="Achievements", icon=":material/emoji_events:"),
        st.Page(render_data_export, title="Data Export", icon=":material/download:"),
    ]
}

# Initialize navigation
pg = st.navigation(pages)

# Run the selected page
pg.run()
