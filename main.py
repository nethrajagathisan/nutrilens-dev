import streamlit as st

from config.settings import PAGE_CONFIG, init_session_state
from config.styles import inject_css
from components.sidebar import render_sidebar
from app.home import render_home
from app.scanner import render_scanner
from app.diary import render_diary
from app.tracker import render_tracker
from app.analytics import render_analytics
from app.auth import render_auth

# --- Bootstrap ---
st.set_page_config(**PAGE_CONFIG)
inject_css()
init_session_state()

# --- Auth Gate ---
if not st.session_state["logged_in"]:
    render_auth()
    st.stop()

# --- Sidebar (nav + widgets) ---
render_sidebar()

# --- Page Router ---
page = st.session_state["page"]

if "Home" in page:
    render_home()
elif "Scan" in page:
    render_scanner()
elif "Tracker" in page:
    render_tracker()
elif "Analytics" in page:
    render_analytics()
elif "Diary" in page:
    render_diary()
