import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.rl_agent import run_rl_cycle, observe_state, compute_reward
from core.database import get_rl_history, update_user

# ── Chart theme ────────────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(20,20,30,0.6)",
    font=dict(color="white", family="Poppins, sans-serif"),
    margin=dict(t=40, b=30, l=10, r=10),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
)


def render_rl_dashboard():
    uid = st.session_state.get("user_id")
    if not uid:
        st.warning("Please log in first.")
        return

    st.markdown("## 🔁 Adaptive Goal Engine")
    st.caption("Your calorie goal is automatically recalibrated every week based on your behaviour, weight trend, hydration, and logging consistency.")

    # ── Run RL cycle ──────────────────────────────────────────────────────────
    result = run_rl_cycle(uid)
    state = observe_state(uid)
    reward, reason_str = compute_reward(state)

    if result["changed"]:
        st.session_state["daily_goal"] = result["new_goal"]

    # ── Section 1: Goal Change Banner ─────────────────────────────────────────
    st.markdown("### 🎯 Goal Update")
    if result["changed"]:
        border_color = "#00E676" if result["action"] > 0 else "#FFD740"
        st.markdown(
            f"""
            <div style="background:rgba(30,30,45,0.85); border-left:5px solid {border_color};
                        border-radius:14px; padding:1.2rem 1.6rem; margin-bottom:1rem;">
                <span style="font-size:2rem; font-weight:700; color:white;">
                    {result['old_goal']} kcal &nbsp;→&nbsp; {result['new_goal']} kcal
                </span><br>
                <span style="color:#ccc; font-size:0.95rem;">{result['reason']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.success("✅ Your goal is well-calibrated — no adjustment needed right now.")

    # ── Section 2: State Panel ────────────────────────────────────────────────
    st.markdown("### 📊 What the Agent Sees (Last 7 Days)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Calorie Adherence", f"{state['adherence_ratio'] * 100:.0f} %")
    c2.metric("Hydration Score", f"{state['hydration_ratio'] * 100:.0f} %")
    c3.metric("Logging Rate", f"{state['log_consistency'] * 100:.0f} %")
    c4.metric("Weight Δ", f"{state['weight_delta']:+.1f} kg")

    # ── Section 3: Reward Gauge ───────────────────────────────────────────────
    st.markdown("### 🏆 Current Reward Signal")
    g_col, r_col = st.columns([2, 1])
    with g_col:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=reward,
            number=dict(font=dict(size=38)),
            gauge=dict(
                axis=dict(range=[-1, 1], tickcolor="white"),
                bar=dict(color="#7C4DFF"),
                bgcolor="rgba(20,20,30,0.6)",
                steps=[
                    dict(range=[-1.0, -0.3], color="#FF5252"),
                    dict(range=[-0.3,  0.3], color="#FFD740"),
                    dict(range=[ 0.3,  1.0], color="#00E676"),
                ],
            ),
        ))
        fig.update_layout(**_LAYOUT, height=260)
        st.plotly_chart(fig, use_container_width=True)
    with r_col:
        st.markdown("**Reward components:**")
        for part in reason_str.split("; "):
            st.markdown(f"- {part}")

    # ── Section 4: Goal Adaptation History ────────────────────────────────────
    st.markdown("### 📈 Goal Adaptation History")
    history = get_rl_history(uid, days=60)
    if history:
        df = pd.DataFrame(history)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df["date"], y=df["new_goal"],
            mode="lines+markers", name="Goal",
            line=dict(color="#7C4DFF", width=2),
            marker=dict(size=6),
        ))
        raised = df[df["action_kcal"] > 0]
        lowered = df[df["action_kcal"] < 0]
        if not raised.empty:
            fig2.add_trace(go.Scatter(
                x=raised["date"], y=raised["new_goal"],
                mode="markers", name="Raised",
                marker=dict(color="#00E676", size=12, symbol="triangle-up"),
            ))
        if not lowered.empty:
            fig2.add_trace(go.Scatter(
                x=lowered["date"], y=lowered["new_goal"],
                mode="markers", name="Lowered",
                marker=dict(color="#FF5252", size=12, symbol="triangle-down"),
            ))
        fig2.update_layout(**_LAYOUT, height=340, yaxis_title="kcal")
        st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📄 Raw adjustment history"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No adaptation history yet — check back after a week of logging.")

    # ── Section 5: Manual Override ────────────────────────────────────────────
    st.markdown("### 🛠️ Manual Override")
    override_val = st.number_input(
        "Set goal manually (kcal)",
        min_value=1200, max_value=5000, step=50,
        value=st.session_state.get("daily_goal", 2000),
    )
    if st.button("💾 Save Manual Goal"):
        update_user(uid, daily_goal=override_val)
        st.session_state["daily_goal"] = override_val
        st.rerun()
