import streamlit as st
import pandas as pd


def render_diary():
    st.subheader("📊 Your Daily Progress")

    if st.session_state["food_log"]:
        df = pd.DataFrame(st.session_state["food_log"])
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

        st.dataframe(df, use_container_width=True)
        if st.button("Clear History"):
            st.session_state["food_log"] = []
            st.rerun()
    else:
        st.info("Empty! Eat something yummy 😋")
