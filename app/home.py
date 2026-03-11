import streamlit as st


def render_home():
    st.markdown(
        "<h1 style='text-align: center; color: #00E676;'>🥗 NutriLens</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-size: 1.2rem; color: #bbb;'>"
        "Your Fun, Smart & Healthy Food Companion! 🚀</p>",
        unsafe_allow_html=True,
    )

    st.write("---")

    # --- HEALTH STATS ---
    st.subheader("🏥 My Health Stats")

    if st.session_state["bmi"] > 0:
        hc1, hc2 = st.columns(2)

        with hc1:
            bmi_val = st.session_state["bmi"]
            bmi_status = "💚 Healthy" if 18.5 <= bmi_val < 25 else "⚠️ Checkup"
            st.markdown(
                f"""
                <div class="glass-card" style="text-align:center;">
                    <h2>⚖️ BMI Score</h2>
                    <h1 style="color:#FFD700; font-size: 3rem;">{bmi_val:.1f}</h1>
                    <p style="font-size: 1.2rem;">Status: <b>{bmi_status}</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with hc2:
            st.markdown(
                f"""
                <div class="glass-card" style="text-align:center;">
                    <h2>🔥 Daily Goal</h2>
                    <h1 style="color:#FF5722; font-size: 3rem;">{st.session_state['daily_goal']}</h1>
                    <p style="font-size: 1.2rem;">Calories to maintain weight</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info(
            "👈 **Tip:** Go to the Sidebar, enter your Age/Weight/Height, "
            "and click 'Save Stats' to see your Health Cards here!"
        )

    st.write("---")

    # --- FEATURES ---
    st.markdown("### ✨ App Features")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="feature-box"><h1>📸</h1><h3>AI Vision</h3>'
            "<p>I can see your food! Just snap a pic and I'll tell you "
            "calories, macros, and nutrients.</p></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="feature-box"><h1>👨\u200d🍳</h1><h3>Smart Chef</h3>'
            "<p>Got ingredients? I'll cook up yummy recipes based on your "
            "diet (Keto, Vegan, etc.).</p></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="feature-box"><h1>⚖️</h1><h3>Health & Burn</h3>'
            "<p>I analyze good vs bad ingredients and tell you how much to "
            "run/walk to burn it off!</p></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(
            '<div class="feature-box"><h1>📊</h1><h3>Daily Diary</h3>'
            "<p>Track your meals and see your progress bars fill up!</p></div>",
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            '<div class="feature-box"><h1>💬</h1><h3>AI Chatbot</h3>'
            "<p>Ask me anything about nutrition, digestion, or diet tips.</p></div>",
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            '<div class="feature-box"><h1>💧</h1><h3>Hydration</h3>'
            "<p>Don't forget to drink water! Track your glasses in the sidebar.</p></div>",
            unsafe_allow_html=True,
        )

    st.write("---")
    st.info(
        "💡 **Tip of the Day:** Drinking water before meals can help you "
        "feel fuller and aid weight loss!"
    )
