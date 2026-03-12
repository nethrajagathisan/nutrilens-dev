import streamlit as st

from core.database import register_user, authenticate_user, get_hydration_today

# ─── CONSTANTS ─────────────────────────────────────────
TOTAL_STEPS = 4
STEP_LABELS = {
    1: "About You",
    2: "Your Goals",
    3: "Your Lifestyle",
    4: "Create Account",
}
STEP_EMOJIS = {1: "👋", 2: "🎯", 3: "🏃", 4: "🔐"}
STEP_SUBTITLES = {
    1: "Let's get to know you a little — just the basics!",
    2: "What are you working toward? We'll set you up for success.",
    3: "Help us tailor your experience to your daily life.",
    4: "Almost there! Create your account and let's go.",
}


def _render_progress_dots(current: int):
    """Render step progress indicator dots."""
    dots = ""
    for i in range(1, TOTAL_STEPS + 1):
        if i < current:
            cls = "step-dot done"
        elif i == current:
            cls = "step-dot active"
        else:
            cls = "step-dot"
        dots += f'<div class="{cls}"></div>'
    st.markdown(
        f'<div class="step-progress">{dots}</div>',
        unsafe_allow_html=True,
    )


def _render_step_header(step: int):
    """Render the emoji, title, and subtitle for a step."""
    st.markdown(
        f'<div class="step-emoji">{STEP_EMOJIS[step]}</div>'
        f'<div class="step-title">{STEP_LABELS[step]}</div>'
        f'<div class="step-subtitle">{STEP_SUBTITLES[step]}</div>',
        unsafe_allow_html=True,
    )


def _calc_daily_goal(weight, height, age, gender, activity, goal_type, goal_pace):
    """Calculate TDEE-based daily calorie goal adjusted for goal & pace."""
    gender_offset = 5 if gender == "Male" else -161
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + gender_offset
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Athlete": 1.9,
    }
    tdee = bmr * activity_multipliers.get(activity, 1.55)

    pace_offsets = {"slow": 250, "medium": 500, "fast": 750}
    offset = pace_offsets.get(goal_pace, 500)

    if goal_type == "lose":
        return int(tdee - offset)
    elif goal_type == "gain":
        return int(tdee + offset)
    return int(tdee)


def render_auth():
    """Render the full onboarding + auth flow."""
    # Initialize onboarding state if needed
    if "onboarding_step" not in st.session_state:
        st.session_state["onboarding_step"] = 1
    if "onboarding_data" not in st.session_state:
        st.session_state["onboarding_data"] = {}
    if "onboarding_done" not in st.session_state:
        st.session_state["onboarding_done"] = False

    # If onboarding is complete, show login/signup
    if st.session_state["onboarding_done"]:
        _render_login_screen()
        return

    step = st.session_state["onboarding_step"]

    # Header
    st.markdown(
        '<div class="onboarding-header">'
        '<h1>🥗 NutriLens</h1>'
        '<p>Your Smart & Healthy Food Companion</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Progress
    _render_progress_dots(step)
    st.markdown(
        f'<div class="step-label">Step {step} of {TOTAL_STEPS}: {STEP_LABELS[step]}</div>',
        unsafe_allow_html=True,
    )

    # Center content
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if step == 1:
            _render_step_about()
        elif step == 2:
            _render_step_goals()
        elif step == 3:
            _render_step_lifestyle()
        elif step == 4:
            _render_step_create_account()


# ─── STEP 1: ABOUT YOU ────────────────────────────────

def _render_step_about():
    data = st.session_state["onboarding_data"]
    _render_step_header(1)

    age = st.number_input(
        "How old are you?",
        min_value=13, max_value=100,
        value=data.get("age", 25),
        key="ob_age",
    )
    gender = st.radio(
        "What's your gender?",
        ["Male", "Female"],
        index=0 if data.get("gender", "Male") == "Male" else 1,
        horizontal=True,
        key="ob_gender",
    )
    height = st.number_input(
        "Height (cm)",
        min_value=100, max_value=250,
        value=data.get("height_cm", 170),
        key="ob_height",
    )
    weight = st.number_input(
        "Current weight (kg)",
        min_value=30.0, max_value=250.0,
        value=float(data.get("weight_kg", 70.0)),
        step=0.5,
        key="ob_weight",
    )

    st.write("")
    if st.button("Next →", key="step1_next", use_container_width=True):
        st.session_state["onboarding_data"].update({
            "age": age,
            "gender": gender,
            "height_cm": height,
            "weight_kg": weight,
        })
        st.session_state["onboarding_step"] = 2
        st.rerun()


# ─── STEP 2: YOUR GOALS ───────────────────────────────

def _render_step_goals():
    data = st.session_state["onboarding_data"]
    _render_step_header(2)

    goal_options = {"Lose weight 🔥": "lose", "Maintain weight ⚖️": "maintain", "Gain weight 💪": "gain"}
    goal_labels = list(goal_options.keys())
    current_goal = data.get("goal_type", "maintain")
    default_idx = list(goal_options.values()).index(current_goal) if current_goal in goal_options.values() else 1

    goal_choice = st.radio(
        "What's your goal?",
        goal_labels,
        index=default_idx,
        key="ob_goal_type",
    )
    goal_type = goal_options[goal_choice]

    target_weight = st.number_input(
        "Target weight (kg)",
        min_value=30.0, max_value=250.0,
        value=float(data.get("target_weight", data.get("weight_kg", 70.0))),
        step=0.5,
        key="ob_target_weight",
    )

    pace_options = {"Slow & steady 🐢": "slow", "Moderate pace 🚶": "medium", "Aggressive 🏃": "fast"}
    pace_labels = list(pace_options.keys())
    current_pace = data.get("goal_pace", "medium")
    pace_idx = list(pace_options.values()).index(current_pace) if current_pace in pace_options.values() else 1

    pace_choice = st.radio(
        "How fast do you want to progress?",
        pace_labels,
        index=pace_idx,
        key="ob_pace",
    )
    goal_pace = pace_options[pace_choice]

    # Show calorie preview
    w = data.get("weight_kg", 70)
    h = data.get("height_cm", 170)
    a = data.get("age", 25)
    g = data.get("gender", "Male")
    estimated_cal = _calc_daily_goal(w, h, a, g, "Moderately Active", goal_type, goal_pace)
    st.info(f"🔥 Estimated daily goal: **~{estimated_cal} kcal** (we'll fine-tune this next)")

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", key="step2_back", use_container_width=True):
            st.session_state["onboarding_step"] = 1
            st.rerun()
    with c2:
        if st.button("Next →", key="step2_next", use_container_width=True):
            st.session_state["onboarding_data"].update({
                "goal_type": goal_type,
                "target_weight": target_weight,
                "goal_pace": goal_pace,
            })
            st.session_state["onboarding_step"] = 3
            st.rerun()


# ─── STEP 3: LIFESTYLE ────────────────────────────────

def _render_step_lifestyle():
    data = st.session_state["onboarding_data"]
    _render_step_header(3)

    activity_options = [
        "Sedentary",
        "Lightly Active",
        "Moderately Active",
        "Very Active",
        "Athlete",
    ]
    activity_descriptions = {
        "Sedentary": "Little or no exercise, desk job",
        "Lightly Active": "Light exercise 1-3 days/week",
        "Moderately Active": "Moderate exercise 3-5 days/week",
        "Very Active": "Hard exercise 6-7 days/week",
        "Athlete": "Very hard exercise, physical job",
    }
    current_act = data.get("activity", "Moderately Active")
    act_idx = activity_options.index(current_act) if current_act in activity_options else 2

    activity = st.selectbox(
        "How active are you?",
        activity_options,
        index=act_idx,
        key="ob_activity",
    )
    st.caption(f"ℹ️ {activity_descriptions[activity]}")

    diet_options = [
        "Balanced",
        "Keto",
        "Vegan",
        "Vegetarian",
        "Paleo",
        "Mediterranean",
        "Low-carb",
        "High-protein",
    ]
    current_diet = data.get("diet", "Balanced")
    diet_idx = diet_options.index(current_diet) if current_diet in diet_options else 0

    diet = st.selectbox(
        "Any dietary preference?",
        diet_options,
        index=diet_idx,
        key="ob_diet",
    )

    restrictions = st.text_input(
        "Food allergies or restrictions? (optional)",
        value=data.get("restrictions", ""),
        placeholder="e.g., gluten-free, nut allergy, lactose intolerant",
        key="ob_restrictions",
    )

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", key="step3_back", use_container_width=True):
            st.session_state["onboarding_step"] = 2
            st.rerun()
    with c2:
        if st.button("Next →", key="step3_next", use_container_width=True):
            st.session_state["onboarding_data"].update({
                "activity": activity,
                "diet": diet,
                "restrictions": restrictions,
            })
            st.session_state["onboarding_step"] = 4
            st.rerun()


# ─── STEP 4: CREATE ACCOUNT ───────────────────────────

def _render_step_create_account():
    data = st.session_state["onboarding_data"]
    _render_step_header(4)

    # Summary of what they entered
    st.markdown("**Here's your profile summary:**")
    summary_items = [
        f"**Age:** {data.get('age', 25)} · **Gender:** {data.get('gender', '–')}",
        f"**Height:** {data.get('height_cm', 170)} cm · **Weight:** {data.get('weight_kg', 70)} kg",
        f"**Goal:** {data.get('goal_type', 'maintain').title()} → {data.get('target_weight', '–')} kg ({data.get('goal_pace', 'medium')} pace)",
        f"**Activity:** {data.get('activity', '–')} · **Diet:** {data.get('diet', '–')}",
    ]
    for item in summary_items:
        st.markdown(f"  {item}")
    st.write("")

    # Account creation form
    tab_signup, tab_login = st.tabs(["✨ Create Account", "🔑 I have an account"])

    with tab_signup:
        with st.form("onboarding_signup"):
            username = st.text_input("Choose a username", placeholder="cooluser123")
            password = st.text_input("Password", type="password", placeholder="At least 6 characters")
            confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Create Account & Start 🚀", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Username and password are required.")
            elif len(username.strip()) < 3:
                st.error("Username must be at least 3 characters.")
            elif password != confirm:
                st.error("Passwords don't match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                # Calculate BMI and daily goal from onboarding data
                w = data.get("weight_kg", 70)
                h = data.get("height_cm", 170)
                bmi = w / ((h / 100) ** 2)
                daily_goal = _calc_daily_goal(
                    w, h, data.get("age", 25), data.get("gender", "Male"),
                    data.get("activity", "Moderately Active"),
                    data.get("goal_type", "maintain"),
                    data.get("goal_pace", "medium"),
                )
                profile = {
                    "age": data.get("age", 25),
                    "gender": data.get("gender", "Male"),
                    "weight_kg": w,
                    "height_cm": h,
                    "activity": data.get("activity", "Moderately Active"),
                    "diet": data.get("diet", "Balanced"),
                    "bmi": round(bmi, 1),
                    "daily_goal": daily_goal,
                    "target_weight": data.get("target_weight", w),
                    "goal_type": data.get("goal_type", "maintain"),
                    "goal_pace": data.get("goal_pace", "medium"),
                }
                user = register_user(username.strip(), password, **profile)
                if user:
                    _load_user_into_session(user)
                    st.rerun()
                else:
                    st.error("Username already taken. Try another.")

    with tab_login:
        with st.form("onboarding_login"):
            login_user = st.text_input("Username", placeholder="your_username", key="ol_user")
            login_pass = st.text_input("Password", type="password", placeholder="••••••••", key="ol_pass")
            login_sub = st.form_submit_button("Log In", use_container_width=True)

        if login_sub:
            if not login_user or not login_pass:
                st.error("Please enter both username and password.")
            else:
                user = authenticate_user(login_user, login_pass)
                if user:
                    _load_user_into_session(user)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    st.write("")
    if st.button("← Back", key="step4_back", use_container_width=True):
        st.session_state["onboarding_step"] = 3
        st.rerun()


# ─── LOGIN SCREEN (for returning users) ───────────────

def _render_login_screen():
    """Fallback login screen for returning users who skip onboarding."""
    st.markdown(
        '<div class="onboarding-header">'
        '<h1>🥗 NutriLens</h1>'
        '<p>Welcome back!</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        tab_login, tab_signup = st.tabs(["🔑 Login", "✨ New here?"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="your_username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        _load_user_into_session(user)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with tab_signup:
            st.info("Starting the onboarding wizard...")
            if st.button("Start Setup →", use_container_width=True):
                st.session_state["onboarding_done"] = False
                st.session_state["onboarding_step"] = 1
                st.session_state["onboarding_data"] = {}
                st.rerun()


def _load_user_into_session(user: dict):
    """Populate session state from a DB user dict after successful login."""
    goal_type = str(user.get("goal_type", "maintain") or "maintain").lower()
    goal_pace = str(user.get("goal_pace", "medium") or "medium").lower()
    target_weight = float(user.get("target_weight", 0) or 0)
    if target_weight < 30:
        target_weight = float(user.get("weight_kg", 70) or 70)

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["daily_goal"] = user["daily_goal"]
    st.session_state["bmi"] = user["bmi"]
    st.session_state["user_diet"] = user.get("diet", "Balanced")
    st.session_state["target_weight"] = target_weight
    st.session_state["goal_type"] = goal_type
    st.session_state["goal_pace"] = goal_pace
    st.session_state["water_ml"] = get_hydration_today(user["id"])
    st.session_state["page"] = "Home"
