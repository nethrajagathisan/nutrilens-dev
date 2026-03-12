"""
Nutritional Fingerprint Engine
──────────────────────────────
Computes and maintains a 10-dimensional EMA-smoothed vector that
captures a user's evolving nutritional identity.
"""

from core.database import (
    get_food_logs_today,
    get_hydration_today,
    get_user_by_id,
    get_fingerprint,
    save_fingerprint,
    get_fingerprint_history,
)

# ─── Dimension metadata ───────────────────────────────────

DIMENSION_LABELS = [
    "Calorie Balance",
    "Protein Intake",
    "Carbohydrate Intake",
    "Fat Intake",
    "Hydration",
    "Breakfast Regularity",
    "Lunch Regularity",
    "Dinner Regularity",
    "Meal Diversity",
    "Logging Streak",
]

DIMENSION_EMOJIS = [
    "🔥", "💪", "🍞", "🧈", "💧",
    "🌅", "☀️", "🌙", "🍽️", "📝",
]

HEALTHY_REFERENCE = [1.0] * 10

HEALTH_WEIGHTS = [1.0, 1.5, 1.0, 1.0, 1.5, 0.8, 0.8, 0.8, 0.6, 0.5]


def _clamp(val: float) -> float:
    return max(0.0, min(1.0, val))


# ─── Core computation ─────────────────────────────────────

def compute_daily_vector(user_id: int) -> list[float]:
    """Build today's raw 10-element vector from logged data."""
    logs = get_food_logs_today(user_id)
    if not logs:
        return [0.0] * 10

    user = get_user_by_id(user_id) or {}
    daily_goal = user.get("daily_goal", 2000) or 2000
    weight_kg = user.get("weight_kg", 70) or 70

    total_cals = sum(l["calories"] for l in logs)
    total_protein = sum(l["protein"] for l in logs)
    total_carbs = sum(l["carbs"] for l in logs)
    total_fat = sum(l["fat"] for l in logs)
    water_ml = get_hydration_today(user_id)

    meals = {l["meal"] for l in logs}
    has_breakfast = 1.0 if any("Breakfast" in m for m in meals) else 0.0
    has_lunch = 1.0 if any("Lunch" in m for m in meals) else 0.0
    has_dinner = 1.0 if any("Dinner" in m for m in meals) else 0.0
    distinct_meals = len(meals)

    vector = [
        _clamp(total_cals / daily_goal),           # 0  Calorie Balance
        _clamp(total_protein / (weight_kg * 0.8)),  # 1  Protein Intake
        _clamp(total_carbs / 275),                  # 2  Carbohydrate Intake
        _clamp(total_fat / 78),                     # 3  Fat Intake
        _clamp(water_ml / 2500),                    # 4  Hydration
        has_breakfast,                               # 5  Breakfast Regularity
        has_lunch,                                   # 6  Lunch Regularity
        has_dinner,                                  # 7  Dinner Regularity
        _clamp(distinct_meals / 4),                  # 8  Meal Diversity
        1.0,                                         # 9  Logging Streak (logged today)
    ]
    return vector


def update_fingerprint(user_id: int, alpha: float = 0.15) -> list[float]:
    """EMA-update the stored fingerprint with today's vector and persist."""
    old = get_fingerprint(user_id)
    today = compute_daily_vector(user_id)
    new = [
        alpha * today[i] + (1 - alpha) * old[i]
        for i in range(10)
    ]
    save_fingerprint(user_id, new)
    return new


# ─── Analysis helpers ─────────────────────────────────────

def analyze_deficiencies(fingerprint: list[float]) -> list[dict]:
    """Compare fingerprint against the healthy reference and classify gaps."""
    results = []
    for i in range(10):
        score = fingerprint[i]
        gap = HEALTHY_REFERENCE[i] - score
        if score < 0.40:
            severity = "critical"
        elif score < 0.65:
            severity = "caution"
        else:
            severity = "good"
        results.append({
            "index": i,
            "label": DIMENSION_LABELS[i],
            "emoji": DIMENSION_EMOJIS[i],
            "score": round(score, 3),
            "gap": round(gap, 3),
            "severity": severity,
        })
    severity_order = {"critical": 0, "caution": 1, "good": 2}
    results.sort(key=lambda d: severity_order[d["severity"]])
    return results


def compute_overall_health_score(fingerprint: list[float]) -> float:
    """Weighted average of all 10 dimensions, scaled 0–100."""
    total_weight = sum(HEALTH_WEIGHTS)
    weighted = sum(fingerprint[i] * HEALTH_WEIGHTS[i] for i in range(10))
    return round((weighted / total_weight) * 100, 1)


def get_fingerprint_trend(user_id: int, days: int = 14) -> list[dict]:
    """Replay EMA forward over historical daily aggregates."""
    history = get_fingerprint_history(user_id, days)
    if not history:
        return []

    user = get_user_by_id(user_id) or {}
    daily_goal = user.get("daily_goal", 2000) or 2000
    weight_kg = user.get("weight_kg", 70) or 70
    alpha = 0.15

    fp = [0.5] * 10  # neutral starting point
    trend = []

    for row in history:
        total_cals = row["total_cals"]
        total_protein = row["total_protein"]
        total_carbs = row["total_carbs"]
        total_fat = row["total_fat"]
        meals_logged = row["meals_logged"]

        day_vec = [
            _clamp(total_cals / daily_goal),
            _clamp(total_protein / (weight_kg * 0.8)),
            _clamp(total_carbs / 275),
            _clamp(total_fat / 78),
            0.5,   # hydration not available in aggregated history
            1.0 if meals_logged >= 1 else 0.0,
            1.0 if meals_logged >= 2 else 0.0,
            1.0 if meals_logged >= 3 else 0.0,
            _clamp(min(meals_logged, 4) / 4),
            1.0,
        ]

        fp = [alpha * day_vec[i] + (1 - alpha) * fp[i] for i in range(10)]
        score = compute_overall_health_score(fp)
        trend.append({
            "day": row["day"],
            "vector": [round(v, 4) for v in fp],
            "health_score": score,
        })

    return trend
