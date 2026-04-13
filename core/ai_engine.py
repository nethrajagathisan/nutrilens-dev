import streamlit as st
import google.generativeai as genai
import json
import re


# ─── MICRONUTRIENT ESTIMATION ──────────────────────────

MICRO_DB = {
    "banana":       {"iron": 0.3, "calcium": 5, "vitamin_c": 8.7, "vitamin_d": 0, "fiber": 2.6, "sodium": 1, "sugar": 12},
    "egg":          {"iron": 1.2, "calcium": 28, "vitamin_c": 0, "vitamin_d": 1.1, "fiber": 0, "sodium": 62, "sugar": 0.6},
    "boiled egg":   {"iron": 1.2, "calcium": 28, "vitamin_c": 0, "vitamin_d": 1.1, "fiber": 0, "sodium": 62, "sugar": 0.6},
    "rice":         {"iron": 0.2, "calcium": 10, "vitamin_c": 0, "vitamin_d": 0, "fiber": 0.4, "sodium": 1, "sugar": 0},
    "milk":         {"iron": 0.1, "calcium": 125, "vitamin_c": 0, "vitamin_d": 1.2, "fiber": 0, "sodium": 44, "sugar": 5},
    "bread":        {"iron": 1.2, "calcium": 73, "vitamin_c": 0, "vitamin_d": 0, "fiber": 1.3, "sodium": 132, "sugar": 1.5},
    "chicken":      {"iron": 1.0, "calcium": 15, "vitamin_c": 0, "vitamin_d": 0.1, "fiber": 0, "sodium": 74, "sugar": 0},
    "avocado":      {"iron": 0.6, "calcium": 12, "vitamin_c": 10, "vitamin_d": 0, "fiber": 6.7, "sodium": 7, "sugar": 0.7},
    "peanuts":      {"iron": 1.3, "calcium": 26, "vitamin_c": 0, "vitamin_d": 0, "fiber": 2.4, "sodium": 5, "sugar": 1.2},
    "apple":        {"iron": 0.1, "calcium": 6, "vitamin_c": 4.6, "vitamin_d": 0, "fiber": 2.4, "sodium": 1, "sugar": 10},
    "spinach":      {"iron": 2.7, "calcium": 99, "vitamin_c": 28, "vitamin_d": 0, "fiber": 2.2, "sodium": 79, "sugar": 0.4},
    "salmon":       {"iron": 0.3, "calcium": 9, "vitamin_c": 0, "vitamin_d": 11, "fiber": 0, "sodium": 59, "sugar": 0},
    "yogurt":       {"iron": 0.1, "calcium": 110, "vitamin_c": 0.5, "vitamin_d": 0.1, "fiber": 0, "sodium": 46, "sugar": 4.7},
    "orange":       {"iron": 0.1, "calcium": 40, "vitamin_c": 53, "vitamin_d": 0, "fiber": 2.4, "sodium": 0, "sugar": 9},
    "broccoli":     {"iron": 0.7, "calcium": 47, "vitamin_c": 89, "vitamin_d": 0, "fiber": 2.6, "sodium": 33, "sugar": 1.7},
    "potato":       {"iron": 0.8, "calcium": 12, "vitamin_c": 20, "vitamin_d": 0, "fiber": 2.2, "sodium": 6, "sugar": 0.8},
    "oatmeal":      {"iron": 1.7, "calcium": 21, "vitamin_c": 0, "vitamin_d": 0, "fiber": 4, "sodium": 2, "sugar": 0.5},
    "tofu":         {"iron": 2.7, "calcium": 350, "vitamin_c": 0.1, "vitamin_d": 0, "fiber": 0.3, "sodium": 7, "sugar": 0.6},
    "lentils":      {"iron": 3.3, "calcium": 19, "vitamin_c": 1.5, "vitamin_d": 0, "fiber": 7.9, "sodium": 2, "sugar": 1.8},
    "cheese":       {"iron": 0.7, "calcium": 721, "vitamin_c": 0, "vitamin_d": 0.6, "fiber": 0, "sodium": 621, "sugar": 0.5},
    "almond":       {"iron": 3.7, "calcium": 269, "vitamin_c": 0, "vitamin_d": 0, "fiber": 12.5, "sodium": 1, "sugar": 4.4},
    "beef":         {"iron": 2.6, "calcium": 18, "vitamin_c": 0, "vitamin_d": 0.1, "fiber": 0, "sodium": 66, "sugar": 0},
    "pasta":        {"iron": 1.3, "calcium": 7, "vitamin_c": 0, "vitamin_d": 0, "fiber": 1.8, "sodium": 1, "sugar": 0.6},
    "tomato":       {"iron": 0.3, "calcium": 10, "vitamin_c": 14, "vitamin_d": 0, "fiber": 1.2, "sodium": 5, "sugar": 2.6},
    "carrot":       {"iron": 0.3, "calcium": 33, "vitamin_c": 6, "vitamin_d": 0, "fiber": 2.8, "sodium": 69, "sugar": 4.7},
}

# Generic fallback based on calorie proportions
_GENERIC_PER_100KCAL = {
    "iron": 0.8, "calcium": 40, "vitamin_c": 5, "vitamin_d": 0.3,
    "fiber": 1.5, "sodium": 150, "sugar": 4,
}


def estimate_micronutrients(food_name: str, calories: int) -> dict:
    """Estimate micronutrients from food name and calories using lookup + fallback."""
    name_lower = food_name.lower().strip()

    # Try direct match or partial match
    match = None
    for key in MICRO_DB:
        if key in name_lower or name_lower in key:
            match = MICRO_DB[key]
            break

    if match:
        # Scale by approximate portion (assume DB values are per 100kcal-equivalent serving)
        scale = max(calories / 150, 0.3)  # rough scaling
        return {k: round(v * scale, 2) for k, v in match.items()}

    # Fallback: generic estimation based on calories
    scale = calories / 100
    return {k: round(v * scale, 2) for k, v in _GENERIC_PER_100KCAL.items()}


def connect_to_best_model(key: str) -> str | None:
    """Try Gemini models in priority order; return the best one that works."""
    try:
        genai.configure(api_key=key)

        candidates = [
            "gemini-3.0-pro",
            "gemini-3.0-flash",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]

        available_models = [
            m.name.replace("models/", "") for m in genai.list_models()
        ]

        selected = None
        for c in candidates:
            if any(c in m for m in available_models):
                selected = c
                break

        if not selected:
            selected = "gemini-1.5-flash"

        model = genai.GenerativeModel(selected)
        model.generate_content("test")
        return selected
    except Exception:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            model.generate_content("test")
            return "gemini-1.5-flash"
        except Exception:
            return None


def analyze_image(image):
    """Send a food image to Gemini and return structured nutrition JSON."""
    try:
        if not st.session_state.get("active_model"):
            return {"error": "AI not connected — add GEMINI_API_KEY to your .env file"}
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        prompt = """
        Analyze this food. Return raw JSON ONLY.
        Keys: "name", "cals" (int), "carbs" (float), "prot" (float), "fat" (float), 
        "desc" (fun summary), "benefits" (emoji bullet points), "harm" (emoji bullet points).
        """
        response = model.generate_content([prompt, image])
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}


def get_recipes(food: str, diet: str) -> list[dict]:
    """Generate 3 structured recipe suggestions with macro details."""
    try:
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        prompt = f"""
        Suggest 3 {diet} recipes using {food} as the main ingredient.
        Return raw JSON ONLY — a list of 3 objects. Each object must have:
        "title" (string), "ingredients" (string, bullet list with emoji),
        "instructions" (string, numbered steps with emoji),
        "calories" (int, per serving), "carbs" (int, grams),
        "protein" (int, grams), "fat" (int, grams).
        """
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return []


def analyze_fridge(image) -> list[dict]:
    """Send a fridge/pantry image to Gemini and identify available ingredients."""
    try:
        if not st.session_state.get("active_model"):
            return [{"error": "AI not connected — add GEMINI_API_KEY to your .env file"}]
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        prompt = """
        Look at this fridge or pantry image. Identify all visible food items.
        Return raw JSON ONLY — a list of objects, each with:
        "name" (string), "category" (string: vegetable/fruit/dairy/meat/grain/condiment/other).
        """
        response = model.generate_content([prompt, image])
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return [{"error": str(e)}]


def get_recipes_from_ingredients(ingredients: list[str], diet: str) -> list[dict]:
    """Generate 3 structured recipes from a list of available ingredients."""
    try:
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        items = ", ".join(ingredients)
        prompt = f"""
        I have these ingredients: {items}.
        Suggest 3 {diet} recipes I can make with them.
        Return raw JSON ONLY — a list of 3 objects. Each object must have:
        "title" (string), "ingredients" (string, bullet list with emoji),
        "instructions" (string, numbered steps with emoji),
        "calories" (int, per serving), "carbs" (int, grams),
        "protein" (int, grams), "fat" (int, grams).
        """
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return []


def chat_ai(query: str, context: str) -> str:
    """Send a chat message to Gemini with optional context."""
    try:
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        return model.generate_content(
            f"Context: {context}. User: {query}"
        ).text
    except Exception:
        return "Connection error."


def _extract_response_text(response) -> str | None:
    """Read text safely even when the SDK doesn't populate response.text."""
    try:
        text = getattr(response, "text", None)
        if text:
            return text.strip()
    except Exception:
        pass

    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        if content is None:
            continue
        parts = getattr(content, "parts", []) or []
        chunks = [getattr(part, "text", "") for part in parts if getattr(part, "text", "")]
        if chunks:
            return "".join(chunks).strip()
    return None


def _build_local_rag_fallback(query: str, user_context: str = "",
                              user_id: int | None = None) -> str:
    """Return a grounded local answer when the remote model is unavailable."""
    from core.rag_engine import build_user_log_context, retrieve

    docs = retrieve(query, top_k=4, user_id=user_id, user_context=user_context)
    if not docs or docs[0]["score"] <= 0:
        return (
            "I’m not sure based on the current verified fitness and nutrition knowledge base. "
            "Try a more specific nutrition or training question, or reconnect the AI model for a fuller answer."
        )

    highlights: list[str] = []
    for doc in docs:
        sentences = re.split(r"(?<=[.!?])\s+", doc["text"].strip())
        for sentence in sentences[:2]:
            if sentence:
                highlights.append(sentence)
            if len(highlights) >= 4:
                break
        if len(highlights) >= 4:
            break

    source_topics = ", ".join(dict.fromkeys(doc["topic"] for doc in docs))
    summary = " ".join(highlights[:4]).strip()
    recent_context = build_user_log_context(user_id, days=7) if user_id is not None else f"PERSONAL CONTEXT: {user_context}"
    prefix = (
        "I couldn’t reach the AI model, so here’s a grounded answer from the local verified coach knowledge base."
        if st.session_state.get("api_key") and st.session_state.get("active_model")
        else "AI is not connected, so here’s a grounded answer from the local verified coach knowledge base."
    )
    return f"{prefix} Relevant topics: {source_topics}. {summary}\n\n{recent_context}"


def chat_ai_rag(query: str, user_context: str, user_id: int | None = None) -> str:
    """RAG-powered fitness and nutrition coach."""
    if not st.session_state.get("api_key") or not st.session_state.get("active_model"):
        return _build_local_rag_fallback(query, user_context=user_context, user_id=user_id)

    try:
        from core.rag_engine import build_rag_context

        rag_ctx = build_rag_context(
            query,
            top_k=4,
            user_id=user_id,
            user_context=user_context,
            days=7,
        )
        prompt = (
            f"{rag_ctx}\n"
            f"USER QUESTION: {query}\n"
            "You are NutriLens' professional fitness and nutrition coach. Use ONLY the verified "
            "knowledge base context and the user's recent log data above. Provide evidence-based, "
            "personalized advice that is tailored to their diet, calorie goal, hydration, weight "
            "trend, and exercise pattern. If data is missing or the answer is not fully covered by "
            "the context, say so clearly and give cautious general guidance. Keep the answer concise, "
            "practical, and friendly with a few helpful emojis."
        )
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        response = model.generate_content(prompt)
        text = _extract_response_text(response)
        return text if text else _build_local_rag_fallback(query, user_context=user_context, user_id=user_id)
    except Exception:
        return _build_local_rag_fallback(query, user_context=user_context, user_id=user_id)
