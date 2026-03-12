import streamlit as st
import json
import re
import io

from core.database import add_food_log, get_last_food_log_id, add_micronutrient_log
from core.ai_engine import estimate_micronutrients
from core.fingerprint_engine import update_fingerprint

MEAL_OPTIONS = ["Breakfast 🍳", "Lunch 🥗", "Dinner 🍗", "Snack 🍎"]

# Quick macro database for common foods (per typical serving)
FOOD_KB = {
    "banana":       {"calories": 89, "carbs": 23, "protein": 1, "fat": 0},
    "apple":        {"calories": 95, "carbs": 25, "protein": 0, "fat": 0},
    "egg":          {"calories": 78, "carbs": 1, "protein": 6, "fat": 5},
    "boiled egg":   {"calories": 78, "carbs": 1, "protein": 6, "fat": 5},
    "rice":         {"calories": 206, "carbs": 45, "protein": 4, "fat": 0},
    "chicken":      {"calories": 165, "carbs": 0, "protein": 31, "fat": 4},
    "chicken breast":{"calories": 165, "carbs": 0, "protein": 31, "fat": 4},
    "bread":        {"calories": 79, "carbs": 15, "protein": 3, "fat": 1},
    "toast":        {"calories": 79, "carbs": 15, "protein": 3, "fat": 1},
    "milk":         {"calories": 122, "carbs": 10, "protein": 6, "fat": 7},
    "oatmeal":      {"calories": 150, "carbs": 27, "protein": 5, "fat": 3},
    "yogurt":       {"calories": 100, "carbs": 17, "protein": 6, "fat": 1},
    "salmon":       {"calories": 208, "carbs": 0, "protein": 20, "fat": 13},
    "pasta":        {"calories": 220, "carbs": 43, "protein": 8, "fat": 1},
    "orange":       {"calories": 62, "carbs": 15, "protein": 1, "fat": 0},
    "avocado":      {"calories": 240, "carbs": 12, "protein": 3, "fat": 22},
    "cheese":       {"calories": 113, "carbs": 0, "protein": 7, "fat": 9},
    "peanut butter":{"calories": 188, "carbs": 6, "protein": 8, "fat": 16},
    "almonds":      {"calories": 164, "carbs": 6, "protein": 6, "fat": 14},
    "salad":        {"calories": 65, "carbs": 7, "protein": 3, "fat": 3},
    "pizza":        {"calories": 285, "carbs": 36, "protein": 12, "fat": 10},
    "burger":       {"calories": 354, "carbs": 29, "protein": 20, "fat": 17},
    "sandwich":     {"calories": 250, "carbs": 30, "protein": 12, "fat": 8},
    "steak":        {"calories": 271, "carbs": 0, "protein": 26, "fat": 18},
    "soup":         {"calories": 100, "carbs": 12, "protein": 4, "fat": 3},
    "smoothie":     {"calories": 180, "carbs": 35, "protein": 5, "fat": 2},
    "coffee":       {"calories": 5, "carbs": 0, "protein": 0, "fat": 0},
    "tea":          {"calories": 2, "carbs": 0, "protein": 0, "fat": 0},
    "juice":        {"calories": 110, "carbs": 26, "protein": 1, "fat": 0},
    "roti":         {"calories": 120, "carbs": 20, "protein": 3, "fat": 3},
    "chapati":      {"calories": 120, "carbs": 20, "protein": 3, "fat": 3},
    "dal":          {"calories": 150, "carbs": 20, "protein": 9, "fat": 3},
    "paneer":       {"calories": 265, "carbs": 4, "protein": 18, "fat": 20},
    "biryani":      {"calories": 350, "carbs": 45, "protein": 15, "fat": 12},
    "dosa":         {"calories": 133, "carbs": 19, "protein": 4, "fat": 5},
    "idli":         {"calories": 39, "carbs": 8, "protein": 1, "fat": 0},
    "paratha":      {"calories": 200, "carbs": 28, "protein": 4, "fat": 8},
    "naan":         {"calories": 262, "carbs": 45, "protein": 9, "fat": 5},
    "tofu":         {"calories": 144, "carbs": 3, "protein": 15, "fat": 8},
    "fish":         {"calories": 136, "carbs": 0, "protein": 20, "fat": 6},
    "shrimp":       {"calories": 85, "carbs": 0, "protein": 20, "fat": 1},
    "potato":       {"calories": 161, "carbs": 37, "protein": 4, "fat": 0},
    "sweet potato": {"calories": 103, "carbs": 24, "protein": 2, "fat": 0},
    "corn":         {"calories": 96, "carbs": 21, "protein": 3, "fat": 1},
    "broccoli":     {"calories": 55, "carbs": 11, "protein": 4, "fat": 1},
    "beans":        {"calories": 130, "carbs": 24, "protein": 8, "fat": 0},
    "lentils":      {"calories": 230, "carbs": 40, "protein": 18, "fat": 1},
    "mango":        {"calories": 99, "carbs": 25, "protein": 1, "fat": 1},
    "grapes":       {"calories": 69, "carbs": 18, "protein": 1, "fat": 0},
    "watermelon":   {"calories": 46, "carbs": 12, "protein": 1, "fat": 0},
    "pineapple":    {"calories": 82, "carbs": 22, "protein": 1, "fat": 0},
    "strawberry":   {"calories": 49, "carbs": 12, "protein": 1, "fat": 0},
    "protein shake": {"calories": 200, "carbs": 10, "protein": 30, "fat": 5},
    "protein bar":  {"calories": 220, "carbs": 25, "protein": 20, "fat": 8},
    "chocolate":    {"calories": 210, "carbs": 24, "protein": 3, "fat": 13},
    "ice cream":    {"calories": 207, "carbs": 24, "protein": 4, "fat": 11},
    "cookie":       {"calories": 150, "carbs": 20, "protein": 2, "fat": 7},
    "cake":         {"calories": 257, "carbs": 35, "protein": 3, "fat": 12},
    "donut":        {"calories": 252, "carbs": 31, "protein": 3, "fat": 14},
    "chips":        {"calories": 152, "carbs": 15, "protein": 2, "fat": 10},
    "popcorn":      {"calories": 93, "carbs": 19, "protein": 3, "fat": 1},
    "granola":      {"calories": 200, "carbs": 30, "protein": 5, "fat": 8},
    "cereal":       {"calories": 150, "carbs": 33, "protein": 3, "fat": 1},
    "pancake":      {"calories": 175, "carbs": 22, "protein": 5, "fat": 7},
    "waffle":       {"calories": 218, "carbs": 25, "protein": 6, "fat": 11},
    "french fries": {"calories": 312, "carbs": 41, "protein": 3, "fat": 15},
    "fried rice":   {"calories": 238, "carbs": 30, "protein": 5, "fat": 11},
    "noodles":      {"calories": 219, "carbs": 40, "protein": 7, "fat": 3},
}

# Quantity multiplier patterns
QTY_PATTERNS = [
    (r"(\d+)\s*(?:piece|pcs|pc|slice)", "pieces"),
    (r"(\d+)\s*(?:bowl|cup)s?", "bowls"),
    (r"(\d+)\s*(?:plate|serving)s?", "plates"),
    (r"(\d+)\s*(?:glass|glasses)", "glasses"),
    (r"(\d+)\s*(?:g|grams?)", "grams"),
    (r"half|½", "half"),
    (r"double|two|2x", "double"),
    (r"triple|three|3x", "triple"),
]


def _parse_text_input(text: str) -> list[dict]:
    """Parse conversational text into a list of food items with quantities."""
    items = []

    # Split on common separators: "and", commas, semicolons, newlines, "then", "also", "plus"
    parts = re.split(r'\band\b|,|;|\n|\bthen\b|\balso\b|\bplus\b|\bwith\b', text, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if not part or len(part) < 2:
            continue

        # Determine quantity multiplier
        multiplier = 1.0
        for pattern, qty_type in QTY_PATTERNS:
            match = re.search(pattern, part, re.IGNORECASE)
            if match:
                if qty_type == "half":
                    multiplier = 0.5
                elif qty_type == "double":
                    multiplier = 2.0
                elif qty_type == "triple":
                    multiplier = 3.0
                elif qty_type == "grams":
                    grams = int(match.group(1))
                    multiplier = grams / 100  # normalize to per-100g
                elif qty_type in ("pieces", "bowls", "plates", "glasses"):
                    multiplier = float(match.group(1))
                break

        # Clean food name - remove quantity descriptors
        food_name = re.sub(
            r'\d+\s*(?:piece|pcs|pc|slice|bowl|cup|plate|serving|glass|glasses|g|grams?)\s*(?:of\s*)?',
            '', part, flags=re.IGNORECASE
        ).strip()
        food_name = re.sub(r'^(?:had|ate|eaten|i\s+had|i\s+ate|i\s+eaten|a|an|some|the)\s+', '', food_name, flags=re.IGNORECASE).strip()
        food_name = re.sub(r'\b(?:half|double|triple|two|three|2x|3x|½)\s*', '', food_name, flags=re.IGNORECASE).strip()

        if not food_name or len(food_name) < 2:
            continue

        # Lookup nutrition
        lookup_key = food_name.lower().strip()
        matched = None
        for key in FOOD_KB:
            if key in lookup_key or lookup_key in key:
                matched = FOOD_KB[key]
                break

        if matched:
            items.append({
                "name": food_name.title(),
                "calories": int(matched["calories"] * multiplier),
                "carbs": int(matched["carbs"] * multiplier),
                "protein": int(matched["protein"] * multiplier),
                "fat": int(matched["fat"] * multiplier),
                "multiplier": multiplier,
                "matched": True,
            })
        else:
            # Estimate ~150 kcal per unknown item per serving
            est_cal = int(150 * multiplier)
            items.append({
                "name": food_name.title(),
                "calories": est_cal,
                "carbs": int(20 * multiplier),
                "protein": int(5 * multiplier),
                "fat": int(5 * multiplier),
                "multiplier": multiplier,
                "matched": False,
            })

    return items


def _try_ai_parse(text: str) -> list[dict] | None:
    """Use Gemini to parse food text into structured items (when available)."""
    if not st.session_state.get("api_key") or not st.session_state.get("active_model"):
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        prompt = f"""
        Parse this food description into individual food items with nutritional estimates.
        Input: "{text}"
        Return raw JSON ONLY — a list of objects. Each object must have:
        "name" (string), "calories" (int), "carbs" (int), "protein" (int), "fat" (int).
        Do your best to estimate realistic nutrition values for each item.
        """
        response = model.generate_content(prompt)
        resp_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(resp_text)
    except Exception:
        return None


def _transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to text using SpeechRecognition + Google."""
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""


def render_voice_logger():
    uid = st.session_state["user_id"]

    st.markdown(
        "<h2 style='color:#00E676;'>🎙️ Voice & Conversational Food Logger</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Speak or type what you ate. Log multiple foods at once!")
    st.write("---")

    tab_voice, tab_examples = st.tabs(["🗣️ Log Food", "📋 Examples"])

    with tab_voice:
        meal = st.selectbox("Meal", MEAL_OPTIONS, key="voice_meal")

        use_ai = st.toggle(
            "Use AI for better parsing",
            value=bool(st.session_state.get("active_model")),
            disabled=not bool(st.session_state.get("active_model")),
        )

        # ── INPUT MODE: Microphone or Text ──────────────
        st.markdown("### Tell me what you ate")
        input_mode = st.radio(
            "Input method:", ["🎤 Microphone", "⌨️ Type it"],
            horizontal=True, label_visibility="collapsed",
        )

        food_text = ""

        if input_mode == "🎤 Microphone":
            st.info("🎤 Click the microphone below and describe what you ate.")
            audio_data = st.audio_input("Tap to record", key="voice_mic_input")

            if audio_data is not None:
                audio_bytes = audio_data.getvalue()
                with st.spinner("🔊 Transcribing your voice..."):
                    transcript = _transcribe_audio(audio_bytes)

                if transcript:
                    st.success(f"**Heard:** {transcript}")
                    food_text = transcript
                    # Store in session so it survives reruns
                    st.session_state["voice_transcript"] = transcript
                else:
                    st.warning("Couldn't understand the audio. Please try again or switch to typing.")

            # Use stored transcript if available
            if not food_text and "voice_transcript" in st.session_state:
                food_text = st.session_state["voice_transcript"]
                if food_text:
                    st.caption(f"📝 Using previous transcript: *{food_text}*")
        else:
            food_text = st.text_area(
                "Describe your food",
                placeholder="e.g. I had 2 eggs, a banana, and a bowl of oatmeal with milk",
                height=100,
                label_visibility="collapsed",
            )

        if st.button("🔍 Parse & Preview", use_container_width=True) and food_text.strip():
            with st.spinner("Parsing your food..."):
                if use_ai:
                    ai_items = _try_ai_parse(food_text)
                    if ai_items:
                        st.session_state["voice_parsed"] = ai_items
                    else:
                        st.session_state["voice_parsed"] = _parse_text_input(food_text)
                else:
                    st.session_state["voice_parsed"] = _parse_text_input(food_text)

        # Show parsed results for confirmation
        if "voice_parsed" in st.session_state and st.session_state["voice_parsed"]:
            items = st.session_state["voice_parsed"]

            st.write("---")
            st.markdown("### 📋 Parsed Items — Review & Edit")

            total_cals = 0
            edited_items = []

            for i, item in enumerate(items):
                with st.expander(
                    f"{'✅' if item.get('matched', True) else '⚠️'} {item['name']} — {item['calories']} kcal",
                    expanded=True,
                ):
                    ec1, ec2, ec3, ec4, ec5 = st.columns(5)
                    name = ec1.text_input("Name", item["name"], key=f"vn_{i}")
                    cals = ec2.number_input("Calories", 0, 5000, item["calories"], key=f"vc_{i}")
                    carbs = ec3.number_input("Carbs (g)", 0, 500, item["carbs"], key=f"vca_{i}")
                    protein = ec4.number_input("Protein (g)", 0, 300, item["protein"], key=f"vp_{i}")
                    fat = ec5.number_input("Fat (g)", 0, 300, item["fat"], key=f"vf_{i}")

                    if not item.get("matched", True):
                        st.caption("⚠️ Food not in database — values are estimated. Please verify.")

                    edited_items.append({
                        "name": name, "calories": cals, "carbs": carbs,
                        "protein": protein, "fat": fat,
                    })
                    total_cals += cals

            # Summary
            st.markdown(
                f"<div style='text-align:center; padding:15px; background:#1e1e1e; "
                f"border-radius:12px; border:1px solid #00E676; margin:10px 0;'>"
                f"<h3 style='color:#00E676; margin:0;'>"
                f"Total: {len(edited_items)} items — {total_cals} kcal</h3>"
                f"</div>",
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            if c1.button("✅ Log All Items", use_container_width=True, type="primary"):
                for item in edited_items:
                    add_food_log(
                        uid, item["name"], item["calories"],
                        item["carbs"], item["protein"], item["fat"], meal,
                    )
                    # Also log micronutrients
                    food_log_id = get_last_food_log_id(uid)
                    micros = estimate_micronutrients(item["name"], item["calories"])
                    if food_log_id:
                        add_micronutrient_log(
                            uid, food_log_id,
                            micros["iron"], micros["calcium"], micros["vitamin_c"],
                            micros["vitamin_d"], micros["fiber"], micros["sodium"],
                            micros["sugar"],
                        )
                update_fingerprint(uid)
                st.success(f"Logged **{len(edited_items)} items** ({total_cals} kcal) to {meal}! 🎉")
                del st.session_state["voice_parsed"]
                st.rerun()

            if c2.button("🗑️ Clear", use_container_width=True):
                del st.session_state["voice_parsed"]
                st.rerun()

    with tab_examples:
        st.markdown("### How to describe your food")
        st.markdown("""
        **Simple list:**
        > I had 2 eggs, toast, and a banana

        **With quantities:**
        > 3 slices of bread with peanut butter and a glass of milk

        **Descriptive:**
        > Had a bowl of oatmeal, then a chicken sandwich for lunch, also some grapes

        **Multiple meals:**
        > Rice with dal and 2 roti, also had yogurt and an apple

        **Partial servings:**
        > Half an avocado, double portion of pasta, and a salad
        """)

        st.info(
            "💡 **Tips:**\n"
            "- Use the **🎤 Microphone** button to speak what you ate\n"
            "- Use 'and', commas, 'then', 'also', 'plus' to separate items\n"
            "- Specify quantities like '2 eggs', '3 slices', 'half avocado'\n"
            "- Enable AI parsing for better accuracy with complex descriptions\n"
            "- You can edit any parsed values before logging"
        )
