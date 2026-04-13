import streamlit as st

from core.ai_engine import chat_ai_rag
from core.rag_engine import build_user_log_context, get_retrieved_sources
from core.nutrition_kb import KNOWLEDGE_BASE


def render_rag_chat():
    uid = st.session_state.get("user_id")
    if not uid:
        st.warning("Please log in first.")
        return

    ai_connected = bool(
        st.session_state.get("api_key") and st.session_state.get("active_model")
    )

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("## 💪 Fitness & Nutrition Coach")
    st.caption("Ask about nutrition, recovery, hydration, training fuel, or weight trends. Answers are grounded in a verified coach knowledge base plus your last 7 days of logs.")
    if not ai_connected:
        st.info("💡 AI is not connected — add `GEMINI_API_KEY` to your `.env` file for full responses. The page will still answer using the local coach knowledge base and your recent log data.")

    # Clear button (top-right)
    _, clear_col = st.columns([5, 1])
    with clear_col:
        if st.button("🗑️ Clear Chat"):
            st.session_state["rag_chat_history"] = []
            st.rerun()

    # ── Suggested questions ───────────────────────────────────────────────────
    suggestions = [
        "Am I eating enough protein for my weight and goals?",
        "What should I eat before and after workouts?",
        "How can I improve recovery after exercise?",
        "How much water and electrolytes do I need?",
        "Why am I not losing weight from my recent logs?",
        "Based on my last 7 days, what should I change next week?",
    ]
    cols = st.columns(len(suggestions))
    clicked_q = None
    for col, q in zip(cols, suggestions):
        if col.button(q, use_container_width=True):
            clicked_q = q

    # ── User input ────────────────────────────────────────────────────────────
    with st.expander("📊 Last 7-Day Coach Context", expanded=False):
        st.code(build_user_log_context(uid, days=7))

    user_input = st.chat_input("Ask your fitness and nutrition coach…")
    query = clicked_q or user_input

    if query:
        # Build personal context string
        diet = st.session_state.get("user_diet", "Balanced")
        goal = st.session_state.get("daily_goal", 2000)
        scan = st.session_state.get("scan_data")
        food_ctx = scan["name"] if scan else "No food scanned"
        user_context = f"Diet: {diet}, Daily goal: {goal} kcal, Current food: {food_ctx}"

        st.session_state["rag_chat_history"].append({"role": "user", "text": query})

        with st.spinner("Searching knowledge base and generating answer..."):
            sources = get_retrieved_sources(query, top_k=4, user_id=uid, user_context=user_context)
            reply = chat_ai_rag(query, user_context, user_id=uid)

        st.session_state["rag_chat_history"].append({
            "role": "assistant",
            "text": reply,
            "sources": sources,
        })
        st.rerun()

    # ── Chat history ──────────────────────────────────────────────────────────
    for msg in st.session_state.get("rag_chat_history", []):
        with st.chat_message(msg["role"]):
            st.write(msg["text"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("📖 Sources used (click to see)"):
                    badges = ""
                    for s in msg["sources"]:
                        pct = f"{s['score'] * 100:.0f}%"
                        badges += (
                            f'<span style="display:inline-block; background:#2e7d32; '
                            f'color:white; padding:3px 10px; border-radius:12px; '
                            f'margin:2px 4px; font-size:0.85rem;">'
                            f'{s["topic"]} — {pct}</span>'
                        )
                    st.markdown(badges, unsafe_allow_html=True)

    # ── Knowledge Base Info ───────────────────────────────────────────────────
    with st.expander("ℹ️ Knowledge Base Info"):
        topics = sorted(set(d["topic"] for d in KNOWLEDGE_BASE))
        st.markdown(f"**Total documents:** {len(KNOWLEDGE_BASE)}")
        st.markdown(f"**Topics covered:** {', '.join(topics)}")
