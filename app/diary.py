import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime

from core.database import (
    get_food_logs_today,
    get_food_logs_by_date,
    clear_food_logs_today,
    delete_food_log,
    get_daily_calorie_summary,
    get_daily_hydration_summary,
    get_hydration_by_date,
    get_weight_history,
)

MEAL_ORDER = ["Breakfast 🍳", "Lunch 🥗", "Dinner 🍗", "Snack 🍎"]
MEAL_COLORS = {
    "Breakfast 🍳": "#FFD700",
    "Lunch 🥗":     "#00E676",
    "Dinner 🍗":    "#FF5252",
    "Snack 🍎":     "#85E3FF",
}


def render_diary():
    uid = st.session_state["user_id"]
    daily_goal = st.session_state.get("daily_goal", 2000)

    st.markdown(
        "<h2 style='color:#00E676;'>📊 My Diary</h2>",
        unsafe_allow_html=True,
    )

    tab_today, tab_calendar, tab_timeline, tab_weight = st.tabs(
        ["📅 Today", "🗓️ Calendar", "📈 Timeline", "⚖️ Weight History"]
    )

    # ── TAB 1: TODAY ─────────────────────────────────────────────────────────
    with tab_today:
        logs = get_food_logs_today(uid)
        _render_day_view(uid, logs, daily_goal,
                         datetime.date.today().isoformat(), allow_clear=True,
                         key_prefix="today")

    # ── TAB 2: CALENDAR ──────────────────────────────────────────────────────
    with tab_calendar:
        st.markdown("### 🗓️ Browse Any Day")
        selected_date = st.date_input(
            "Select a date",
            value=datetime.date.today(),
            max_value=datetime.date.today(),
        )
        date_str = selected_date.isoformat()
        logs = get_food_logs_by_date(uid, date_str)
        hydration_ml = get_hydration_by_date(uid, date_str)

        st.caption(f"Showing logs for **{selected_date.strftime('%A, %d %B %Y')}**")

        if not logs and hydration_ml == 0:
            st.info("No entries recorded for this day.")
        else:
            _render_day_view(uid, logs, daily_goal, date_str, allow_clear=False,
                             key_prefix=f"cal_{date_str}")
            if hydration_ml:
                st.markdown(f"💧 **Hydration:** {hydration_ml} ml logged")

    # ── TAB 3: TIMELINE ──────────────────────────────────────────────────────
    with tab_timeline:
        st.markdown("### 📈 Trends Over Time")

        days_opts = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30}
        days_label = st.selectbox("Range", list(days_opts.keys()))
        days = days_opts[days_label]

        cal_summary  = get_daily_calorie_summary(uid, days)
        hyd_summary  = get_daily_hydration_summary(uid, days)

        # Calories chart
        if cal_summary:
            df_cal = pd.DataFrame(cal_summary)
            fig_cal = go.Figure()
            fig_cal.add_trace(go.Bar(
                x=df_cal["day"], y=df_cal["total_cals"],
                name="Calories", marker_color="#FF5252",
            ))
            fig_cal.add_hline(
                y=daily_goal, line_dash="dash",
                line_color="#FFD700",
                annotation_text=f"Goal: {daily_goal} kcal",
                annotation_position="top left",
            )
            fig_cal.update_layout(
                title="🔥 Daily Calories",
                xaxis_title="Date", yaxis_title="kcal",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=300,
            )
            st.plotly_chart(fig_cal, use_container_width=True, key="timeline_calories")
            fig_mac = go.Figure()
            for macro, color in [
                ("total_carbs",   "#FFABAB"),
                ("total_protein", "#85E3FF"),
                ("total_fat",     "#B9FBC0"),
            ]:
                fig_mac.add_trace(go.Bar(
                    x=df_cal["day"], y=df_cal[macro],
                    name=macro.replace("total_", "").title(),
                    marker_color=color,
                ))
            fig_mac.update_layout(
                barmode="stack",
                title="🧬 Daily Macros (g)",
                xaxis_title="Date", yaxis_title="grams",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=300,
            )
            st.plotly_chart(fig_mac, use_container_width=True, key="timeline_macros")
        else:
            st.info("No food logs yet for this period. Start tracking!")

        # Hydration chart
        if hyd_summary:
            df_hyd = pd.DataFrame(hyd_summary)
            fig_hyd = go.Figure()
            fig_hyd.add_trace(go.Scatter(
                x=df_hyd["day"], y=df_hyd["total_ml"],
                mode="lines+markers",
                name="Hydration",
                line=dict(color="#85E3FF", width=3),
                fill="tozeroy",
                fillcolor="rgba(133, 227, 255, 0.15)",
            ))
            fig_hyd.add_hline(
                y=st.session_state.get("hydration_target", 3000), line_dash="dash", line_color="#00E676",
                annotation_text=f"Goal: {st.session_state.get('hydration_target', 3000)} ml",
                annotation_position="top left",
            )
            fig_hyd.update_layout(
                title="💧 Daily Hydration",
                xaxis_title="Date", yaxis_title="ml",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=280,
            )
            st.plotly_chart(fig_hyd, use_container_width=True, key="timeline_hydration")
        else:
            st.info("No hydration logs yet for this period.")

    # ── TAB 4: WEIGHT HISTORY ────────────────────────────────────────────────
    with tab_weight:
        st.markdown("### ⚖️ Weight & BMI History")
        weight_history = get_weight_history(uid)

        if weight_history:
            df_w = pd.DataFrame(weight_history)
            df_w["logged_at"] = pd.to_datetime(df_w["logged_at"])

            height_m = st.session_state.get("bmi", 0)
            # Get actual height from DB user (re-fetch once)
            from core.database import get_user_by_id
            db_user = get_user_by_id(uid) or {}
            h_m = db_user.get("height_cm", 175) / 100.0
            df_w["bmi"] = (df_w["weight_kg"] / (h_m ** 2)).round(1)

            # Latest entry stats
            latest = df_w.iloc[-1]
            first  = df_w.iloc[0]
            delta_kg = latest["weight_kg"] - first["weight_kg"]

            sw1, sw2, sw3 = st.columns(3)
            sw1.metric("Current Weight", f"{latest['weight_kg']} kg",
                       f"{delta_kg:+.1f} kg since start")
            sw2.metric("Current BMI", f"{latest['bmi']:.1f}")
            sw3.metric("Entries Logged", len(df_w))

            fig_w = go.Figure()
            fig_w.add_trace(go.Scatter(
                x=df_w["logged_at"], y=df_w["weight_kg"],
                mode="lines+markers",
                name="Weight (kg)",
                line=dict(color="#FFD700", width=3),
                marker=dict(size=8),
            ))
            fig_w.update_layout(
                title="⚖️ Weight Over Time",
                xaxis_title="Date", yaxis_title="kg",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=300,
            )
            st.plotly_chart(fig_w, use_container_width=True, key="weight_history")

            fig_bmi = go.Figure()
            fig_bmi.add_trace(go.Scatter(
                x=df_w["logged_at"], y=df_w["bmi"],
                mode="lines+markers",
                name="BMI",
                line=dict(color="#B9FBC0", width=3),
                fill="tozeroy",
                fillcolor="rgba(185,251,192,0.1)",
            ))
            for y_val, color, label in [
                (18.5, "#85E3FF", "Underweight"),
                (25.0, "#00E676", "Healthy"),
                (30.0, "#FFD700", "Overweight"),
            ]:
                fig_bmi.add_hline(
                    y=y_val, line_dash="dot", line_color=color,
                    annotation_text=label, annotation_position="top right",
                )
            fig_bmi.update_layout(
                title="📊 BMI Trend",
                xaxis_title="Date", yaxis_title="BMI",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                height=300,
            )
            st.plotly_chart(fig_bmi, use_container_width=True, key="bmi_trend")

            with st.expander("View Raw Data"):
                st.dataframe(
                    df_w[["logged_at", "weight_kg", "bmi"]].rename(
                        columns={"logged_at": "Date", "weight_kg": "Weight (kg)", "bmi": "BMI"}
                    ),
                    use_container_width=True,
                )
        else:
            st.info("No weight entries yet. Log your weight in the **📝 Tracker** page.")


# ── SHARED: DAY VIEW ─────────────────────────────────────────────────────────

def _render_day_view(uid: int, logs: list, daily_goal: int,
                     date_str: str, allow_clear: bool, key_prefix: str = "day"):
    """Render a single day's food logs grouped by meal with macro breakdown."""
    if not logs:
        st.info("No food entries for this day. Use **📝 Tracker** to log a meal!")
        return

    df = pd.DataFrame(logs)
    total_cals    = df["calories"].sum()
    total_carbs   = df["carbs"].sum()
    total_protein = df["protein"].sum()
    total_fat     = df["fat"].sum()

    # Summary metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔥 Calories", f"{total_cals}", f"Goal {daily_goal}")
    m2.metric("🍞 Carbs",    f"{total_carbs}g")
    m3.metric("💪 Protein",  f"{total_protein}g")
    m4.metric("🧈 Fat",      f"{total_fat}g")
    remaining = max(daily_goal - total_cals, 0)
    m5.metric("📉 Remaining", f"{remaining} kcal")

    st.progress(min(total_cals / daily_goal, 1.0))

    # Macro donut
    donut_col, log_col = st.columns([1, 2])
    with donut_col:
        if total_carbs + total_protein + total_fat > 0:
            fig = go.Figure(data=[go.Pie(
                labels=["Carbs", "Protein", "Fat"],
                values=[total_carbs, total_protein, total_fat],
                hole=0.65,
                marker_colors=["#FFABAB", "#85E3FF", "#B9FBC0"],
                textinfo="percent",
            )])
            fig.update_layout(
                height=220,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                showlegend=True,
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_donut")

    # Meal-categorised log
    with log_col:
        for meal in MEAL_ORDER:
            meal_logs = df[df["meal"] == meal]
            if meal_logs.empty:
                continue
            color = MEAL_COLORS.get(meal, "#aaa")
            meal_cals = meal_logs["calories"].sum()
            st.markdown(
                f"<p style='color:{color}; font-weight:700; margin-bottom:4px;'>"
                f"{meal} — {meal_cals} kcal</p>",
                unsafe_allow_html=True,
            )
            for _, row in meal_logs.iterrows():
                entry_col, del_col = st.columns([5, 1])
                entry_col.markdown(
                    f"<small style='color:#ddd;'>• <b>{row['name']}</b> &nbsp;"
                    f"{row['calories']} kcal &nbsp;|&nbsp; "
                    f"C:{row['carbs']}g P:{row['protein']}g F:{row['fat']}g</small>",
                    unsafe_allow_html=True,
                )
                if del_col.button("🗑️", key=f"{key_prefix}_del_{row['id']}",
                                  help="Delete this entry"):
                    delete_food_log(row["id"], uid)
                    st.rerun()

    if allow_clear:
        st.write("")
        if st.button("🗑️ Clear All Today's Entries", type="secondary"):
            clear_food_logs_today(uid)
            st.rerun()
