import streamlit as st
import plotly.graph_objects as go
from gtts import gTTS
from io import BytesIO
from PIL import Image

from core.ai_engine import (
    analyze_image,
    get_recipes,
    analyze_fridge,
    get_recipes_from_ingredients,
)
from core.barcode import lookup_barcode
from core.database import add_food_log, save_recipe, get_last_food_log_id, add_micronutrient_log
from core.fingerprint_engine import update_fingerprint
from core.ai_engine import estimate_micronutrients


# ───────────────────────────────────────────────────────
def render_scanner():
    tab_food, tab_barcode, tab_fridge = st.tabs(
        ["🍔 Food Scanner", "📶 Barcode Scanner", "🧳 Fridge Scanner"]
    )

    with tab_food:
        _food_scanner()

    with tab_barcode:
        _barcode_scanner()

    with tab_fridge:
        _fridge_scanner()


# ─── FOOD SCANNER ─────────────────────────────────────
def _food_scanner():
    c1, c2 = st.columns([1, 1.5])

    with c1:
        st.markdown("### 📸 Snap or Upload Food")
        src = st.radio(
            "Source",
            ["Upload 📁", "Camera 📷"],
            horizontal=True,
            label_visibility="collapsed",
            key="food_src",
        )
        img_file = (
            st.file_uploader("File", type=["jpg", "png"], key="food_upload")
            if "Upload" in src
            else st.camera_input("Snap", key="food_cam")
        )

        if img_file:
            img = Image.open(img_file)
            st.image(img, use_container_width=True)
            if st.button("🔍 IDENTIFY FOOD", key="btn_identify"):
                if not st.session_state.get("active_model"):
                    st.error("AI not connected — add GEMINI_API_KEY to your .env file.")
                else:
                    with st.spinner("AI is analysing... 🧠"):
                        res = analyze_image(img)
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.session_state["scan_data"] = res
                            st.session_state["recipe_result"] = None
                            st.rerun()

        # AI Chef section
        if st.session_state.get("scan_data"):
            st.write("---")
            st.markdown("### 👨‍🍳 AI Chef")
            st.caption(f"Based on **{st.session_state.get('user_diet', 'Balanced')}** diet")

            if st.button("✨ Generate Recipes", key="btn_food_recipes"):
                with st.spinner("Cooking up ideas..."):
                    recipes = get_recipes(
                        st.session_state["scan_data"]["name"],
                        st.session_state.get("user_diet", "Balanced"),
                    )
                    st.session_state["recipe_result"] = recipes

            if st.session_state.get("recipe_result"):
                _render_recipe_cards(
                    st.session_state["recipe_result"],
                    st.session_state["scan_data"].get("name", ""),
                    key_prefix="food",
                )

    # Nutrition results panel
    with c2:
        if st.session_state.get("scan_data"):
            d = st.session_state["scan_data"]
            _show_nutrition_panel(d)


# ─── BARCODE SCANNER ──────────────────────────────────
def _barcode_scanner():
    st.markdown("### 📶 Barcode Lookup")
    st.caption("Enter a barcode number to instantly fetch nutrition data from OpenFoodFacts.")

    bc1, bc2 = st.columns([2, 1])
    barcode = bc1.text_input(
        "Barcode", placeholder="e.g. 5449000000996", key="barcode_input"
    )
    bc2.write("")  # spacing
    search = bc2.button("🔍 Look Up", key="btn_barcode_search")

    if search and barcode:
        with st.spinner("Fetching product info..."):
            result = lookup_barcode(barcode)
            if result:
                st.session_state["barcode_result"] = result
            else:
                st.error("Product not found. Check the barcode and try again.")
                st.session_state["barcode_result"] = None

    product = st.session_state.get("barcode_result")
    if not product:
        return

    # ── Product info ────────────────────────────────
    st.write("---")
    p1, p2 = st.columns([1, 2])

    with p1:
        if product["image_url"]:
            st.image(product["image_url"], width=180)
        st.markdown(
            f"<div class='glass-card' style='padding:12px'>"
            f"<h3 style='color:#00E676;margin:0'>{product['name']}</h3>"
            f"<p style='color:#aaa;margin:4px 0'>{product['brand']}</p>"
            f"<code>{product['barcode']}</code></div>",
            unsafe_allow_html=True,
        )

    with p2:
        st.markdown("### 🧮 Portion Calculator")
        unit = st.radio("Unit", ["g", "serving"], horizontal=True, key="bc_unit")
        if unit == "g":
            qty = st.slider("Amount (g)", 1, 1000, 100, key="bc_qty")
            factor = qty / 100
        else:
            servings = st.slider("Servings", 1, 10, 1, key="bc_servings")
            factor = (product["serving_g"] / 100) * servings
            st.caption(f"1 serving ≈ {product['serving_g']}g")

        cals = int(product["calories_100g"] * factor)
        carbs = int(product["carbs_100g"] * factor)
        prot = int(product["protein_100g"] * factor)
        fat_val = int(product["fat_100g"] * factor)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔥 Calories", f"{cals}")
        m2.metric("🍞 Carbs", f"{carbs}g")
        m3.metric("💪 Protein", f"{prot}g")
        m4.metric("🧈 Fat", f"{fat_val}g")

        # Macro pie
        if carbs or prot or fat_val:
            fig = go.Figure(data=[go.Pie(
                labels=["Carbs", "Protein", "Fat"],
                values=[carbs, prot, fat_val],
                hole=0.6,
                marker_colors=["#FFABAB", "#85E3FF", "#B9FBC0"],
            )])
            fig.update_layout(
                height=200, showlegend=True,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
            )
            st.plotly_chart(fig, use_container_width=True, key="bc_macro_pie")

        # Auto-log
        meal = st.selectbox(
            "Meal", ["Breakfast 🍳", "Lunch 🥗", "Dinner 🍗", "Snack 🍎"],
            key="bc_meal",
        )
        if st.button("➕ Add to Diary", key="btn_bc_log"):
            uid = st.session_state["user_id"]
            add_food_log(
                user_id=uid,
                name=product["name"],
                calories=cals,
                carbs=carbs,
                protein=prot,
                fat=fat_val,
                meal=meal,
            )
            fid = get_last_food_log_id(uid)
            if fid:
                micros = estimate_micronutrients(product["name"], cals)
                add_micronutrient_log(uid, fid, **micros)
            update_fingerprint(uid)
            st.balloons()
            st.success(f"✅ Logged **{product['name']}** — {cals} kcal")


# ─── FRIDGE SCANNER ───────────────────────────────────
def _fridge_scanner():
    st.markdown("### 🧊 What's In Your Fridge?")
    st.caption("Upload a photo of your fridge or pantry and get recipe ideas!")

    src = st.radio(
        "Source",
        ["Upload 📁", "Camera 📷"],
        horizontal=True,
        label_visibility="collapsed",
        key="fridge_src",
    )
    img_file = (
        st.file_uploader("Fridge photo", type=["jpg", "png"], key="fridge_upload")
        if "Upload" in src
        else st.camera_input("Snap", key="fridge_cam")
    )

    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True, caption="Your fridge")

        if st.button("🔎 Identify Ingredients", key="btn_fridge_scan"):
            if not st.session_state.get("active_model"):
                st.error("AI not connected — add GEMINI_API_KEY to your .env file.")
            else:
                with st.spinner("Scanning fridge... 🔍"):
                    items = analyze_fridge(img)
                    if items and "error" in items[0]:
                        st.error(items[0]["error"])
                    else:
                        st.session_state["fridge_items"] = items
                        st.session_state["fridge_recipes"] = None
                        st.rerun()

    if st.session_state.get("fridge_items"):
        items = st.session_state["fridge_items"]
        st.markdown("#### 🥬 Detected Ingredients")
        cols = st.columns(min(len(items), 4))
        for i, item in enumerate(items):
            with cols[i % len(cols)]:
                cat_emoji = {
                    "vegetable": "🥦", "fruit": "🍎", "dairy": "🧀",
                    "meat": "🥩", "grain": "🌾", "condiment": "🧂",
                }.get(item.get("category", "").lower(), "📦")
                st.markdown(
                    f"<div class='glass-card' style='text-align:center;padding:8px'>"
                    f"<b>{cat_emoji} {item['name']}</b></div>",
                    unsafe_allow_html=True,
                )

        if st.button("🍳 Generate Recipes From These", key="btn_fridge_recipes"):
            with st.spinner("Chef is thinking... 👨‍🍳"):
                names = [it["name"] for it in items]
                recipes = get_recipes_from_ingredients(
                    names, st.session_state.get("user_diet", "Balanced")
                )
                st.session_state["fridge_recipes"] = recipes

        if st.session_state.get("fridge_recipes"):
            _render_recipe_cards(
                st.session_state["fridge_recipes"],
                "fridge items",
                key_prefix="fridge",
            )


# ─── SHARED HELPERS ───────────────────────────────────
def _show_nutrition_panel(d: dict):
    """Render the nutrition detail panel for a scanned food."""
    st.markdown(
        f"""
        <div class="glass-card">
            <h1 style="color:#00E676; margin:0;">{d['name']}</h1>
            <p>{d.get('desc', '')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Text-to-speech
    tts = gTTS(f"{d['name']}. {d.get('desc', '')}")
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.audio(fp, format="audio/mp3")

    with st.expander("ℹ️ Nutritional Details", expanded=True):
        k1, k2 = st.columns(2)
        k1.success(f"**Benefits:**\n{d.get('benefits', 'N/A')}")
        k2.error(f"**Risks:**\n{d.get('harm', 'N/A')}")

    st.markdown("### 🧮 Calculator")
    u1, u2 = st.columns([1, 2])
    unit = u1.radio("Unit", ["g", "kg"], key="scan_unit")
    qty = u2.slider("Amount", 0, 1000, 100 if unit == "g" else 1, key="scan_qty")

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
    st.plotly_chart(fig, use_container_width=True, key="scan_macro_pie")

    # Auto-log to diary
    meal = st.selectbox(
        "Meal", ["Breakfast 🍳", "Lunch 🥗", "Dinner 🍗", "Snack 🍎"],
        key="scan_meal",
    )
    if st.button("➕ Add to Diary", key="btn_add_diary"):
        uid = st.session_state["user_id"]
        add_food_log(
            user_id=uid,
            name=d["name"],
            calories=rcals,
            carbs=int(d["carbs"] * factor),
            protein=int(d["prot"] * factor),
            fat=int(d["fat"] * factor),
            meal=meal,
        )
        fid = get_last_food_log_id(uid)
        if fid:
            micros = estimate_micronutrients(d["name"], rcals)
            add_micronutrient_log(uid, fid, **micros)
        update_fingerprint(uid)
        st.balloons()
        st.success("Logged! 📝")


def _render_recipe_cards(recipes: list[dict], source_food: str,
                         key_prefix: str = "r"):
    """Display recipe cards with Save buttons."""
    if not recipes:
        st.warning("No recipes generated — try again.")
        return

    st.markdown("---")
    st.markdown("### 🍽️ Recipe Suggestions")

    for i, r in enumerate(recipes):
        with st.expander(f"🍳 {r.get('title', f'Recipe {i+1}')}", expanded=(i == 0)):
            rc1, rc2 = st.columns([2, 1])
            with rc1:
                st.markdown(f"**Ingredients:**\n{r.get('ingredients', 'N/A')}")
                st.markdown(f"**Instructions:**\n{r.get('instructions', 'N/A')}")
            with rc2:
                st.metric("Calories", f"{r.get('calories', 0)} kcal")
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Carbs", f"{r.get('carbs', 0)}g")
                mc2.metric("Protein", f"{r.get('protein', 0)}g")
                mc3.metric("Fat", f"{r.get('fat', 0)}g")

            if st.button(f"💾 Save Recipe", key=f"{key_prefix}_save_{i}"):
                uid = st.session_state["user_id"]
                save_recipe(
                    user_id=uid,
                    title=r.get("title", f"Recipe {i+1}"),
                    ingredients=r.get("ingredients", ""),
                    instructions=r.get("instructions", ""),
                    calories=r.get("calories", 0),
                    carbs=r.get("carbs", 0),
                    protein=r.get("protein", 0),
                    fat=r.get("fat", 0),
                    diet=st.session_state.get("user_diet", "Balanced"),
                    source_food=source_food,
                )
                st.success(f"✅ Saved **{r.get('title', 'Recipe')}** to Recipe Corner!")
