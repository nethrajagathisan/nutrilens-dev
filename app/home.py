import datetime
import streamlit as st

from core.database import (
    get_food_logs_today,
    get_hydration_today,
    get_exercise_logs_today,
    get_user_by_id,
    get_weight_history,
    add_hydration,
)
from core.ai_engine import chat_ai_rag


def render_home():
    uid = st.session_state["user_id"]
    daily_goal = st.session_state["daily_goal"]
    username = st.session_state.get("username", "friend")
    goal_type = st.session_state.get("goal_type", "maintain")

    # Greeting
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    st.markdown(
        f"<h2 style='margin-bottom:0;'>{greeting}, {username}! 👋</h2>"
        f"<p style='color:#aaa; margin-top:0;'>Here's your day at a glance</p>",
        unsafe_allow_html=True,
    )

    # ─── GOAL PROGRESS ──────────────────────────────────
    food_logs = get_food_logs_today(uid)
    total_cal = sum(log["calories"] for log in food_logs)
    total_carbs = sum(log.get("carbs", 0) for log in food_logs)
    total_protein = sum(log.get("protein", 0) for log in food_logs)
    total_fat = sum(log.get("fat", 0) for log in food_logs)

    cal_pct = min(total_cal / max(daily_goal, 1) * 100, 120)
    cal_cls = "progress-bar-fill"
    if cal_pct > 100:
        cal_cls += " over"
    elif cal_pct > 85:
        cal_cls += " warn"

    st.markdown('<div class="goal-progress-container">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="display:flex; justify-content:space-between; align-items:baseline;">'
        f'<span style="font-size:1.1rem; font-weight:700; color:#fff;">🔥 Calories</span>'
        f'<span style="color:#aaa;">{total_cal} / {daily_goal} kcal</span>'
        f'</div>'
        f'<div class="progress-bar-outer">'
        f'<div class="{cal_cls}" style="width:{min(cal_pct, 100):.0f}%;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Macro mini-bars
    macro_targets = {"Carbs": int(daily_goal * 0.5 / 4), "Protein": int(daily_goal * 0.25 / 4), "Fat": int(daily_goal * 0.25 / 9)}
    macro_actuals = {"Carbs": total_carbs, "Protein": total_protein, "Fat": total_fat}
    macro_colors = {"Carbs": "#4FC3F7", "Protein": "#AB47BC", "Fat": "#FFB74D"}

    mc = st.columns(3)
    for i, (macro, target) in enumerate(macro_targets.items()):
        actual = macro_actuals[macro]
        pct = min(actual / max(target, 1) * 100, 100)
        with mc[i]:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<span style="font-size:0.8rem; color:#888;">{macro}</span><br>'
                f'<span style="font-weight:700; color:{macro_colors[macro]};">{actual}g</span>'
                f'<span style="color:#666;"> / {target}g</span>'
                f'<div class="progress-bar-outer" style="height:8px;">'
                f'<div style="height:100%; border-radius:12px; width:{pct:.0f}%; background:{macro_colors[macro]};"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── SMART LOG BAR ──────────────────────────────────
    st.markdown('<div class="smart-log-bar">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">⚡ Smart Log</div>',
        unsafe_allow_html=True,
    )

    sl_cols = st.columns([0.8, 6, 0.8, 0.8])
    with sl_cols[0]:
        camera_clicked = st.button("📸", key="smart_cam", help="Scan food with camera")
    with sl_cols[1]:
        smart_text = st.text_input(
            "smart_log",
            placeholder="Describe what you ate or ask a nutrition question…",
            label_visibility="collapsed",
            key="smart_log_input",
        )
    with sl_cols[2]:
        mic_clicked = st.button("🎙️", key="smart_mic", help="Voice input")
    with sl_cols[3]:
        send_clicked = st.button("➤", key="smart_send", help="Send")
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle Smart Log actions
    if camera_clicked:
        st.session_state["page"] = "📸 Scan & Eat"
        st.rerun()
    if mic_clicked:
        st.session_state["page"] = "🎙️ Voice Logger"
        st.rerun()
    if (send_clicked or smart_text) and smart_text and smart_text.strip():
        _handle_smart_log(smart_text.strip(), uid)

    # ─── TODAY CARDS ─────────────────────────────────────
    st.markdown(
        '<div class="section-header">📋 Today</div>',
        unsafe_allow_html=True,
    )

    water_ml = get_hydration_today(uid)
    exercise_logs = get_exercise_logs_today(uid)
    total_burn = sum(e["calories_burned"] for e in exercise_logs)
    meal_count = len(food_logs)

    # Weight
    weight_hist = get_weight_history(uid)
    user = get_user_by_id(uid)
    current_weight = weight_hist[-1]["weight_kg"] if weight_hist else (user["weight_kg"] if user else 0)

    tc = st.columns(4)
    cards = [
        ("🍽️", "Meals", str(meal_count), f"{total_cal} kcal logged"),
        ("🏃", "Exercise", f"{total_burn}", "kcal burned"),
        ("💧", "Water", f"{water_ml}", f"/ 3000 ml"),
        ("⚖️", "Weight", f"{current_weight:.1f}", "kg"),
    ]
    for i, (icon, label, value, sub) in enumerate(cards):
        with tc[i]:
            st.markdown(
                f'<div class="today-card">'
                f'<div class="today-card-icon">{icon}</div>'
                f'<div class="today-card-label">{label}</div>'
                f'<div class="today-card-value">{value}</div>'
                f'<div class="today-card-sub">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ─── QUICK ACTIONS ───────────────────────────────────
    st.write("")
    st.markdown(
        '<div class="section-header">⚡ Quick Actions</div>',
        unsafe_allow_html=True,
    )
    qa = st.columns(4)
    actions = [
        ("📸 Scan Food", "📸 Scan & Eat"),
        ("📝 Log Meal", "📝 Tracker"),
        ("🏋️ Log Exercise", "🏋️ Exercise Logger"),
        ("💧 Add Water", None),
    ]
    for i, (label, page) in enumerate(actions):
        with qa[i]:
            if page:
                if st.button(label, key=f"qa_{i}", use_container_width=True):
                    st.session_state["page"] = page
                    st.rerun()
            else:
                if st.button(label, key=f"qa_{i}", use_container_width=True):
                    add_hydration(uid, 250)
                    st.session_state["water_ml"] = get_hydration_today(uid)
                    st.rerun()

    # ─── AI RECOMMENDATIONS ──────────────────────────────
    st.write("")
    st.markdown(
        '<div class="section-header">🤖 AI Recommendations</div>',
        unsafe_allow_html=True,
    )

    remaining = daily_goal - total_cal
    goal_label = {"lose": "deficit", "gain": "surplus", "maintain": "balance"}.get(goal_type, "balance")

    recs = []
    if remaining > 400:
        recs.append(("🍽️ Meal Suggestion", f"You have **{remaining} kcal** remaining. Consider a nutritious meal to stay on track for your {goal_label} goal."))
    elif remaining < 0:
        recs.append(("⚠️ Over Goal", f"You're **{abs(remaining)} kcal** over your daily target. A light walk could help balance things out."))
    else:
        recs.append(("✅ On Track", f"Only **{remaining} kcal** left — you're doing great today!"))

    if water_ml < 2000:
        recs.append(("💧 Hydration Reminder", f"You've had {water_ml}ml today. Try to reach 3000ml for optimal health."))

    if total_burn == 0:
        recs.append(("🏃 Get Moving", "No exercise logged yet. Even a 15-minute walk can boost your mood and metabolism!"))

    for title, text in recs:
        st.markdown(
            f'<div class="ai-card">'
            f'<div class="ai-card-title">{title}</div>'
            f'<div class="ai-card-text">{text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _handle_smart_log(text: str, uid: int):
    """Process smart log input — either log food or answer a question."""
    # Check if it looks like a question
    question_words = ["what", "how", "why", "is", "can", "should", "does", "which", "tell", "explain"]
    is_question = text.endswith("?") or any(text.lower().startswith(w) for w in question_words)

    if is_question:
        # Route to AI chat
        with st.spinner("Thinking..."):
            reply = chat_ai_rag(text, "General", user_id=uid)
        st.markdown(
            f'<div class="ai-card">'
            f'<div class="ai-card-title">🤖 NutriLens AI</div>'
            f'<div class="ai-card-text">{reply}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        # Route to food logging via voice parser
        st.info(f"💡 To log \"{text}\", use the **Voice Logger** or **Tracker** for accurate macro tracking.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎙️ Open Voice Logger", key="sl_voice"):
                st.session_state["page"] = "🎙️ Voice Logger"
                st.rerun()
        with col2:
            if st.button("📝 Open Tracker", key="sl_tracker"):
                st.session_state["page"] = "📝 Tracker"
                st.rerun()
