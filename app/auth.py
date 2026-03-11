import streamlit as st

from core.database import register_user, authenticate_user, get_hydration_today


def render_auth():
    st.markdown(
        "<h1 style='text-align:center; color:#00E676;'>🥗 NutriLens</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-size:1.1rem; color:#bbb;'>"
        "Your Smart & Healthy Food Companion 🚀</p>",
        unsafe_allow_html=True,
    )
    st.write("---")

    col_left, col_mid, col_right = st.columns([1, 1.6, 1])
    with col_mid:
        tab_login, tab_signup = st.tabs(["🔑 Login", "✨ Sign Up"])

        # ── LOGIN ──────────────────────────────────────────
        with tab_login:
            st.write("")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="your_username")
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                submitted = st.form_submit_button(
                    "Login", use_container_width=True
                )

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        _load_user_into_session(user)
                        st.rerun()
                    else:
                        st.error("Invalid username or password ❌")

        # ── SIGN UP ────────────────────────────────────────
        with tab_signup:
            st.write("")
            with st.form("signup_form"):
                new_username = st.text_input(
                    "Choose a Username", placeholder="cooluser123"
                )
                new_password = st.text_input(
                    "Choose a Password",
                    type="password",
                    placeholder="At least 6 characters",
                )
                confirm_password = st.text_input(
                    "Confirm Password", type="password", placeholder="••••••••"
                )
                submitted_signup = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

            if submitted_signup:
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                elif len(new_username.strip()) < 3:
                    st.error("Username must be at least 3 characters.")
                elif new_password != confirm_password:
                    st.error("Passwords don't match ❌")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user = register_user(new_username.strip(), new_password)
                    if user:
                        st.success(
                            "Account created! Switch to Login and sign in 🎉"
                        )
                    else:
                        st.error("Username already taken. Try another ❌")


def _load_user_into_session(user: dict):
    """Populate session state from a DB user dict after successful login."""
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["daily_goal"] = user["daily_goal"]
    st.session_state["bmi"] = user["bmi"]
    st.session_state["user_diet"] = user["diet"]
    st.session_state["water_ml"] = get_hydration_today(user["id"])
