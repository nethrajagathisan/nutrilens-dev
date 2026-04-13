import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime

from core.database import (
    get_daily_calorie_summary,
    get_daily_exercise_summary,
    get_daily_hydration_summary,
    get_weight_history,
    get_meal_distribution,
    get_all_food_logs_range,
    get_streak_and_totals,
    get_user_by_id,
)
from core.ai_engine import chat_ai_rag
from core.rag_engine import build_user_log_context, get_retrieved_sources

# ── Chart theme defaults ──────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(20,20,30,0.6)",
    font=dict(color="white", family="Poppins, sans-serif"),
    margin=dict(t=40, b=30, l=10, r=10),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
)

MEAL_COLORS = {
    "Breakfast 🍳": "#FFD700",
    "Lunch 🥗":     "#00E676",
    "Dinner 🍗":    "#FF5252",
    "Snack 🍎":     "#85E3FF",
}


def render_analytics():
    uid        = st.session_state["user_id"]
    daily_goal = st.session_state.get("daily_goal", 2000)

    st.markdown(
        "<h2 style='color:#00E676;'>📉 Analytics Dashboard</h2>",
        unsafe_allow_html=True,
    )

    # ── Range picker ─────────────────────────────────────────────────────────
    range_opts = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30}
    sel = st.selectbox("📆 Time Range", list(range_opts.keys()),
                       key="analytics_range")
    days = range_opts[sel]

    # ── Pre-fetch all data ────────────────────────────────────────────────────
    cal_summary  = get_daily_calorie_summary(uid, days)
    hyd_summary  = get_daily_hydration_summary(uid, days)
    weight_hist  = get_weight_history(uid)
    meal_dist    = get_meal_distribution(uid, days)
    all_logs     = get_all_food_logs_range(uid, days)
    stats        = get_streak_and_totals(uid)
    db_user      = get_user_by_id(uid) or {}

    df_cal  = pd.DataFrame(cal_summary)  if cal_summary  else pd.DataFrame()
    df_hyd  = pd.DataFrame(hyd_summary)  if hyd_summary  else pd.DataFrame()
    df_logs = pd.DataFrame(all_logs)     if all_logs     else pd.DataFrame()
    df_meal = pd.DataFrame(meal_dist)    if meal_dist    else pd.DataFrame()

    # ── KPI Banner ───────────────────────────────────────────────────────────
    st.write("---")
    k1, k2, k3, k4, k5 = st.columns(5)
    today_cals = 0
    if not df_cal.empty:
        today_row = df_cal[df_cal["day"] == datetime.date.today().isoformat()]
        today_cals = int(today_row["total_cals"].values[0]) if not today_row.empty else 0

    k1.metric("🔥 Today", f"{today_cals} kcal",
              f"{today_cals - daily_goal:+d} vs goal")
    k2.metric("📅 Active Days",   str(stats["active_days"]))
    k3.metric("🔢 Total Entries", str(stats["total_entries"]))
    k4.metric("🏆 Log Streak",    f"{stats['streak']} days")
    k5.metric("♾️ Total Cals",
              f"{stats['total_cals']:,}" if stats["total_cals"] < 1_000_000
              else f"{stats['total_cals']/1000:.1f}k")

    st.write("---")

    # ── Section 1: Daily Calorie Intake ──────────────────────────────────────
    st.markdown("### 🔥 Daily Calorie Intake")
    if not df_cal.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_cal["day"],
            y=df_cal["total_cals"],
            name="Calories",
            marker=dict(
                color=df_cal["total_cals"].apply(
                    lambda v: "#00E676" if v <= daily_goal else "#FF5252"
                ),
                opacity=0.85,
            ),
            hovertemplate="%{x}<br><b>%{y} kcal</b><extra></extra>",
        ))
        fig.add_hline(
            y=daily_goal, line_dash="dash", line_color="#FFD700",
            annotation_text=f"Goal: {daily_goal} kcal",
            annotation_position="top left",
            annotation_font_color="#FFD700",
        )
        # 7-day rolling avg
        if len(df_cal) >= 3:
            df_cal["rolling_avg"] = (
                df_cal["total_cals"].rolling(min(7, len(df_cal)), min_periods=1).mean()
            )
            fig.add_trace(go.Scatter(
                x=df_cal["day"],
                y=df_cal["rolling_avg"].round(0),
                mode="lines",
                name="Rolling Avg",
                line=dict(color="#FFD700", width=2, dash="dot"),
                hovertemplate="%{x}<br>Avg: %{y:.0f} kcal<extra></extra>",
            ))
        fig.update_layout(height=320, **_LAYOUT,
                          legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True, key="an_daily_cals")
    else:
        st.info("No calorie data yet for this range.")

    # ── Section 2: Weekly Calorie Trend (7-day avg line) ────────────────────
    st.markdown("### 📈 Weekly Calorie Trend")
    full_cal = get_daily_calorie_summary(uid, 60)  # wider window for trend
    if full_cal and len(full_cal) >= 3:
        df_trend = pd.DataFrame(full_cal)
        df_trend["rolling_7"] = (
            df_trend["total_cals"].rolling(7, min_periods=1).mean().round(0)
        )
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_trend["day"],
            y=df_trend["rolling_7"],
            mode="lines+markers",
            name="7-day Avg",
            line=dict(color="#00E676", width=3),
            fill="tozeroy",
            fillcolor="rgba(0,230,118,0.08)",
            hovertemplate="%{x}<br>Avg: %{y} kcal<extra></extra>",
        ))
        fig_trend.add_hline(
            y=daily_goal, line_dash="dash", line_color="#FF5252",
            annotation_text="Daily Goal",
            annotation_position="top right",
            annotation_font_color="#FF5252",
        )
        fig_trend.update_layout(height=290, **_LAYOUT)
        st.plotly_chart(fig_trend, use_container_width=True, key="an_weekly_trend")
    else:
        st.info("Log food for at least 3 days to see trend data.")

    # ── Section 3: Macro Breakdown ───────────────────────────────────────────
    st.markdown("### 🧬 Macro Breakdown")
    if not df_logs.empty:
        mac_col1, mac_col2 = st.columns([1, 1.6])

        with mac_col1:
            # Aggregate donut
            total_c = int(df_logs["carbs"].sum())
            total_p = int(df_logs["protein"].sum())
            total_f = int(df_logs["fat"].sum())
            fig_donut = go.Figure(data=[go.Pie(
                labels=["Carbs", "Protein", "Fat"],
                values=[total_c, total_p, total_f],
                hole=0.62,
                marker_colors=["#FFABAB", "#85E3FF", "#B9FBC0"],
                textinfo="percent+label",
                hovertemplate="%{label}: %{value}g (%{percent})<extra></extra>",
            )])
            fig_donut.update_layout(
                height=290,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False,
                annotations=[dict(
                    text=f"{total_c+total_p+total_f}g<br>total",
                    x=0.5, y=0.5, font_size=14, font_color="white",
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_donut, use_container_width=True, key="an_macro_donut")

        with mac_col2:
            # Per-day stacked bar
            df_mac = (
                df_logs.groupby("logged_at")
                .agg(carbs=("carbs", "sum"), protein=("protein", "sum"), fat=("fat", "sum"))
                .reset_index()
            )
            df_mac["logged_at"] = pd.to_datetime(df_mac["logged_at"]).dt.date
            df_mac = df_mac.groupby("logged_at").sum().reset_index()

            fig_mac = go.Figure()
            for col, color, label in [
                ("carbs",   "#FFABAB", "Carbs"),
                ("protein", "#85E3FF", "Protein"),
                ("fat",     "#B9FBC0", "Fat"),
            ]:
                fig_mac.add_trace(go.Bar(
                    x=df_mac["logged_at"].astype(str),
                    y=df_mac[col],
                    name=label,
                    marker_color=color,
                    hovertemplate=f"{label}: %{{y}}g<extra></extra>",
                ))
            fig_mac.update_layout(
                barmode="stack", height=290,
                xaxis_title="Date", yaxis_title="grams",
                legend=dict(orientation="h", y=1.12),
                **_LAYOUT,
            )
            st.plotly_chart(fig_mac, use_container_width=True, key="an_macro_stack")
    else:
        st.info("No macro data yet for this range.")

    # ── Section 4: Hydration Trends ──────────────────────────────────────────
    st.markdown("### 💧 Hydration Trends")
    if not df_hyd.empty:
        target_ml = st.session_state.get("hydration_target", 3000)
        df_hyd["pct"] = (df_hyd["total_ml"] / target_ml * 100).round(1)
        fig_hyd = go.Figure()
        fig_hyd.add_trace(go.Bar(
            x=df_hyd["day"],
            y=df_hyd["total_ml"],
            name="Water (ml)",
            marker=dict(
                color=df_hyd["total_ml"].apply(
                    lambda v: "#85E3FF" if v >= target_ml else "#FFAB40"
                ),
                opacity=0.8,
            ),
            hovertemplate="%{x}<br><b>%{y} ml</b><extra></extra>",
        ))
        fig_hyd.add_trace(go.Scatter(
            x=df_hyd["day"],
            y=df_hyd["total_ml"].rolling(3, min_periods=1).mean().round(0),
            mode="lines",
            name="3-day Avg",
            line=dict(color="white", width=2, dash="dot"),
            hovertemplate="Avg: %{y:.0f} ml<extra></extra>",
        ))
        fig_hyd.add_hline(
            y=target_ml, line_dash="dash", line_color="#00E676",
            annotation_text=f"Goal: {target_ml} ml",
            annotation_position="top left",
            annotation_font_color="#00E676",
        )
        fig_hyd.update_layout(
            height=300, **_LAYOUT,
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig_hyd, use_container_width=True, key="an_hydration")

        met1, met2, met3 = st.columns(3)
        avg_hyd = int(df_hyd["total_ml"].mean())
        goal_days = int((df_hyd["total_ml"] >= target_ml).sum())
        met1.metric("Avg Daily Intake", f"{avg_hyd} ml")
        met2.metric("Days Hit Goal",    f"{goal_days} / {len(df_hyd)}")
        met3.metric("Best Day", f"{int(df_hyd['total_ml'].max())} ml")
    else:
        st.info("No hydration data yet for this range.")

    # ── Section 5: BMI Progress ──────────────────────────────────────────────
    st.markdown("### ⚖️ BMI Progress")
    if weight_hist:
        df_w = pd.DataFrame(weight_hist)
        df_w["logged_at"] = pd.to_datetime(df_w["logged_at"])
        h_m = db_user.get("height_cm", 175) / 100.0
        df_w["bmi"] = (df_w["weight_kg"] / h_m ** 2).round(1)

        bmi_col1, bmi_col2 = st.columns([1.6, 1])
        with bmi_col1:
            fig_bmi = go.Figure()
            # BMI zone bands
            for y0, y1, color, label in [
                (0,    18.5, "rgba(133,227,255,0.10)", "Underweight"),
                (18.5, 25,   "rgba(0,230,118,0.10)",   "Healthy"),
                (25,   30,   "rgba(255,211,0,0.10)",    "Overweight"),
                (30,   50,   "rgba(255,82,82,0.10)",    "Obese"),
            ]:
                fig_bmi.add_hrect(
                    y0=y0, y1=y1,
                    fillcolor=color, line_width=0,
                    annotation_text=label,
                    annotation_position="top right",
                    annotation_font_color="rgba(255,255,255,0.4)",
                    annotation_font_size=10,
                )
            fig_bmi.add_trace(go.Scatter(
                x=df_w["logged_at"],
                y=df_w["bmi"],
                mode="lines+markers",
                name="BMI",
                line=dict(color="#FFD700", width=3),
                marker=dict(size=7),
                hovertemplate="%{x|%d %b}<br>BMI: %{y}<extra></extra>",
            ))
            fig_bmi.update_layout(height=300, **_LAYOUT)
            fig_bmi.update_yaxes(range=[max(0, df_w["bmi"].min() - 2),
                                        df_w["bmi"].max() + 2])
            st.plotly_chart(fig_bmi, use_container_width=True, key="an_bmi")

        with bmi_col2:
            latest_bmi = df_w["bmi"].iloc[-1]
            first_bmi  = df_w["bmi"].iloc[0]
            bmi_cat = (
                "Underweight" if latest_bmi < 18.5
                else "Healthy ✅" if latest_bmi < 25
                else "Overweight ⚠️" if latest_bmi < 30
                else "Obese 🚨"
            )
            bmi_color = (
                "#85E3FF" if latest_bmi < 18.5
                else "#00E676" if latest_bmi < 25
                else "#FFD700" if latest_bmi < 30
                else "#FF5252"
            )
            st.markdown(
                f"""
                <div class="glass-card" style="text-align:center; padding:20px;">
                    <p style="color:#bbb; margin:0;">Current BMI</p>
                    <h1 style="color:{bmi_color}; font-size:3.5rem; margin:4px 0;">
                        {latest_bmi:.1f}
                    </h1>
                    <p style="color:{bmi_color}; font-weight:700;">{bmi_cat}</p>
                    <hr style="border-color:rgba(255,255,255,0.1);">
                    <p style="color:#bbb; font-size:0.85rem;">
                        Change: <b style="color:{'#00E676' if latest_bmi <= first_bmi else '#FF5252'};">
                        {latest_bmi - first_bmi:+.1f}</b> since first entry
                    </p>
                    <p style="color:#bbb; font-size:0.85rem;">
                        Entries: <b>{len(df_w)}</b>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No weight entries yet. Log your weight in the **📝 Tracker** page.")

    # ── Section 6: Meal Category Distribution ────────────────────────────────
    st.markdown("### 🍽️ Meal Category Distribution")
    if not df_meal.empty:
        dist_col1, dist_col2 = st.columns(2)

        with dist_col1:
            # Calories per meal
            colors = [MEAL_COLORS.get(m, "#aaa") for m in df_meal["meal"]]
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_meal["meal"],
                values=df_meal["total_cals"],
                hole=0.5,
                marker_colors=colors,
                textinfo="percent+label",
                hovertemplate="%{label}<br>%{value} kcal (%{percent})<extra></extra>",
            )])
            fig_pie.update_layout(
                title="Calories by Meal",
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                margin=dict(t=40, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True, key="an_meal_pie")

        with dist_col2:
            # Entries per meal bar
            fig_bar = go.Figure(data=[go.Bar(
                x=df_meal["meal"],
                y=df_meal["entry_count"],
                marker_color=[MEAL_COLORS.get(m, "#aaa") for m in df_meal["meal"]],
                text=df_meal["entry_count"],
                textposition="outside",
                hovertemplate="%{x}<br>%{y} entries<extra></extra>",
            )])
            fig_bar.update_layout(
                title="Number of Entries by Meal",
                height=300,
                xaxis_title="Meal",
                yaxis_title="Entries",
                **_LAYOUT,
            )
            st.plotly_chart(fig_bar, use_container_width=True, key="an_meal_bar")
    else:
        st.info("No meal data yet for this range.")

    # ── Section 7: Health Insights ───────────────────────────────────────────
    st.markdown("### 💡 Health Insights")
    insights = _generate_insights(df_cal, df_hyd, df_meal, daily_goal, db_user)
    for icon, text, kind in insights:
        if kind == "good":
            st.success(f"{icon} {text}")
        elif kind == "warn":
            st.warning(f"{icon} {text}")
        else:
            st.info(f"{icon} {text}")

    st.write("---")
    st.markdown("### 🤖 RAG Fitness & Nutrition Coach")
    st.caption("Uses the verified coach knowledge base plus your last 7 days of food, hydration, weight, and exercise logs.")
    with st.expander("📊 Last 7-Day Coach Context", expanded=False):
        st.code(build_user_log_context(uid, days=7))

    coach_query = (
        "Based on my last 7 days of food, hydration, weight, and exercise logs, "
        "what are the top 3 evidence-based nutrition and fitness adjustments I should make this week?"
    )
    if st.button("Generate Coach Insight", key="analytics_coach_button"):
        with st.spinner("Building personalized coach advice..."):
            st.session_state["coach_last_insight"] = chat_ai_rag(
                coach_query,
                "Analytics insight request",
                user_id=uid,
            )
            st.session_state["coach_last_sources"] = get_retrieved_sources(
                coach_query,
                top_k=4,
                user_id=uid,
                user_context="Analytics insight request",
            )

    if st.session_state.get("coach_last_insight"):
        st.info(st.session_state["coach_last_insight"])
        if st.session_state.get("coach_last_sources"):
            badges = ""
            for source in st.session_state["coach_last_sources"]:
                badges += (
                    f'<span style="display:inline-block; background:#1b5e20; color:white; '
                    f'padding:3px 10px; border-radius:12px; margin:2px 4px; font-size:0.85rem;">'
                    f'{source["topic"]} — {source["score"] * 100:.0f}%</span>'
                )
            st.markdown(badges, unsafe_allow_html=True)


def _generate_insights(df_cal, df_hyd, df_meal, daily_goal, db_user) -> list:
    tips = []

    # Calorie insights
    if not df_cal.empty:
        avg_cals = df_cal["total_cals"].mean()
        over_days = (df_cal["total_cals"] > daily_goal).sum()
        if over_days == 0:
            tips.append(("🎯", f"You stayed within your {daily_goal} kcal goal every day this period. Great discipline!", "good"))
        elif over_days <= len(df_cal) * 0.3:
            tips.append(("✅", f"You exceeded your calorie goal on {over_days} day(s). You're mostly on track!", "good"))
        else:
            tips.append(("⚠️", f"You went over your {daily_goal} kcal goal on {over_days} day(s). Try smaller portions.", "warn"))

        if avg_cals < daily_goal * 0.75:
            tips.append(("🍽️", f"Your average intake ({avg_cals:.0f} kcal) is well below your goal. Make sure you're eating enough!", "warn"))

    # Hydration insights
    if not df_hyd.empty:
        avg_hyd = df_hyd["total_ml"].mean()
        ht = st.session_state.get("hydration_target", 3000)
        if avg_hyd >= ht:
            tips.append(("💧", f"Excellent hydration! You're averaging {avg_hyd:.0f} ml/day — above the {ht}ml goal.", "good"))
        elif avg_hyd >= ht * 0.67:
            tips.append(("💧", f"Good hydration effort. Averaging {avg_hyd:.0f} ml/day — try to hit {ht} ml daily.", "info"))
        else:
            tips.append(("⚠️", f"Low hydration: only {avg_hyd:.0f} ml/day on average. Aim for at least {ht} ml.", "warn"))

    # Macro insights
    if not df_cal.empty and "total_protein" in df_cal.columns:
        avg_protein = df_cal["total_protein"].mean()
        weight_kg = db_user.get("weight_kg", 70)
        rec_protein = weight_kg * 0.8
        if avg_protein >= rec_protein:
            tips.append(("💪", f"Protein intake looks solid at {avg_protein:.0f}g/day (recommended ~{rec_protein:.0f}g).", "good"))
        else:
            tips.append(("🥩", f"Protein is low at {avg_protein:.0f}g/day. Aim for ~{rec_protein:.0f}g/day (0.8g per kg body weight).", "warn"))

    # Meal distribution
    if not df_meal.empty:
        meals_logged = set(df_meal["meal"].tolist())
        if "Breakfast 🍳" not in meals_logged:
            tips.append(("🍳", "You haven't logged breakfast recently. Starting the day with a balanced meal boosts metabolism.", "warn"))
        if len(meals_logged) >= 3:
            tips.append(("⚖️", "You're spreading meals across multiple categories — good for balanced nutrition!", "good"))

    if not tips:
        tips.append(("📊", "Log more meals and water to unlock personalised insights!", "info"))

    return tips
