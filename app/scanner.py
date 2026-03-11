import streamlit as st
import plotly.graph_objects as go
from gtts import gTTS
from io import BytesIO
from PIL import Image
import datetime

from core.ai_engine import analyze_image, get_recipes


def render_scanner():
    c1, c2 = st.columns([1, 1.5])

    with c1:
        st.markdown("### 📸 Input")
        src = st.radio(
            "Source",
            ["Upload 📁", "Camera 📷"],
            horizontal=True,
            label_visibility="collapsed",
        )
        img_file = (
            st.file_uploader("File", type=["jpg", "png"])
            if "Upload" in src
            else st.camera_input("Snap")
        )

        if img_file:
            img = Image.open(img_file)
            st.image(img, use_container_width=True)
            if st.button("🔍 IDENTIFY FOOD"):
                if not st.session_state["active_model"]:
                    st.error("Link Key in Sidebar!")
                else:
                    with st.spinner("AI is thinking... 🧠"):
                        res = analyze_image(img)
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.session_state["scan_data"] = res
                            st.session_state["recipe_result"] = None
                            st.rerun()

        # --- AI CHEF ---
        if st.session_state["scan_data"]:
            st.write("---")
            st.markdown("### 👨‍🍳 AI Chef")
            st.caption(f"Based on **{st.session_state['user_diet']}** diet")

            if st.button("✨ Generate Recipes"):
                with st.spinner("Cooking up ideas..."):
                    st.session_state["recipe_result"] = get_recipes(
                        st.session_state["scan_data"]["name"],
                        st.session_state["user_diet"],
                    )

            if st.session_state["recipe_result"]:
                st.info(st.session_state["recipe_result"])

    # --- NUTRITION RESULTS ---
    with c2:
        if st.session_state["scan_data"]:
            d = st.session_state["scan_data"]

            st.markdown(
                f"""
                <div class="glass-card">
                    <h1 style="color:#00E676; margin:0;">{d['name']}</h1>
                    <p>{d['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            tts = gTTS(f"{d['name']}. {d['desc']}")
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            st.audio(fp, format="audio/mp3")

            with st.expander("ℹ️ Nutritional Details", expanded=True):
                k1, k2 = st.columns(2)
                k1.success(f"**Benefits:**\n{d['benefits']}")
                k2.error(f"**Risks:**\n{d['harm']}")

            st.markdown("### 🧮 Calculator")
            u1, u2 = st.columns([1, 2])
            unit = u1.radio("Unit", ["g", "kg"])
            qty = u2.slider("Amount", 0, 1000, 100 if unit == "g" else 1)

            factor = qty / 100 if unit == "g" else qty * 10
            rcals = int(d["cals"] * factor)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Energy 🔥", f"{rcals}")
            m2.metric("Walk 🚶", f"{int(rcals / 4)}m")
            m3.metric("Run 🏃", f"{int(rcals / 11)}m")
            m4.metric("Bike 🚴", f"{int(rcals / 9)}m")

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Carbs", "Protein", "Fat"],
                        values=[d["carbs"], d["prot"], d["fat"]],
                        hole=0.6,
                        marker_colors=["#FFABAB", "#85E3FF", "#B9FBC0"],
                    )
                ]
            )
            fig.update_layout(
                height=250,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            meal = st.selectbox(
                "Meal", ["Breakfast 🍳", "Lunch 🥗", "Dinner 🍗", "Snack 🍎"]
            )
            if st.button("➕ Add to Diary"):
                st.session_state["food_log"].append(
                    {
                        "name": d["name"],
                        "cals": rcals,
                        "carbs": int(d["carbs"] * factor),
                        "prot": int(d["prot"] * factor),
                        "fat": int(d["fat"] * factor),
                        "meal": meal,
                        "time": datetime.datetime.now().strftime("%H:%M"),
                    }
                )
                st.balloons()
                st.success("Logged! 📝")
