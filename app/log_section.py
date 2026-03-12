"""Log section — groups Food, Exercise, Water, and Weight logging under tabs."""

import streamlit as st

from app.scanner import render_scanner
from app.tracker import render_tracker
from app.voice_logger import render_voice_logger
from app.exercise_logger import render_exercise_logger
from app.diary import render_diary


def render_log_section():
    st.markdown(
        '<div class="section-header" style="font-size:1.4rem;">📝 Log</div>',
        unsafe_allow_html=True,
    )

    tab_food, tab_scan, tab_voice, tab_exercise, tab_diary = st.tabs(
        ["🍽️ Food", "📸 Scan", "🎙️ Voice", "🏋️ Exercise", "📊 Diary"]
    )

    with tab_food:
        render_tracker()

    with tab_scan:
        render_scanner()

    with tab_voice:
        render_voice_logger()

    with tab_exercise:
        render_exercise_logger()

    with tab_diary:
        render_diary()
