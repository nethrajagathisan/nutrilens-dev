"""
Nutritional Fingerprint — Streamlit UI page.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.fingerprint_engine import (
    update_fingerprint,
    analyze_deficiencies,
    compute_overall_health_score,
    get_fingerprint_trend,
    DIMENSION_LABELS,
    DIMENSION_EMOJIS,
    HEALTHY_REFERENCE,
)


def render_fingerprint():
    uid = st.session_state["user_id"]

    st.markdown(
        "<h2 style='color:#00E676;'>🧠 Nutritional Fingerprint</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Your evolving nutritional identity — a 10-dimensional vector updated "
        "every time you log food, smoothed with Exponential Moving Average."
    )
    st.write("---")

    # Update fingerprint on page load
    fingerprint = update_fingerprint(uid)
    health_score = compute_overall_health_score(fingerprint)
    deficiencies = analyze_deficiencies(fingerprint)

    # ── Section 1: Overall Health Score ──────────────────────────────────
    if health_score >= 75:
        score_color = "#00E676"
    elif health_score >= 50:
        score_color = "#FFD700"
    else:
        score_color = "#FF5252"

    st.markdown(
        f"""
        <div class="glass-card" style="text-align:center; padding:30px;">
            <p style="color:#aaa; margin:0; font-size:1rem;">Overall Health Score</p>
            <h1 style="color:{score_color}; font-size:4rem; margin:0;">
                {health_score}
            </h1>
            <p style="color:#aaa; margin:0; font-size:1rem;">out of 100</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("---")

    # ── Section 2: Radar Chart + Deficiency Alerts ───────────────────────
    col_radar, col_alerts = st.columns([1.2, 1])

    with col_radar:
        st.markdown("### 🕸️ Fingerprint Radar")
        angular_labels = [
            f"{DIMENSION_EMOJIS[i]} {DIMENSION_LABELS[i]}" for i in range(10)
        ]

        fig = go.Figure()
        # Healthy reference trace
        fig.add_trace(go.Scatterpolar(
            r=HEALTHY_REFERENCE + [HEALTHY_REFERENCE[0]],
            theta=angular_labels + [angular_labels[0]],
            name="Healthy Goal",
            line=dict(color="#00E676", dash="dash", width=2),
            fill="none",
            opacity=0.6,
        ))
        # User fingerprint trace
        fig.add_trace(go.Scatterpolar(
            r=fingerprint + [fingerprint[0]],
            theta=angular_labels + [angular_labels[0]],
            name="Your Fingerprint",
            line=dict(color="#448AFF", width=3),
            fill="toself",
            fillcolor="rgba(68,138,255,0.15)",
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    visible=True, range=[0, 1.05],
                    gridcolor="rgba(255,255,255,0.1)",
                ),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            ),
            showlegend=True,
            legend=dict(font=dict(color="white")),
            height=420,
            margin=dict(t=30, b=30, l=60, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True, key="fp_radar")

    with col_alerts:
        st.markdown("### 🔔 Dimension Alerts")
        for item in deficiencies:
            if item["severity"] == "critical":
                border_color = "#FF5252"
            elif item["severity"] == "caution":
                border_color = "#FFD700"
            else:
                border_color = "#00E676"

            pct = int(item["score"] * 100)
            st.markdown(
                f"""
                <div style="
                    border-left: 4px solid {border_color};
                    background: rgba(255,255,255,0.04);
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 8px;
                ">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:white; font-weight:600;">
                            {item['emoji']} {item['label']}
                        </span>
                        <span style="color:{border_color}; font-weight:700;">
                            {pct}%
                        </span>
                    </div>
                    <div style="
                        background: rgba(255,255,255,0.1);
                        border-radius: 4px;
                        height: 8px;
                        margin-top: 6px;
                        overflow: hidden;
                    ">
                        <div style="
                            width: {pct}%;
                            height: 100%;
                            background: {border_color};
                            border-radius: 4px;
                        "></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("---")

    # ── Section 3: Trend Timeline ────────────────────────────────────────
    st.markdown("### 📈 Health Score Trend")
    period = st.selectbox(
        "Period",
        ["Last 7 days", "Last 14 days", "Last 30 days"],
        index=1,
        key="fp_period",
    )
    period_days = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30}[period]

    trend = get_fingerprint_trend(uid, period_days)

    if trend:
        days_list = [t["day"] for t in trend]
        scores_list = [t["health_score"] for t in trend]

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=days_list, y=scores_list,
            mode="lines+markers",
            name="Health Score",
            line=dict(color="#448AFF", width=3),
            fill="tozeroy",
            fillcolor="rgba(68,138,255,0.1)",
        ))
        # Reference lines
        fig_trend.add_hline(
            y=75, line_dash="dash", line_color="#00E676",
            annotation_text="Target",
            annotation_position="top left",
            annotation_font_color="#00E676",
        )
        fig_trend.add_hline(
            y=50, line_dash="dash", line_color="#FFD700",
            annotation_text="Caution",
            annotation_position="bottom left",
            annotation_font_color="#FFD700",
        )
        fig_trend.update_layout(
            yaxis=dict(range=[0, 105], title="Score", gridcolor="rgba(255,255,255,0.08)"),
            xaxis=dict(title="Date", gridcolor="rgba(255,255,255,0.08)"),
            height=350,
            margin=dict(t=20, b=40, l=40, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            showlegend=False,
        )
        st.plotly_chart(fig_trend, use_container_width=True, key="fp_trend")
    else:
        st.info("No historical data yet — keep logging meals to see your trend!")

    st.write("---")

    # ── Section 4: Raw Vector Expander ───────────────────────────────────
    with st.expander("🔬 View Raw Fingerprint Vector"):
        rows = []
        for i in range(10):
            rows.append({
                "Dimension": f"{DIMENSION_EMOJIS[i]} {DIMENSION_LABELS[i]}",
                "Your Score": round(fingerprint[i], 3),
                "Healthy Goal": HEALTHY_REFERENCE[i],
                "Gap": round(HEALTHY_REFERENCE[i] - fingerprint[i], 3),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
