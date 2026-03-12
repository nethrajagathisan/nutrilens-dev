import streamlit as st
import datetime

from core.database import (
    add_food_log,
    add_hydration,
    get_hydration_today,
    add_weight_log,
    add_exercise_log,
    get_user_by_id,
    update_user,
    get_last_food_log_id,
    add_micronutrient_log,
)
from core.fingerprint_engine import update_fingerprint
from core.ai_engine import estimate_micronutrients

MEAL_OPTIONS = ["Breakfast 🍳", "Lunch 🥗", "Dinner 🍗", "Snack 🍎"]


def render_tracker():
    uid = st.session_state["user_id"]

    st.markdown(
        "<h2 style='color:#00E676;'>📝 Manual Nutrition Tracker</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Log food, water, weight, and exercise without needing AI — works fully offline.")
    st.write("---")

    tab_food, tab_hydration, tab_weight, tab_exercise = st.tabs(
        ["🍽️ Log Food", "💧 Log Water", "⚖️ Log Weight", "🏃 Log Exercise"]
    )

    # ── TAB 1: FOOD ──────────────────────────────────────────────────────────
    with tab_food:
        st.markdown("### Add a Food Entry")
        with st.form("manual_food_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns([2, 1])
            food_name = f_col1.text_input(
                "Food Name *", placeholder="e.g. Chicken Biryani"
            )
            meal = f_col2.selectbox("Meal", MEAL_OPTIONS)

            n1, n2, n3, n4 = st.columns(4)
            calories = n1.number_input("Calories (kcal) *", min_value=0, max_value=5000, value=0)
            carbs    = n2.number_input("Carbs (g)",         min_value=0, max_value=500,  value=0)
            protein  = n3.number_input("Protein (g)",       min_value=0, max_value=300,  value=0)
            fat      = n4.number_input("Fat (g)",           min_value=0, max_value=300,  value=0)

            submitted = st.form_submit_button("➕ Add to Diary", use_container_width=True)

        if submitted:
            if not food_name.strip():
                st.error("Food name is required.")
            elif calories == 0:
                st.warning("⚠️ Calories are 0 — are you sure?")
                add_food_log(uid, food_name.strip(), calories, carbs, protein, fat, meal)
                fid = get_last_food_log_id(uid)
                if fid:
                    micros = estimate_micronutrients(food_name, calories)
                    add_micronutrient_log(uid, fid, **micros)
                update_fingerprint(uid)
                st.success(f"**{food_name}** logged to {meal}! 📝")
            else:
                add_food_log(uid, food_name.strip(), calories, carbs, protein, fat, meal)
                fid = get_last_food_log_id(uid)
                if fid:
                    micros = estimate_micronutrients(food_name, calories)
                    add_micronutrient_log(uid, fid, **micros)
                update_fingerprint(uid)
                st.success(f"**{food_name}** ({calories} kcal) logged to {meal}! 📝")

        # Quick-add common foods
        st.write("---")
        st.markdown("#### ⚡ Quick-Add Common Foods")
        quick_foods = [
            ("🍌 Banana",        89,  23, 1, 0),
            ("🥚 Boiled Egg",    78,   1, 6, 5),
            ("🍚 Rice (100g)",  130,  28, 3, 0),
            ("🥛 Milk (200ml)", 122,  10, 6, 7),
            ("🍞 Bread slice",   79,  15, 3, 1),
            ("🍗 Chicken(100g)",165,   0,31, 4),
            ("🥑 Avocado (½)",  120,   6, 1,11),
            ("🥜 Peanuts (30g)",170,   5, 8,15),
        ]
        q_meal = st.selectbox("Add to meal:", MEAL_OPTIONS, key="quick_meal")
        cols = st.columns(4)
        for i, (label, cals, c, p, f_) in enumerate(quick_foods):
            if cols[i % 4].button(label, use_container_width=True):
                name_clean = label.split(" ", 1)[1].split("(")[0].strip()
                add_food_log(uid, name_clean, cals, c, p, f_, q_meal)
                fid = get_last_food_log_id(uid)
                if fid:
                    micros = estimate_micronutrients(name_clean, cals)
                    add_micronutrient_log(uid, fid, **micros)
                update_fingerprint(uid)
                st.success(f"**{name_clean}** added!")
                st.rerun()

    # ── TAB 2: HYDRATION ─────────────────────────────────────────────────────
    with tab_hydration:
        st.markdown("### Log Water Intake")

        today_ml = get_hydration_today(uid)
        st.session_state["water_ml"] = today_ml

        daily_target = 3000
        pct = min(today_ml / daily_target, 1.0)

        h1, h2, h3 = st.columns(3)
        h1.metric("Today's Intake", f"{today_ml} ml")
        h2.metric("Daily Target",   f"{daily_target} ml")
        h3.metric("Remaining",      f"{max(daily_target - today_ml, 0)} ml")

        st.progress(pct)
        st.caption(f"{pct*100:.0f}% of daily goal reached")

        st.write("---")
        st.markdown("#### Quick Add")
        qa1, qa2, qa3, qa4 = st.columns(4)
        if qa1.button("🥤 Glass\n150 ml",  use_container_width=True):
            add_hydration(uid, 150)
            st.rerun()
        if qa2.button("☕ Cup\n250 ml",    use_container_width=True):
            add_hydration(uid, 250)
            st.rerun()
        if qa3.button("🍼 Bottle\n500 ml", use_container_width=True):
            add_hydration(uid, 500)
            st.rerun()
        if qa4.button("🫙 Large\n1000 ml", use_container_width=True):
            add_hydration(uid, 1000)
            st.rerun()

        st.write("")
        st.markdown("#### Custom Amount")
        with st.form("hydration_form", clear_on_submit=True):
            custom_ml = st.number_input(
                "Amount (ml)", min_value=50, max_value=2000, value=250, step=50
            )
            if st.form_submit_button("Log Water 💧", use_container_width=True):
                add_hydration(uid, custom_ml)
                st.success(f"Logged {custom_ml} ml 💧")
                st.rerun()

    # ── TAB 3: WEIGHT ────────────────────────────────────────────────────────
    with tab_weight:
        st.markdown("### Log Your Weight")

        db_user = get_user_by_id(uid) or {}
        current_weight = db_user.get("weight_kg", 70.0)
        height_cm      = db_user.get("height_cm", 175.0)
        current_bmi    = db_user.get("bmi", 0.0)

        wc1, wc2 = st.columns(2)
        wc1.metric("Current Weight", f"{current_weight} kg")
        if current_bmi > 0:
            bmi_label = (
                "Underweight" if current_bmi < 18.5
                else "Healthy" if current_bmi < 25
                else "Overweight" if current_bmi < 30
                else "Obese"
            )
            bmi_color = (
                "#85E3FF" if current_bmi < 18.5
                else "#00E676" if current_bmi < 25
                else "#FFD700" if current_bmi < 30
                else "#FF5252"
            )
            wc2.markdown(
                f"<div style='text-align:center;'>"
                f"<p style='color:#bbb; margin:0; font-size:0.85rem;'>BMI</p>"
                f"<h2 style='color:{bmi_color}; margin:0;'>{current_bmi:.1f}</h2>"
                f"<p style='color:{bmi_color}; margin:0; font-size:0.9rem;'>{bmi_label}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.write("---")
        with st.form("weight_form", clear_on_submit=True):
            new_weight = st.number_input(
                "New Weight (kg)",
                min_value=20.0,
                max_value=300.0,
                value=float(current_weight),
                step=0.1,
            )
            if st.form_submit_button("Save Weight ⚖️", use_container_width=True):
                new_bmi = new_weight / ((height_cm / 100) ** 2)
                add_weight_log(uid, new_weight)
                update_user(uid, weight_kg=new_weight, bmi=new_bmi)
                st.session_state["bmi"] = new_bmi
                st.success(
                    f"Weight updated: **{new_weight} kg** | BMI: **{new_bmi:.1f}**"
                )
                st.rerun()

    # ── TAB 4: EXERCISE ─────────────────────────────────────────────────────
    with tab_exercise:
        st.markdown("### Log Exercise")
        st.caption("Track workouts so the AI coach can combine fitness and nutrition advice.")

        with st.form("exercise_form", clear_on_submit=True):
            ex_col1, ex_col2 = st.columns([2, 1])
            activity_name = ex_col1.text_input(
                "Activity *", placeholder="e.g. Brisk Walk, Strength Training"
            )
            intensity = ex_col2.selectbox("Intensity", ["Light", "Moderate", "High"])

            ex_col3, ex_col4 = st.columns(2)
            duration_min = ex_col3.number_input(
                "Duration (min)", min_value=5, max_value=300, value=30, step=5
            )
            calories_burned = ex_col4.number_input(
                "Calories Burned", min_value=0, max_value=3000, value=0, step=10
            )

            if st.form_submit_button("➕ Save Exercise", use_container_width=True):
                if not activity_name.strip():
                    st.error("Activity name is required.")
                else:
                    add_exercise_log(
                        uid,
                        activity_name.strip(),
                        duration_min,
                        calories_burned,
                        intensity,
                    )
                    st.success(f"Logged **{activity_name}** for **{duration_min} min**.")
                    st.rerun()

        st.write("---")
        st.markdown("#### ⚡ Quick-Add Workouts")
        quick_workouts = [
            ("🚶 Brisk Walk", 30, 140, "Light"),
            ("🏃 Run", 30, 300, "High"),
            ("🚴 Cycling", 45, 360, "Moderate"),
            ("🏋️ Strength", 45, 250, "Moderate"),
        ]
        ex_cols = st.columns(4)
        for i, (label, mins, cals, intensity_label) in enumerate(quick_workouts):
            if ex_cols[i].button(label, use_container_width=True):
                add_exercise_log(uid, label.split(" ", 1)[1], mins, cals, intensity_label)
                st.success(f"Added **{label.split(' ', 1)[1]}**.")
                st.rerun()
