import streamlit as st
import google.generativeai as genai
import json


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
        if not st.session_state["active_model"]:
            return {"error": "Link Key First 🔑"}
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


def get_recipes(food: str, diet: str) -> str:
    """Generate recipe suggestions for a given food and diet."""
    try:
        genai.configure(api_key=st.session_state["api_key"])
        model = genai.GenerativeModel(st.session_state["active_model"])
        response = model.generate_content(
            f"Suggest 3 yummy {diet} recipes using {food} as the main ingredient. "
            "Use emojis and keep it short."
        )
        return response.text
    except Exception:
        return "Chef is napping 😴"


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
