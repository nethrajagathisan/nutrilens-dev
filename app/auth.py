import streamlit as st

from core.database import authenticate_user, get_hydration_today, register_user


ACTIVITY_OPTIONS = [
    "Sedentary",
    "Lightly Active",
    "Moderately Active",
    "Very Active",
    "Athlete",
]

DIET_OPTIONS = [
    "Balanced",
    "Keto",
    "Vegan",
    "Vegetarian",
    "Paleo",
    "Mediterranean",
    "Low-carb",
    "High-protein",
]

GOAL_OPTIONS = {
    "Lose weight": "lose",
    "Maintain weight": "maintain",
    "Gain weight": "gain",
}


def _calc_daily_goal(weight_kg: float, height_cm: float, age: int, gender: str,
                     activity_level: str, goal_type: str) -> int:
    gender_offset = 5 if gender == "Male" else -161
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + gender_offset
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Athlete": 1.9,
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)
    if goal_type == "lose":
        return int(tdee - 500)
    if goal_type == "gain":
        return int(tdee + 500)
    return int(tdee)


def render_auth():
    """Render dedicated Login/Signup pages when user is not authenticated."""
    st.markdown(
        '<div class="onboarding-header">'
        '<h1>NutriLens</h1>'
        '<p>Sign in to continue to your dashboard</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        tab_login, tab_signup = st.tabs(["Login", "Signup"])

        with tab_login:
            _render_login_form()

        with tab_signup:
            _render_signup_form()


def _render_login_form():
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com").strip().lower()
        password = st.text_input("Password", type="password", placeholder="Your password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if not submitted:
        return

    if not email or not password:
        st.error("Please enter both email and password.")
        return

    user = authenticate_user(email, password)
    if not user:
        st.error("Invalid email or password.")
        return

    _load_user_into_session(user)
    st.rerun()


def _render_signup_form():
    with st.form("signup_form"):
        name = st.text_input("Name", placeholder="Your full name").strip()
        email = st.text_input("Email", placeholder="you@example.com").strip().lower()
        password = st.text_input("Password", type="password", placeholder="At least 8 characters")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

        age = st.number_input("Age", min_value=13, max_value=100, value=25)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=0)

        c1, c2 = st.columns(2)
        with c1:
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.5)
        with c2:
            activity_level = st.selectbox("Activity Level", ACTIVITY_OPTIONS, index=2)
            diet_type = st.selectbox("Diet Type", DIET_OPTIONS, index=0)

        goal_label = st.selectbox("Goal Type", list(GOAL_OPTIONS.keys()), index=1)
        goal_type = GOAL_OPTIONS[goal_label]
        target_weight_kg = st.number_input(
            "Target Weight (kg)",
            min_value=30.0,
            max_value=250.0,
            value=weight_kg,
            step=0.5,
        )

        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if not submitted:
        return

    if not name:
        st.error("Name is required.")
        return
    if not email or "@" not in email:
        st.error("Please enter a valid email address.")
        return
    if len(password) < 8:
        st.error("Password must be at least 8 characters.")
        return
    if password != confirm:
        st.error("Passwords do not match.")
        return

    bmi = float(weight_kg) / ((float(height_cm) / 100) ** 2)
    daily_goal = _calc_daily_goal(
        weight_kg=float(weight_kg),
        height_cm=float(height_cm),
        age=int(age),
        gender=gender,
        activity_level=activity_level,
        goal_type=goal_type,
    )

    user = register_user(
        email=email,
        password=password,
        name=name,
        age=int(age),
        gender=gender,
        height_cm=float(height_cm),
        weight_kg=float(weight_kg),
        activity_level=activity_level,
        diet_type=diet_type,
        goal_type=goal_type,
        target_weight_kg=float(target_weight_kg),
        bmi=round(bmi, 1),
        daily_goal=daily_goal,
    )
    if not user:
        st.error("An account with this email already exists.")
        return

    _load_user_into_session(user)
    st.rerun()


def _load_user_into_session(user: dict):
    """Populate session state from DB user dict after login/signup."""
    target_weight = float(user.get("target_weight_kg", 0) or 0)
    if target_weight < 30:
        target_weight = float(user.get("weight_kg", 70) or 70)

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user.get("name") or user.get("email") or "friend"
    st.session_state["daily_goal"] = int(user.get("daily_goal", 2000) or 2000)
    st.session_state["bmi"] = float(user.get("bmi", 0) or 0)
    st.session_state["user_diet"] = user.get("diet_type") or user.get("diet") or "Balanced"
    st.session_state["target_weight"] = target_weight
    st.session_state["goal_type"] = str(user.get("goal_type", "maintain") or "maintain").lower()
    st.session_state["goal_pace"] = "medium"
    st.session_state["water_ml"] = get_hydration_today(user["id"])
    st.session_state["page"] = "Home"


def logout_user():
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = ""
    st.session_state["water_ml"] = 0
    st.session_state["chat_history"] = []
    st.session_state["rag_chat_history"] = []
    st.session_state["page"] = "Home"
