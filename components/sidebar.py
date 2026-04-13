import streamlit as st

from core.ai_engine import chat_ai_rag


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
    """Minimal sidebar: AI status, hydration widget, and AI coach chat."""
    with st.sidebar:
        # ── Brand header ──
        st.markdown(
            "<div style='text-align:center; padding: 0.5rem 0 0.2rem 0;'>"
            "<span style='font-size:2rem;'>🥑</span>"
            "<h2 style='margin:0; color:#00E676; font-weight:800;'>NutriLens</h2>"
            "</div>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("logged_in"):
            username = st.session_state.get("username", "User")
            st.markdown(
                f"<p style='text-align:center; color:#888; margin:0 0 0.5rem 0;'>"
                f"👋 {username}</p>",
                unsafe_allow_html=True,
            )
            if st.button("🚪 Logout", use_container_width=True):
                from app.auth import logout_user
                logout_user()
                st.rerun()

        st.markdown("---")

        # ── AI CONNECTION STATUS ──
        st.markdown(
            "<p style='color:#888; font-size:0.8rem; font-weight:600; "
            "text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;'>"
            "AI Engine</p>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("active_model"):
            model_name = st.session_state["active_model"]
            st.markdown(
                f"<div style='background:rgba(0,230,118,0.1); border:1px solid rgba(0,230,118,0.3); "
                f"border-radius:12px; padding:10px 14px; text-align:center;'>"
                f"<span style='color:#00E676; font-weight:700;'>🟢 Connected</span><br>"
                f"<span style='color:#aaa; font-size:0.8rem;'>{model_name}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:rgba(255,82,82,0.08); border:1px solid rgba(255,82,82,0.2); "
                "border-radius:12px; padding:10px 14px; text-align:center;'>"
                "<span style='color:#FF5252; font-weight:700;'>🔴 Not Connected</span><br>"
                "<span style='color:#888; font-size:0.78rem;'>"
                "Add GEMINI_API_KEY to .env</span>"
                "</div>",
                unsafe_allow_html=True,
            )

        # ── HYDRATION WIDGET ──
        st.markdown("---")
        hydration_target = st.session_state.get("hydration_target", 3000)
        st.markdown(
            "<p style='color:#888; font-size:0.8rem; font-weight:600; "
            "text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;'>"
            "💧 Hydration</p>",
            unsafe_allow_html=True,
        )
        w_col1, w_col2 = st.columns(2)
        if w_col1.button("🥤 250ml", key="sb_cup", use_container_width=True):
            from core.database import add_hydration, get_hydration_today
            uid = st.session_state.get("user_id")
            if uid:
                add_hydration(uid, 250)
                st.session_state["water_ml"] = get_hydration_today(uid)
                st.rerun()
            else:
                st.session_state["water_ml"] += 250
        if w_col2.button("🍼 500ml", key="sb_bottle", use_container_width=True):
            from core.database import add_hydration, get_hydration_today
            uid = st.session_state.get("user_id")
            if uid:
                add_hydration(uid, 500)
                st.session_state["water_ml"] = get_hydration_today(uid)
                st.rerun()
            else:
                st.session_state["water_ml"] += 500

        w_curr = st.session_state.get("water_ml", 0)
        w_pct = min(w_curr / hydration_target, 1.0)
        st.progress(w_pct)

        pct_label = int(w_pct * 100)
        color = "#00E676" if pct_label >= 100 else "#FFD700" if pct_label >= 60 else "#FF5252"
        st.markdown(
            f"<p style='text-align:center; margin:0;'>"
            f"<span style='color:{color}; font-weight:700;'>{w_curr}ml</span>"
            f" <span style='color:#666;'>/ {hydration_target}ml</span></p>",
            unsafe_allow_html=True,
        )

        # ── AI COACH ──
        st.markdown("---")
        st.markdown(
            "<p style='color:#888; font-size:0.8rem; font-weight:600; "
            "text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;'>"
            "💬 AI Coach</p>",
            unsafe_allow_html=True,
        )
        if uq := st.chat_input("Ask me anything…"):
            st.session_state["chat_history"].append({"role": "user", "text": uq})
            ctx = (
                st.session_state["scan_data"]["name"]
                if st.session_state.get("scan_data")
                else "General"
            )
            reply = chat_ai_rag(uq, ctx, user_id=st.session_state.get("user_id"))
            st.session_state["chat_history"].append({"role": "assistant", "text": reply})
            st.rerun()

        for msg in st.session_state.get("chat_history", [])[-3:]:
            role = msg["role"] if msg["role"] in ("user", "assistant") else "assistant"
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
