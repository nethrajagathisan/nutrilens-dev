"""Insights section — groups Analytics, Micronutrients, Fingerprint, and AI Coach."""

import streamlit as st

from app.analytics import render_analytics
from app.micronutrients import render_micronutrients
from app.fingerprint import render_fingerprint
from app.rag_chat import render_rag_chat


def render_insights_section():
    st.markdown(
        '<div class="section-header" style="font-size:1.4rem;">📊 Insights</div>',
        unsafe_allow_html=True,
    )

    tab_analytics, tab_micro, tab_finger, tab_coach = st.tabs(
        ["📉 Analytics", "🔬 Micronutrients", "🧠 Fingerprint", "💬 AI Coach"]
    )

    with tab_analytics:
        render_analytics()

    with tab_micro:
        render_micronutrients()

    with tab_finger:
        render_fingerprint()

    with tab_coach:
        render_rag_chat()
