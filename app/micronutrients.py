import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.database import get_micronutrient_summary, get_user_by_id

# Recommended Daily Intake (RDI) values
RDI = {
    "iron":      {"male": 8, "female": 18, "unit": "mg", "emoji": "🩸"},
    "calcium":   {"male": 1000, "female": 1000, "unit": "mg", "emoji": "🦴"},
    "vitamin_c": {"male": 90, "female": 75, "unit": "mg", "emoji": "🍊"},
    "vitamin_d": {"male": 15, "female": 15, "unit": "µg", "emoji": "☀️"},
    "fiber":     {"male": 38, "female": 25, "unit": "g", "emoji": "🌾"},
    "sodium":    {"male": 2300, "female": 2300, "unit": "mg", "emoji": "🧂"},
    "sugar":     {"male": 36, "female": 25, "unit": "g", "emoji": "🍬"},
}

DISPLAY_NAMES = {
    "iron": "Iron", "calcium": "Calcium", "vitamin_c": "Vitamin C",
    "vitamin_d": "Vitamin D", "fiber": "Fiber", "sodium": "Sodium", "sugar": "Sugar",
}


def _get_rdi(nutrient: str, gender: str) -> float:
    g = "female" if "Female" in gender or "female" in gender.lower() else "male"
    return RDI[nutrient][g]


def render_micronutrients():
    uid = st.session_state["user_id"]

    st.markdown(
        "<h2 style='color:#00E676;'>🔬 Micronutrient Tracker</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Track iron, calcium, vitamins, fiber, sodium & sugar — 7-day averages vs recommended intake.")
    st.write("---")

    user = get_user_by_id(uid) or {}
    gender = user.get("gender", "Male")

    summary = get_micronutrient_summary(uid, days=7)

    if not summary:
        st.info("No micronutrient data yet. Log some food to start tracking! 🍽️")
        return

    df = pd.DataFrame(summary)
    num_days = len(df)
    nutrients = ["iron", "calcium", "vitamin_c", "vitamin_d", "fiber", "sodium", "sugar"]

    # Compute 7-day averages
    averages = {}
    for n in nutrients:
        averages[n] = df[n].sum() / num_days if num_days > 0 else 0

    # ── KPI CARDS ───────────────────────────────────────
    st.markdown("### 📊 7-Day Daily Averages vs Recommended Intake")
    cols = st.columns(len(nutrients))
    for i, n in enumerate(nutrients):
        rdi = _get_rdi(n, gender)
        avg = averages[n]
        pct = (avg / rdi * 100) if rdi > 0 else 0

        # Sodium and sugar: over is bad
        if n in ("sodium", "sugar"):
            if pct > 120:
                status_color = "#FF5252"
                status = "⚠️ HIGH"
            elif pct >= 80:
                status_color = "#FFD700"
                status = "✅ OK"
            else:
                status_color = "#00E676"
                status = "✅ Good"
        else:
            if pct < 60:
                status_color = "#FF5252"
                status = "⚠️ LOW"
            elif pct < 80:
                status_color = "#FFD700"
                status = "⚡ Fair"
            else:
                status_color = "#00E676"
                status = "✅ Good"

        cols[i].markdown(
            f"<div style='text-align:center; padding:10px; background:#1e1e1e; "
            f"border-radius:12px; border:1px solid {status_color};'>"
            f"<p style='font-size:1.5rem; margin:0;'>{RDI[n]['emoji']}</p>"
            f"<p style='color:#bbb; margin:0; font-size:0.75rem;'>{DISPLAY_NAMES[n]}</p>"
            f"<h3 style='color:{status_color}; margin:4px 0;'>{avg:.1f}</h3>"
            f"<p style='color:#888; margin:0; font-size:0.7rem;'>/ {rdi} {RDI[n]['unit']}</p>"
            f"<p style='color:{status_color}; margin:4px 0; font-size:0.8rem;'>{status}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── DEFICIENCY HIGHLIGHTS ───────────────────────────
    st.write("---")
    st.markdown("### 🚨 Deficiency Report")

    deficiencies = []
    excesses = []
    for n in nutrients:
        rdi = _get_rdi(n, gender)
        avg = averages[n]
        pct = (avg / rdi * 100) if rdi > 0 else 0
        if n in ("sodium", "sugar"):
            if pct > 120:
                excesses.append((n, avg, rdi, pct))
        else:
            if pct < 70:
                deficiencies.append((n, avg, rdi, pct))

    if deficiencies:
        for n, avg, rdi, pct in deficiencies:
            st.warning(
                f"{RDI[n]['emoji']} **{DISPLAY_NAMES[n]}** is low: "
                f"**{avg:.1f} {RDI[n]['unit']}** / day "
                f"({pct:.0f}% of {rdi} {RDI[n]['unit']} RDI)"
            )
    if excesses:
        for n, avg, rdi, pct in excesses:
            st.error(
                f"{RDI[n]['emoji']} **{DISPLAY_NAMES[n]}** is high: "
                f"**{avg:.1f} {RDI[n]['unit']}** / day "
                f"({pct:.0f}% of {rdi} {RDI[n]['unit']} RDI)"
            )
    if not deficiencies and not excesses:
        st.success("No deficiencies or excesses detected! Keep it up! 🎉")

    # ── BAR CHART: Avg vs RDI ───────────────────────────
    st.write("---")
    st.markdown("### 📈 Average Intake vs Recommended")

    # Normalize to percentage of RDI for comparison
    names = [DISPLAY_NAMES[n] for n in nutrients]
    avg_pcts = [(averages[n] / _get_rdi(n, gender) * 100) for n in nutrients]
    bar_colors = []
    for n in nutrients:
        pct = averages[n] / _get_rdi(n, gender) * 100 if _get_rdi(n, gender) > 0 else 0
        if n in ("sodium", "sugar"):
            bar_colors.append("#FF5252" if pct > 120 else "#00E676" if pct <= 100 else "#FFD700")
        else:
            bar_colors.append("#FF5252" if pct < 60 else "#FFD700" if pct < 80 else "#00E676")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=avg_pcts, marker_color=bar_colors,
        name="Your Avg", text=[f"{p:.0f}%" for p in avg_pcts], textposition="auto",
    ))
    fig.add_hline(y=100, line_dash="dash", line_color="white", annotation_text="100% RDI")
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", yaxis_title="% of Recommended Daily Intake",
        height=400, margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── DAILY TREND TABLE ───────────────────────────────
    st.write("---")
    st.markdown("### 📅 Daily Breakdown")
    display_df = df.copy()
    display_df.columns = ["Day"] + [f"{RDI[n]['emoji']} {DISPLAY_NAMES[n]} ({RDI[n]['unit']})" for n in nutrients]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
