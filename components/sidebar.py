import streamlit as st
import time

from core.ai_engine import connect_to_best_model, chat_ai
from core.database import (
    update_user,
    add_hydration,
    get_hydration_today,
    add_weight_log,
    get_user_by_id,
)


def render_sidebar():
    """Render the full sidebar: nav, API key, profile, hydration, chatbot."""
    with st.sidebar:
        st.markdown("## 🥑 NutriLens")

        # --- USER INFO + LOGOUT ---
        st.markdown(
            f"<p style='color:#bbb; margin:0;'>👤 Logged in as "
            f"<b style='color:#00E676;'>{st.session_state.get('username', '')}</b></p>",
            unsafe_allow_html=True,
        )
        if st.button("🚨 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # --- NAVIGATION ---
        st.write("---")
        st.markdown("### 🧭 Menu")
        page = st.radio(
            "Go to:",
            ["🏠 Home & Health", "📸 Scan & Eat", "📝 Tracker", "📊 My Diary", "📉 Analytics"],
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
        uid = st.session_state["user_id"]
        db_user = get_user_by_id(uid) or {}

        with st.expander("👤 Edit Profile", expanded=False):
            age = st.number_input("Age", 10, 100, db_user["age"])
            gender_opts = ["Male 👨", "Female 👩"]
            gender_idx = 0 if "Male" in db_user["gender"] else 1
            gender = st.radio("Gender", gender_opts, index=gender_idx, horizontal=True)
            w = st.number_input("Weight (kg)", 30, 150, int(db_user["weight_kg"]))
            h = st.number_input("Height (cm)", 100, 250, int(db_user["height_cm"]))
            act_opts = ["Lazy 🛋️", "Active 🏃", "Athlete 🏋️"]
            act_idx = next(
                (i for i, a in enumerate(act_opts) if db_user["activity"] in a), 1
            )
            act = st.selectbox("Activity", act_opts, index=act_idx)
            diet_opts = ["Balanced ⚖️", "Keto 🥩", "Vegan 🥗"]
            diet_idx = next(
                (i for i, d in enumerate(diet_opts) if db_user["diet"] in d), 0
            )
            st.session_state["user_diet"] = st.selectbox(
                "Diet", diet_opts, index=diet_idx
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

                daily_goal = int(base_bmr * mult)
                st.session_state["daily_goal"] = daily_goal

                # Persist to DB
                diet_clean = st.session_state["user_diet"].split(" ")[0]
                gender_clean = "Male" if "Male" in gender else "Female"
                act_clean = act.split(" ")[0]
                update_user(
                    uid,
                    age=age,
                    gender=gender_clean,
                    weight_kg=w,
                    height_cm=h,
                    activity=act_clean,
                    diet=diet_clean,
                    bmi=bmi,
                    daily_goal=daily_goal,
                )
                # Log weight change
                add_weight_log(uid, w)
                st.success(f"Updated! Goal: {daily_goal} kcal 🚀")

        # --- HYDRATION ---
        st.write("### 💧 Hydration")
        w_col1, w_col2 = st.columns(2)
        if w_col1.button("🥤 Cup\n(250ml)"):
            add_hydration(uid, 250)
            st.session_state["water_ml"] = get_hydration_today(uid)
        if w_col2.button("🍼 Bottle\n(500ml)"):
            add_hydration(uid, 500)
            st.session_state["water_ml"] = get_hydration_today(uid)

        w_target = 3000
        w_curr = st.session_state["water_ml"]
        st.progress(min(w_curr / w_target, 1.0))
        st.caption(f"**{w_curr}ml** / {w_target}ml Goal")

        # --- CHATBOT ---
        st.write("---")
        st.markdown("### 💬 AI Buddy")
        if uq := st.chat_input("Ask me..."):
            if st.session_state["active_model"]:
                st.session_state["chat_history"].append({"role": "user", "text": uq})
                ctx = (
                    st.session_state["scan_data"]["name"]
                    if st.session_state["scan_data"]
                    else "General"
                )
                reply = chat_ai(uq, ctx)
                st.session_state["chat_history"].append({"role": "ai", "text": reply})
                st.rerun()

        for msg in st.session_state["chat_history"][-2:]:
            with st.chat_message(msg["role"]):
                st.write(msg["text"])
