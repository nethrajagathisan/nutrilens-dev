import streamlit as st
import time

from core.ai_engine import connect_to_best_model, chat_ai, chat_ai_rag


def render_sidebar():
    """Render the full sidebar: nav, API key, profile, hydration, chatbot."""
    with st.sidebar:
        st.markdown("## 🥑 NutriLens")

        # --- NAVIGATION ---
        st.write("---")
        st.markdown("### 🧭 Menu")
        page = st.radio(
            "Go to:",
            ["🏠 Home & Health", "📸 Scan & Eat", "📝 Tracker", "🎙️ Voice Logger", "🍽️ Recipe Corner", "📊 My Diary", "📉 Analytics", "🔬 Micronutrients", "🏋️ Exercise Logger", "🧠 Fingerprint", "🔁 Adaptive Goal", "🗓️ Meal Planner", "💪 Fitness & Nutrition Coach", "🏅 Achievements", "📤 Data Export"],
            label_visibility="collapsed",
        )
        st.session_state["page"] = page
        st.write("---")

        # --- CONNECT AI ---
        if not st.session_state["active_model"]:
            with st.expander("🔑 Connect AI", expanded=True):
                key = st.text_input("API Key", type="password")
                if st.button("Link Key"):
                    model = connect_to_best_model(key)
                    if model:
                        st.session_state["api_key"] = key
                        st.session_state["active_model"] = model
                        st.success(f"Linked: {model} 🎉")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid Key ❌")
        else:
            st.success(f"🟢 {st.session_state['active_model']}")

        # --- PROFILE ---
        with st.expander("👤 Edit Profile", expanded=False):
            age = st.number_input("Age", 10, 100, 25)
            gender = st.radio("Gender", ["Male 👨", "Female 👩"], horizontal=True)
            w = st.number_input("Weight (kg)", 30, 150, 70)
            h = st.number_input("Height (cm)", 100, 250, 175)
            act = st.selectbox("Activity", ["Lazy 🛋️", "Active 🏃", "Athlete 🏋️"])
            st.session_state["user_diet"] = st.selectbox(
                "Diet", ["Balanced ⚖️", "Keto 🥩", "Vegan 🥗"]
            )

            if st.button("Save Stats"):
                bmi = w / ((h / 100) ** 2)
                st.session_state["bmi"] = bmi

                gender_offset = 5 if "Male" in gender else -161
                base_bmr = (10 * w) + (6.25 * h) - (5 * age) + gender_offset

                if "Lazy" in act:
                    mult = 1.2
                elif "Active" in act:
                    mult = 1.55
                else:
                    mult = 1.9

                st.session_state["daily_goal"] = int(base_bmr * mult)
                st.success(f"Updated! Goal: {st.session_state['daily_goal']} kcal 🚀")

        # --- HYDRATION ---
        st.write("### 💧 Hydration")
        w_col1, w_col2 = st.columns(2)
        if w_col1.button("🥤 Cup\n(250ml)"):
            st.session_state["water_ml"] += 250
        if w_col2.button("🍼 Bottle\n(500ml)"):
            st.session_state["water_ml"] += 500

        w_target = 3000
        w_curr = st.session_state["water_ml"]
        st.progress(min(w_curr / w_target, 1.0))
        st.caption(f"**{w_curr}ml** / {w_target}ml Goal")

        # --- CHATBOT ---
        st.write("---")
        st.markdown("### 💬 AI Coach")
        if uq := st.chat_input("Ask me..."):
            st.session_state["chat_history"].append({"role": "user", "text": uq})
            ctx = (
                st.session_state["scan_data"]["name"]
                if st.session_state["scan_data"]
                else "General"
            )
            reply = chat_ai_rag(uq, ctx, user_id=st.session_state.get("user_id"))
            st.session_state["chat_history"].append({"role": "assistant", "text": reply})
            st.rerun()

        for msg in st.session_state["chat_history"][-2:]:
            role = "assistant" if msg["role"] == "ai" else msg["role"]
            with st.chat_message(role):
                st.write(msg["text"])
