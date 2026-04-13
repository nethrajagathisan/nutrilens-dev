import streamlit as st
import time

from core.ai_engine import connect_to_best_model, chat_ai_rag


# ─── PRIMARY NAV SECTIONS ──────────────────────────────
NAV_SECTIONS = {
    "Home":     "🏠",
    "Log":      "📝",
    "Insights": "📊",
    "Plans":    "📋",
    "Profile":  "👤",
}


def render_topnav():
    """Render a modern top navigation bar with 5 primary sections."""
    current = st.session_state.get("page", "Home")

    # Map old page names to sections for backwards compat
    section = _resolve_section(current)

    cols = st.columns(len(NAV_SECTIONS))
    for i, (name, icon) in enumerate(NAV_SECTIONS.items()):
        with cols[i]:
            is_active = (name == section)
            if st.button(
                f"{icon} {name}",
                key=f"nav_{name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["page"] = name
                st.rerun()

    st.write("")


def render_sidebar():
    """Minimal sidebar: AI key, hydration widget, and AI coach chat."""
    with st.sidebar:
        st.markdown("## 🥑 NutriLens")
        if st.session_state.get("logged_in"):
            if st.button("Logout", use_container_width=True):
                from app.auth import logout_user

                logout_user()
                st.rerun()
            st.write("---")

        # --- CONNECT AI ---
        if not st.session_state.get("active_model"):
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

        # --- HYDRATION ---
        st.write("---")
        st.markdown("### 💧 Hydration")
        w_col1, w_col2 = st.columns(2)
        if w_col1.button("🥤 Cup\n(250ml)"):
            from core.database import add_hydration, get_hydration_today
            uid = st.session_state.get("user_id")
            if uid:
                add_hydration(uid, 250)
                st.session_state["water_ml"] = get_hydration_today(uid)
                st.rerun()
            else:
                st.session_state["water_ml"] += 250
        if w_col2.button("🍼 Bottle\n(500ml)"):
            from core.database import add_hydration, get_hydration_today
            uid = st.session_state.get("user_id")
            if uid:
                add_hydration(uid, 500)
                st.session_state["water_ml"] = get_hydration_today(uid)
                st.rerun()
            else:
                st.session_state["water_ml"] += 500

        w_target = 3000
        w_curr = st.session_state.get("water_ml", 0)
        st.progress(min(w_curr / w_target, 1.0))
        st.caption(f"**{w_curr}ml** / {w_target}ml Goal")

        # --- AI COACH ---
        st.write("---")
        st.markdown("### 💬 AI Coach")
        if uq := st.chat_input("Ask me..."):
            st.session_state["chat_history"].append({"role": "user", "text": uq})
            ctx = (
                st.session_state["scan_data"]["name"]
                if st.session_state.get("scan_data")
                else "General"
            )
            reply = chat_ai_rag(uq, ctx, user_id=st.session_state.get("user_id"))
            st.session_state["chat_history"].append({"role": "assistant", "text": reply})
            st.rerun()

        for msg in st.session_state.get("chat_history", [])[-2:]:
            role = "assistant" if msg["role"] == "ai" else msg["role"]
            with st.chat_message(role):
                st.write(msg["text"])


def _resolve_section(page_name: str) -> str:
    """Map any page name (old or new) to one of the 5 primary sections."""
    if not page_name:
        return "Home"
    p = page_name.lower()
    if "home" in p:
        return "Home"
    if any(k in p for k in ["log", "scan", "track", "voice", "diary"]):
        return "Log"
    if any(k in p for k in ["analytics", "insight", "micro", "fingerprint"]):
        return "Insights"
    if any(k in p for k in ["plan", "recipe", "adaptive", "coach", "rl", "meal"]):
        return "Plans"
    if any(k in p for k in ["profile", "achieve", "export", "setting"]):
        return "Profile"
    return "Home"
