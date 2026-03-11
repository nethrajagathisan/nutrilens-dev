import streamlit as st
import pandas as pd

from core.database import get_food_logs_today, clear_food_logs_today


def render_diary():
    st.subheader("📊 Your Daily Progress")

    uid = st.session_state["user_id"]
    logs = get_food_logs_today(uid)

    if logs:
        df = pd.DataFrame(logs)
        # Rename DB columns to display-friendly names
        df = df.rename(columns={
            "calories": "cals",
            "protein": "prot",
        })
        total = df["cals"].sum()

        st.metric(
            "Total Calories",
            f"{total}",
            f"Target: {st.session_state['daily_goal']}",
        )
        st.progress(min(total / st.session_state["daily_goal"], 1.0))

        b1, b2, b3 = st.columns(3)
        b1.metric("Carbs", f"{df['carbs'].sum()}g")
        b2.metric("Protein", f"{df['prot'].sum()}g")
        b3.metric("Fat", f"{df['fat'].sum()}g")

        display_df = df[["name", "cals", "carbs", "prot", "fat", "meal", "logged_at"]]
        st.dataframe(display_df, use_container_width=True)
        if st.button("Clear History"):
            clear_food_logs_today(uid)
            st.rerun()
    else:
        st.info("Empty! Eat something yummy 😋")
