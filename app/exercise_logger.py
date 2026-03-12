import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime

from core.database import (
    add_exercise_log,
    get_exercise_logs_today,
    get_net_calories_today,
    get_daily_net_calories,
    get_daily_exercise_summary,
    get_user_by_id,
)

# MET values for common activities
MET_TABLE = {
    "Walking (slow)":       2.5,
    "Walking (brisk)":      3.8,
    "Jogging":              7.0,
    "Running":              9.8,
    "Cycling (light)":      4.0,
    "Cycling (moderate)":   6.8,
    "Cycling (vigorous)":   10.0,
    "Swimming (leisure)":   6.0,
    "Swimming (laps)":      8.0,
    "Yoga":                 3.0,
    "Pilates":              3.5,
    "Jump Rope":            12.3,
    "Dancing":              5.5,
    "Hiking":               6.0,
    "Stair Climbing":       8.0,
    "Rowing":               7.0,
    "Strength Training":    5.0,
    "HIIT":                 8.0,
    "Basketball":           6.5,
    "Soccer":               7.0,
    "Tennis":               7.3,
    "Badminton":            5.5,
    "Stretching":           2.3,
    "Gardening":            3.5,
    "Housework":            3.3,
}


def _calc_met_calories(met: float, weight_kg: float, duration_min: int) -> int:
    """Calories burned = MET × weight_kg × duration_hours."""
    duration_hours = duration_min / 60
    return int(met * weight_kg * duration_hours)


def render_exercise_logger():
    uid = st.session_state["user_id"]

    st.markdown(
        "<h2 style='color:#00E676;'>🏋️ Exercise Logger</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Log workouts with MET-based calorie calculation. Track burns and net calories.")
    st.write("---")

    user = get_user_by_id(uid) or {}
    weight_kg = user.get("weight_kg", 70)

    tab_log, tab_today, tab_trends = st.tabs(
        ["🏃 Log Exercise", "📊 Today's Summary", "📈 Trends"]
    )

    # ── TAB 1: LOG EXERCISE ─────────────────────────────
    with tab_log:
        st.markdown("### Log a Workout")

        mode = st.radio("Entry mode:", ["Select Activity", "Custom Activity"], horizontal=True)

        with st.form("met_exercise_form", clear_on_submit=True):
            if mode == "Select Activity":
                activity = st.selectbox("Activity", list(MET_TABLE.keys()))
                met_val = MET_TABLE[activity]
                st.info(f"MET value: **{met_val}** | Your weight: **{weight_kg} kg**")
            else:
                ec1, ec2 = st.columns(2)
                activity = ec1.text_input("Activity name *", placeholder="e.g. Rock Climbing")
                met_val = ec2.number_input("MET value", min_value=1.0, max_value=20.0, value=5.0, step=0.5)

            duration_min = st.slider("Duration (minutes)", 5, 180, 30, step=5)

            # Live calorie preview
            preview_cals = _calc_met_calories(met_val, weight_kg, duration_min)
            st.markdown(
                f"<div style='text-align:center; padding:15px; background:#1e1e1e; "
                f"border-radius:12px; border:1px solid #FF512F;'>"
                f"<p style='color:#bbb; margin:0;'>Estimated Burn</p>"
                f"<h2 style='color:#FF512F; margin:5px 0;'>🔥 {preview_cals} kcal</h2>"
                f"<p style='color:#888; margin:0; font-size:0.8rem;'>"
                f"MET {met_val} × {weight_kg}kg × {duration_min/60:.2f}hr</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            intensity = "Light" if met_val < 4 else "High" if met_val >= 7 else "Moderate"

            if st.form_submit_button("💪 Log Exercise", use_container_width=True):
                if mode == "Custom Activity" and not activity.strip():
                    st.error("Activity name is required.")
                else:
                    cals = _calc_met_calories(met_val, weight_kg, duration_min)
                    add_exercise_log(uid, activity.strip(), duration_min, cals, intensity)
                    st.success(f"Logged **{activity}** — {duration_min} min — **{cals} kcal** burned! 💪")
                    st.rerun()

        # Quick-add with MET calc
        st.write("---")
        st.markdown("#### ⚡ Quick Log")
        quick = [
            ("🚶 Walk 30min", "Walking (brisk)", 30),
            ("🏃 Run 20min", "Running", 20),
            ("🚴 Cycle 30min", "Cycling (moderate)", 30),
            ("🏋️ Weights 45min", "Strength Training", 45),
            ("🧘 Yoga 30min", "Yoga", 30),
            ("🏊 Swim 30min", "Swimming (laps)", 30),
            ("💃 Dance 30min", "Dancing", 30),
            ("🤸 HIIT 20min", "HIIT", 20),
        ]
        qcols = st.columns(4)
        for i, (label, act, dur) in enumerate(quick):
            if qcols[i % 4].button(label, use_container_width=True):
                met = MET_TABLE[act]
                cals = _calc_met_calories(met, weight_kg, dur)
                inten = "Light" if met < 4 else "High" if met >= 7 else "Moderate"
                add_exercise_log(uid, act, dur, cals, inten)
                st.success(f"Added **{act}** — **{cals} kcal** 🔥")
                st.rerun()

    # ── TAB 2: TODAY'S SUMMARY ──────────────────────────
    with tab_today:
        st.markdown("### Today's Exercise & Net Calories")

        net = get_net_calories_today(uid)
        nc1, nc2, nc3 = st.columns(3)
        nc1.metric("🍽️ Food Calories", f"{net['food_cals']} kcal")
        nc2.metric("🔥 Exercise Burn", f"{net['burned']} kcal")
        net_val = net["net"]
        nc3.metric("⚖️ Net Calories", f"{net_val} kcal",
                   delta=f"{-net['burned']} from exercise" if net["burned"] > 0 else None)

        # Net calorie gauge
        goal = user.get("daily_goal", 2000)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=net_val,
            delta={"reference": goal, "relative": False},
            gauge={
                "axis": {"range": [0, goal * 1.5]},
                "bar": {"color": "#00E676" if net_val <= goal else "#FF5252"},
                "steps": [
                    {"range": [0, goal * 0.8], "color": "rgba(0,230,118,0.15)"},
                    {"range": [goal * 0.8, goal], "color": "rgba(255,215,0,0.15)"},
                    {"range": [goal, goal * 1.5], "color": "rgba(255,82,82,0.15)"},
                ],
                "threshold": {"line": {"color": "white", "width": 2}, "thickness": 0.75, "value": goal},
            },
            title={"text": "Net Calories vs Goal"},
        ))
        fig_gauge.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            height=280, margin=dict(t=60, b=20),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Today's exercise list
        today_logs = get_exercise_logs_today(uid)
        if today_logs:
            st.markdown("#### Today's Workouts")
            for log in today_logs:
                st.markdown(
                    f"- **{log['activity_name']}** — {log['duration_min']} min — "
                    f"**{log['calories_burned']} kcal** ({log['intensity']})"
                )
        else:
            st.info("No exercises logged today.")

    # ── TAB 3: TRENDS ───────────────────────────────────
    with tab_trends:
        st.markdown("### Exercise & Net Calorie Trends")

        period = st.selectbox("Period", [7, 14, 30], format_func=lambda x: f"Last {x} days")

        net_data = get_daily_net_calories(uid, days=period)
        ex_data = get_daily_exercise_summary(uid, days=period)

        if not net_data and not ex_data:
            st.info("Not enough data yet.")
            return

        # Net calories chart
        if net_data:
            df_net = pd.DataFrame(net_data)
            df_net["net"] = df_net["food_cals"] - df_net["burned"]

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_net["day"], y=df_net["food_cals"],
                                 name="Food", marker_color="#00E676"))
            fig.add_trace(go.Bar(x=df_net["day"], y=[-b for b in df_net["burned"]],
                                 name="Exercise", marker_color="#FF512F"))
            fig.add_trace(go.Scatter(x=df_net["day"], y=df_net["net"],
                                     name="Net", line=dict(color="white", width=2)))
            fig.add_hline(y=goal, line_dash="dash", line_color="#FFD700",
                          annotation_text=f"Goal: {goal}")
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", barmode="relative",
                yaxis_title="Calories (kcal)", height=400,
                margin=dict(t=30, b=30),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Exercise volume chart
        if ex_data:
            df_ex = pd.DataFrame(ex_data)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=df_ex["day"], y=df_ex["total_burned"],
                                  name="Calories Burned", marker_color="#FF512F"))
            fig2.add_trace(go.Scatter(x=df_ex["day"], y=df_ex["total_minutes"],
                                      name="Minutes", yaxis="y2",
                                      line=dict(color="#00E676", width=2)))
            fig2.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis_title="Calories Burned", height=350,
                yaxis2=dict(title="Minutes", overlaying="y", side="right"),
                margin=dict(t=30, b=30),
            )
            st.plotly_chart(fig2, use_container_width=True)
