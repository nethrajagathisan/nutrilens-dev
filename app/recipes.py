import streamlit as st
import plotly.graph_objects as go

from core.database import get_saved_recipes, delete_recipe


def render_recipes():
    st.markdown(
        "<h2 style='color:#FFD700;'>🍽️ Recipe Corner</h2>",
        unsafe_allow_html=True,
    )

    uid = st.session_state["user_id"]
    recipes = get_saved_recipes(uid)

    if not recipes:
        st.info("No saved recipes yet! Scan a food or fridge image to generate and save recipes.")
        return

    # ── Filters ──────────────────────────────────────
    f1, f2, f3 = st.columns([1, 1, 2])
    diets = sorted({r["diet"] for r in recipes if r["diet"]})
    diet_filter = f1.selectbox("Diet", ["All"] + diets, key="rc_diet")
    sources = sorted({r["source_food"] for r in recipes if r["source_food"]})
    source_filter = f2.selectbox("Source", ["All"] + sources, key="rc_source")
    search = f3.text_input("🔍 Search recipes", key="rc_search")

    filtered = recipes
    if diet_filter != "All":
        filtered = [r for r in filtered if r["diet"] == diet_filter]
    if source_filter != "All":
        filtered = [r for r in filtered if r["source_food"] == source_filter]
    if search:
        q = search.lower()
        filtered = [
            r for r in filtered
            if q in r["title"].lower() or q in r.get("ingredients", "").lower()
        ]

    st.caption(f"Showing {len(filtered)} of {len(recipes)} saved recipes")

    # ── Recipe cards ─────────────────────────────────
    for i, r in enumerate(filtered):
        with st.expander(f"🍳 {r['title']}", expanded=False):
            top1, top2 = st.columns([3, 1])

            with top1:
                st.markdown(f"**Ingredients:**\n{r['ingredients']}")
                st.markdown(f"**Instructions:**\n{r['instructions']}")
                if r["source_food"]:
                    st.caption(f"🔗 From: {r['source_food']}  •  🥗 {r['diet']}")
                st.caption(f"📅 Saved: {r['saved_at'][:10]}")

            with top2:
                st.metric("Calories", f"{r['calories']} kcal")
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Carbs", f"{r['carbs']}g")
                mc2.metric("Protein", f"{r['protein']}g")
                mc3.metric("Fat", f"{r['fat']}g")

                # Macro donut
                if r["carbs"] or r["protein"] or r["fat"]:
                    fig = go.Figure(data=[go.Pie(
                        labels=["Carbs", "Protein", "Fat"],
                        values=[r["carbs"], r["protein"], r["fat"]],
                        hole=0.55,
                        marker_colors=["#FFABAB", "#85E3FF", "#B9FBC0"],
                        textinfo="percent",
                    )])
                    fig.update_layout(
                        height=150, showlegend=False,
                        margin=dict(t=0, b=0, l=0, r=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True,
                                   key=f"rc_pie_{r['id']}")

            if st.button("🗑️ Delete", key=f"rc_del_{r['id']}"):
                delete_recipe(r["id"], uid)
                st.rerun()
