"""
RAG retrieval engine for the fitness and nutrition coach.

Primary retrieval uses a Chroma vector store with lightweight local embeddings,
then combines the retrieved evidence with the user's last 7 days of logs.
"""

import datetime
import hashlib
import math
import re
from collections import Counter

import chromadb

from core.database import (
    get_all_food_logs_range,
    get_daily_calorie_summary,
    get_daily_exercise_summary,
    get_daily_hydration_summary,
    get_exercise_logs_range,
    init_db,
    get_user_by_id,
    get_weight_history,
)
from core.nutrition_kb import KNOWLEDGE_BASE

EMBED_DIM = 384


def _normalize_token(token: str) -> str:
    """Light stemming so simple plural forms map to the same feature bucket."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us")):
        return token[:-1]
    return token


_STOP_WORDS = frozenset(
    _normalize_token(word) for word in {
        "the", "a", "an", "is", "it", "in", "on", "at", "to", "for", "of", "and",
        "or", "but", "with", "this", "that", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "not", "no", "so", "if", "as", "by",
        "from", "its", "their", "they", "we", "you", "your", "i", "my", "me",
        "he", "she", "his", "her", "our", "us", "them", "what", "which", "who",
        "when", "where", "how", "why", "about", "much", "many", "best", "daily",
        "day", "per", "need", "needs", "long", "term",
    }
)


def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split, and remove common stop words."""
    text = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = [_normalize_token(token) for token in text.split()]
    return [token for token in tokens if token and token not in _STOP_WORDS]


def _hash_bucket(token: str) -> tuple[int, float]:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % EMBED_DIM
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return index, sign


def embed_text(text: str) -> list[float]:
    """Create a deterministic dense embedding suitable for vector search."""
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * EMBED_DIM

    weighted = Counter(tokens)
    for i in range(len(tokens) - 1):
        weighted[f"{tokens[i]}_{tokens[i + 1]}"] += 1.35

    vector = [0.0] * EMBED_DIM
    for token, weight in weighted.items():
        index, sign = _hash_bucket(token)
        vector[index] += sign * float(weight)

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _build_collection():
    """Create an in-memory Chroma collection populated with coach documents."""
    client = chromadb.Client()
    try:
        client.delete_collection("fitness_nutrition_kb")
    except Exception:
        pass
    collection = client.create_collection(
        name="fitness_nutrition_kb",
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=[doc["id"] for doc in KNOWLEDGE_BASE],
        documents=[f"Topic: {doc['topic']}\n{doc['text']}" for doc in KNOWLEDGE_BASE],
        metadatas=[{"topic": doc["topic"], "id": doc["id"]} for doc in KNOWLEDGE_BASE],
        embeddings=[embed_text(f"{doc['topic']} {doc['topic']} {doc['text']}") for doc in KNOWLEDGE_BASE],
    )
    return collection


def get_user_log_snapshot(user_id: int, days: int = 7) -> dict:
    """Return a structured summary of the user's recent nutrition and fitness logs."""
    init_db()
    user = get_user_by_id(user_id) or {}
    calorie_rows = get_daily_calorie_summary(user_id, days)
    hydration_rows = get_daily_hydration_summary(user_id, days)
    exercise_rows = get_daily_exercise_summary(user_id, days)
    exercise_logs = get_exercise_logs_range(user_id, days)
    food_logs = get_all_food_logs_range(user_id, days)

    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    recent_weights = [
        row for row in get_weight_history(user_id)
        if row["logged_at"][:10] >= cutoff
    ]

    calorie_days = max(len(calorie_rows), 1)
    hydration_days = max(len(hydration_rows), 1)
    avg_calories = sum(row["total_cals"] for row in calorie_rows) / calorie_days if calorie_rows else 0.0
    avg_protein = sum(row["total_protein"] for row in calorie_rows) / calorie_days if calorie_rows else 0.0
    avg_carbs = sum(row["total_carbs"] for row in calorie_rows) / calorie_days if calorie_rows else 0.0
    avg_fat = sum(row["total_fat"] for row in calorie_rows) / calorie_days if calorie_rows else 0.0
    avg_hydration_ml = sum(row["total_ml"] for row in hydration_rows) / hydration_days if hydration_rows else 0.0
    total_exercise_minutes = sum(row["total_minutes"] for row in exercise_rows)
    total_exercise_burned = sum(row["total_burned"] for row in exercise_rows)
    exercise_types = list(dict.fromkeys(log["activity_name"] for log in exercise_logs))[:4]
    top_foods = [name for name, _ in Counter(log["name"] for log in food_logs).most_common(5)]
    weight_change = 0.0
    if len(recent_weights) >= 2:
        weight_change = round(recent_weights[-1]["weight_kg"] - recent_weights[0]["weight_kg"], 2)

    activity = user.get("activity", "Active")
    protein_target = user.get("weight_kg", 70) * (1.6 if "Athlete" in activity or total_exercise_minutes >= 120 else 1.0)

    return {
        "days": days,
        "age": user.get("age", 25),
        "gender": user.get("gender", "Male"),
        "weight_kg": user.get("weight_kg", 70.0),
        "height_cm": user.get("height_cm", 175.0),
        "bmi": user.get("bmi", 0.0),
        "diet": user.get("diet", "Balanced"),
        "activity": activity,
        "daily_goal": user.get("daily_goal", 2000),
        "food_days_logged": len(calorie_rows),
        "avg_calories": round(avg_calories, 1),
        "avg_protein": round(avg_protein, 1),
        "avg_carbs": round(avg_carbs, 1),
        "avg_fat": round(avg_fat, 1),
        "protein_target": round(protein_target, 1),
        "hydration_days_logged": len(hydration_rows),
        "avg_hydration_ml": round(avg_hydration_ml, 1),
        "exercise_days_logged": len(exercise_rows),
        "total_exercise_minutes": int(total_exercise_minutes),
        "total_exercise_burned": int(total_exercise_burned),
        "exercise_types": exercise_types,
        "weight_change": weight_change,
        "top_foods": top_foods,
    }


def build_user_log_context(user_id: int, days: int = 7) -> str:
    """Format the recent user snapshot as a compact prompt-friendly context block."""
    snap = get_user_log_snapshot(user_id, days)
    foods = ", ".join(snap["top_foods"]) if snap["top_foods"] else "No recent foods logged"
    exercises = ", ".join(snap["exercise_types"]) if snap["exercise_types"] else "No exercise logged"
    bmi_text = f"{snap['bmi']:.1f}" if snap["bmi"] else "Not available"
    weight_trend = f"{snap['weight_change']:+.2f} kg" if snap["weight_change"] else "No clear change"
    return "\n".join([
        f"PROFILE: {snap['age']}y {snap['gender']}, {snap['weight_kg']:.1f} kg, {snap['height_cm']:.0f} cm, BMI {bmi_text}.",
        f"GOALS: Diet {snap['diet']}, activity {snap['activity']}, daily goal {snap['daily_goal']} kcal.",
        f"FOOD LOGS ({days}d): {snap['food_days_logged']}/{days} days logged, avg {snap['avg_calories']:.0f} kcal/day, protein {snap['avg_protein']:.0f} g/day, carbs {snap['avg_carbs']:.0f} g/day, fat {snap['avg_fat']:.0f} g/day.",
        f"HYDRATION ({days}d): {snap['hydration_days_logged']}/{days} days logged, avg {snap['avg_hydration_ml']:.0f} ml/day.",
        f"WEIGHT TREND ({days}d): {weight_trend}.",
        f"EXERCISE ({days}d): {snap['exercise_days_logged']} days logged, {snap['total_exercise_minutes']} total minutes, {snap['total_exercise_burned']} kcal burned, sessions: {exercises}.",
        f"COMMON FOODS: {foods}.",
        f"PROTEIN TARGET: about {snap['protein_target']:.0f} g/day based on current weight and activity.",
    ])


def _build_retrieval_query(query: str, user_id: int | None = None,
                           user_context: str = "", days: int = 7) -> str:
    parts = [query]
    if user_context:
        parts.append(user_context)
    if user_id is not None:
        snap = get_user_log_snapshot(user_id, days)
        parts.append(
            f"diet {snap['diet']} activity {snap['activity']} daily goal {snap['daily_goal']} calories"
        )
        if snap["avg_protein"] < snap["protein_target"] * 0.9:
            parts.append("protein intake muscle recovery strength training amino acids")
        if snap["avg_hydration_ml"] < 2500:
            parts.append("hydration water needs electrolytes dehydration")
        if snap["total_exercise_minutes"] > 0:
            parts.append("exercise fitness recovery pre workout post workout fueling")
        if snap["weight_change"] > 0.4:
            parts.append("calorie balance weight gain fat loss satiety")
        elif snap["weight_change"] < -0.4:
            parts.append("weight loss muscle preservation adequate protein")
    return ". ".join(parts)


def retrieve(query: str, top_k: int = 3, user_id: int | None = None,
             user_context: str = "", days: int = 7) -> list[dict]:
    """Return the most relevant coach documents via vector similarity search."""
    collection = _build_collection()
    retrieval_query = _build_retrieval_query(query, user_id, user_context, days)
    query_tokens = set(tokenize(query))
    result = collection.query(
        query_embeddings=[embed_text(retrieval_query)],
        n_results=min(max(top_k * 3, top_k), len(KNOWLEDGE_BASE)),
        include=["distances", "metadatas"],
    )

    doc_map = {doc["id"]: doc for doc in KNOWLEDGE_BASE}
    results = []
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    for doc_id, distance, metadata in zip(ids, distances, metadatas):
        entry = doc_map[doc_id]
        vector_score = max(0.0, 1.0 - float(distance))
        topic_tokens = set(tokenize(entry["topic"]))
        doc_tokens = set(tokenize(entry["text"]))
        lexical_overlap = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)
        topic_overlap = len(query_tokens & topic_tokens) / max(len(query_tokens), 1)
        score = min(1.0, vector_score + (0.35 * lexical_overlap) + (0.45 * topic_overlap))
        results.append({
            "id": entry["id"],
            "topic": metadata.get("topic", entry["topic"]),
            "text": entry["text"],
            "score": round(score, 4),
        })
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


def build_rag_context(query: str, top_k: int = 3, user_id: int | None = None,
                      user_context: str = "", days: int = 7) -> str:
    """Combine retrieved coach documents with recent user logs for prompting."""
    docs = retrieve(query, top_k, user_id=user_id, user_context=user_context, days=days)
    lines = ["VERIFIED FITNESS AND NUTRITION KNOWLEDGE BASE CONTEXT:"]
    for doc in docs:
        lines.append(f"\n--- [{doc['topic']}] ---")
        lines.append(doc["text"])
    if user_id is not None:
        lines.append("\nUSER PROFILE AND LAST 7 DAYS OF LOGS:")
        lines.append(build_user_log_context(user_id, days=days))
    elif user_context:
        lines.append("\nUSER PERSONAL CONTEXT:")
        lines.append(user_context)
    lines.append("\n" + "-" * 60)
    return "\n".join(lines)


def get_retrieved_sources(query: str, top_k: int = 3, user_id: int | None = None,
                          user_context: str = "", days: int = 7) -> list[dict]:
    """Return lightweight source metadata for UI display."""
    docs = retrieve(query, top_k, user_id=user_id, user_context=user_context, days=days)
    return [{"topic": d["topic"], "id": d["id"], "score": d["score"]} for d in docs]
