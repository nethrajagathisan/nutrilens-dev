"""Profile section — groups Edit Profile, Achievements, Data Export, and Settings."""

import streamlit as st

from core.database import get_user_by_id, update_user
from app.achievements import render_achievements
from app.data_export import render_data_export


def render_profile_section():
    st.markdown(
        '<div class="section-header" style="font-size:1.4rem;">👤 Profile</div>',
        unsafe_allow_html=True,
    )

    tab_profile, tab_achievements, tab_export = st.tabs(
        ["👤 My Profile", "🏅 Achievements", "📤 Data Export"]
    )

    with tab_profile:
        _render_edit_profile()

    with tab_achievements:
        render_achievements()

    with tab_export:
        render_data_export()


def _render_edit_profile():
    uid = st.session_state.get("user_id")
    if not uid:
        st.warning("Please log in first.")
        return

    user = get_user_by_id(uid)
    if not user:
        st.error("User not found.")
        return

    current_goal = str(user.get("goal_type", "maintain") or "maintain").lower()
    current_pace = str(user.get("goal_pace", "medium") or "medium").lower()
    current_weight = float(user.get("weight_kg", 70) or 70)
    current_target_weight = float(user.get("target_weight", current_weight) or current_weight)
    if current_target_weight < 30:
        current_target_weight = current_weight

    st.markdown("### Edit Your Profile")

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 13, 100, user.get("age", 25), key="prof_age")
        gender = st.radio(
            "Gender", ["Male", "Female"],
            index=0 if user.get("gender", "Male") == "Male" else 1,
            horizontal=True, key="prof_gender",
        )
        weight = st.number_input(
            "Weight (kg)", 30.0, 250.0, float(user.get("weight_kg", 70)),
            step=0.5, key="prof_weight",
        )
        height = st.number_input(
            "Height (cm)", 100, 250, int(user.get("height_cm", 170)),
            key="prof_height",
        )

    with col2:
        activity_options = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Athlete"]
        current_act = user.get("activity", "Moderately Active")
        act_idx = activity_options.index(current_act) if current_act in activity_options else 2
        activity = st.selectbox("Activity Level", activity_options, index=act_idx, key="prof_act")

        diet_options = ["Balanced", "Keto", "Vegan", "Vegetarian", "Paleo", "Mediterranean", "Low-carb", "High-protein"]
        current_diet = user.get("diet", "Balanced")
        diet_idx = diet_options.index(current_diet) if current_diet in diet_options else 0
        diet = st.selectbox("Diet Preference", diet_options, index=diet_idx, key="prof_diet")

        goal_options = ["lose", "maintain", "gain"]
        goal_idx = goal_options.index(current_goal) if current_goal in goal_options else 1
        goal_type = st.selectbox("Goal Type", goal_options, index=goal_idx, format_func=str.title, key="prof_goal")

        target_weight = st.number_input(
            "Target Weight (kg)", 30.0, 250.0,
            current_target_weight,
            step=0.5, key="prof_target",
        )

        pace_options = ["slow", "medium", "fast"]
        pace_idx = pace_options.index(current_pace) if current_pace in pace_options else 1
        goal_pace = st.selectbox("Goal Pace", pace_options, index=pace_idx, format_func=str.title, key="prof_pace")

    st.write("")
    if st.button("💾 Save Profile", use_container_width=True, key="prof_save"):
        bmi = weight / ((height / 100) ** 2)

        # Calculate daily goal
        gender_offset = 5 if gender == "Male" else -161
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + gender_offset
        act_mult = {"Sedentary": 1.2, "Lightly Active": 1.375, "Moderately Active": 1.55, "Very Active": 1.725, "Athlete": 1.9}
        tdee = bmr * act_mult.get(activity, 1.55)
        pace_off = {"slow": 250, "medium": 500, "fast": 750}
        offset = pace_off.get(goal_pace, 500)
        if goal_type == "lose":
            daily_goal = int(tdee - offset)
        elif goal_type == "gain":
            daily_goal = int(tdee + offset)
        else:
            daily_goal = int(tdee)

        update_user(
            uid,
            age=age, gender=gender, weight_kg=weight, height_cm=height,
            activity=activity, diet=diet, bmi=round(bmi, 1),
            daily_goal=daily_goal, target_weight=target_weight,
            goal_type=goal_type, goal_pace=goal_pace,
        )

        st.session_state["bmi"] = round(bmi, 1)
        st.session_state["daily_goal"] = daily_goal
        st.session_state["user_diet"] = diet
        st.session_state["target_weight"] = target_weight
        st.session_state["goal_type"] = goal_type
        st.session_state["goal_pace"] = goal_pace

        st.success(f"Profile updated! Daily goal: {daily_goal} kcal")

    # Current stats display
    st.write("---")
    st.markdown("### Current Stats")
    sc = st.columns(4)
    bmi_val = st.session_state.get("bmi", 0)
    with sc[0]:
        st.metric("BMI", f"{bmi_val:.1f}")
    with sc[1]:
        st.metric("Daily Goal", f"{st.session_state.get('daily_goal', 2000)} kcal")
    with sc[2]:
        st.metric("Goal", st.session_state.get("goal_type", "maintain").title())
    with sc[3]:
        st.metric("Target", f"{st.session_state.get('target_weight', 0):.1f} kg")
