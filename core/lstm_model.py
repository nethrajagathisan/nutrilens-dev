"""
Lightweight LSTM model for learning user meal patterns and predicting
preferred food categories.  Uses a reservoir-computing approach: the LSTM
cell weights are initialised once (Xavier + forget-gate bias = 1) and kept
fixed; only the output (readout) layer is trained with analytical gradients.
This is stable, fast, and works well with small food-log datasets.
"""

import math
import numpy as np
from collections import Counter
from datetime import datetime

# ── Food categories & meal types ────────────────────────────────────────────

FOOD_CATEGORIES = [
    "grain", "protein", "vegetable", "fruit", "dairy",
    "fat", "beverage", "snack", "mixed", "other",
]

MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack"]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "grain": [
        "rice", "bread", "pasta", "oat", "cereal", "wheat", "noodle", "roti",
        "chapati", "quinoa", "barley", "tortilla", "bagel", "muffin",
        "pancake", "waffle", "couscous", "wrap", "pita", "granola",
    ],
    "protein": [
        "chicken", "egg", "fish", "meat", "beef", "pork", "turkey", "tofu",
        "tempeh", "lentil", "bean", "chickpea", "shrimp", "salmon", "tuna",
        "lamb", "steak", "sausage", "prawn", "cod", "tilapia", "paneer",
    ],
    "vegetable": [
        "salad", "spinach", "broccoli", "carrot", "tomato", "cucumber",
        "pepper", "onion", "lettuce", "kale", "cauliflower", "zucchini",
        "pea", "corn", "celery", "cabbage", "mushroom", "asparagus",
        "vegetable", "eggplant", "beetroot", "squash",
    ],
    "fruit": [
        "apple", "banana", "orange", "berry", "grape", "mango", "melon",
        "pear", "peach", "strawberry", "blueberry", "pineapple",
        "watermelon", "kiwi", "avocado", "cherry", "plum", "fruit",
    ],
    "dairy": [
        "milk", "cheese", "yogurt", "butter", "cream", "paneer", "curd",
        "cottage", "whey", "lassi",
    ],
    "fat": [
        "oil", "nut", "almond", "walnut", "peanut", "cashew", "seed",
        "olive", "coconut oil", "flaxseed", "chia",
    ],
    "beverage": [
        "coffee", "tea", "juice", "smoothie", "shake", "soda", "drink",
        "latte", "espresso", "kombucha",
    ],
    "snack": [
        "chip", "cookie", "candy", "chocolate", "biscuit", "popcorn",
        "pretzel", "granola bar", "protein bar",
    ],
    "mixed": [
        "pizza", "burger", "sandwich", "wrap", "burrito", "taco", "soup",
        "stew", "curry", "stir fry", "bowl", "biryani", "fried rice",
        "noodle soup", "sushi", "roll", "casserole", "lasagna", "ramen",
    ],
}


def categorize_food(food_name: str) -> str:
    """Classify a food name into a predefined category via keyword matching."""
    name_lower = food_name.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > 0:
            scores[category] = score
    return max(scores, key=scores.get) if scores else "other"


# ── Activation helpers ──────────────────────────────────────────────────────

def _sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()


# ── LSTM cell ───────────────────────────────────────────────────────────────

class LSTMCell:
    """Single LSTM cell (forget / input / candidate / output gates)."""

    def __init__(self, input_size: int, hidden_size: int, seed: int = 42):
        rng = np.random.RandomState(seed)
        scale_ih = np.sqrt(2.0 / (input_size + hidden_size))
        scale_hh = np.sqrt(2.0 / (hidden_size * 2))

        self.W_ih = rng.randn(4 * hidden_size, input_size) * scale_ih
        self.W_hh = rng.randn(4 * hidden_size, hidden_size) * scale_hh
        self.b = np.zeros(4 * hidden_size)
        self.b[:hidden_size] = 1.0          # forget-gate bias → 1

        self.hidden_size = hidden_size

    def forward(self, x: np.ndarray, h_prev: np.ndarray, c_prev: np.ndarray):
        gates = self.W_ih @ x + self.W_hh @ h_prev + self.b
        hs = self.hidden_size
        f = _sigmoid(gates[:hs])
        i = _sigmoid(gates[hs:2 * hs])
        g = np.tanh(gates[2 * hs:3 * hs])
        o = _sigmoid(gates[3 * hs:4 * hs])
        c = f * c_prev + i * g
        h = o * np.tanh(c)
        return h, c


# ── LSTM model ──────────────────────────────────────────────────────────────

class MealPatternLSTM:
    """
    Learns eating patterns from food-log history.

    Architecture
    ────────────
    Encoder   : Fixed-weight LSTM (reservoir) that processes a meal sequence.
    Readout   : Dense layer  hidden → food-category probabilities (trained).
    """

    INPUT_SIZE = 24          # cat(10) + meal(4) + dow(7) + macros(3)
    HIDDEN_SIZE = 32
    OUTPUT_SIZE = len(FOOD_CATEGORIES)   # 10
    SEQ_LENGTH = 14

    def __init__(self, seed: int = 42):
        self.lstm = LSTMCell(self.INPUT_SIZE, self.HIDDEN_SIZE, seed=seed)
        rng = np.random.RandomState(seed + 1)
        scale = np.sqrt(2.0 / (self.HIDDEN_SIZE + self.OUTPUT_SIZE))
        self.W_out = rng.randn(self.OUTPUT_SIZE, self.HIDDEN_SIZE) * scale
        self.b_out = np.zeros(self.OUTPUT_SIZE)
        self._trained = False

    # ── encoding ────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_dow(logged_at: str) -> int:
        try:
            return datetime.fromisoformat(logged_at).weekday()
        except Exception:
            return 0

    def _encode_meal(self, name: str, meal: str, dow: int,
                     cal: int, carbs: int, protein: int, fat: int) -> np.ndarray:
        vec = np.zeros(self.INPUT_SIZE)
        cat = categorize_food(name)
        cat_idx = FOOD_CATEGORIES.index(cat) if cat in FOOD_CATEGORIES else 9
        vec[cat_idx] = 1.0
        meal_idx = MEAL_TYPES.index(meal) if meal in MEAL_TYPES else 3
        vec[10 + meal_idx] = 1.0
        vec[14 + (dow % 7)] = 1.0
        vec[21] = min(cal / 1000.0, 3.0)
        vec[22] = min(protein / 100.0, 3.0)
        vec[23] = min(carbs / 100.0, 3.0)
        return vec

    def _encode_logs(self, food_logs: list[dict]):
        encoded, targets = [], []
        for log in food_logs:
            dow = self._parse_dow(log.get("logged_at", ""))
            x = self._encode_meal(
                log.get("name", ""), log.get("meal", "Snack"), dow,
                log.get("calories", 0), log.get("carbs", 0),
                log.get("protein", 0), log.get("fat", 0),
            )
            encoded.append(x)
            cat = categorize_food(log.get("name", ""))
            t = np.zeros(self.OUTPUT_SIZE)
            t[FOOD_CATEGORIES.index(cat) if cat in FOOD_CATEGORIES else 9] = 1.0
            targets.append(t)
        return encoded, targets

    # ── forward ─────────────────────────────────────────────────────────────

    def _forward(self, sequence: list[np.ndarray]):
        h = np.zeros(self.HIDDEN_SIZE)
        c = np.zeros(self.HIDDEN_SIZE)
        for x in sequence:
            h, c = self.lstm.forward(x, h, c)
        logits = self.W_out @ h + self.b_out
        return _softmax(logits), h

    # ── training (readout layer only) ───────────────────────────────────────

    def train(self, food_logs: list[dict], epochs: int = 30, lr: float = 0.01):
        if len(food_logs) < 5:
            self._trained = False
            return

        encoded, targets = self._encode_logs(food_logs)
        seq_len = min(self.SEQ_LENGTH, len(encoded) - 1)
        if seq_len < 2:
            self._trained = False
            return

        for epoch in range(epochs):
            total_loss = 0.0
            n = 0
            for i in range(seq_len, len(encoded)):
                seq = encoded[i - seq_len:i]
                target = targets[i]
                probs, h = self._forward(seq)
                total_loss += -np.sum(target * np.log(probs + 1e-8))
                n += 1
                grad = probs - target
                self.W_out -= lr * np.outer(grad, h)
                self.b_out -= lr * grad

            if n and total_loss / n < 0.5:
                break

        self._trained = True

    # ── prediction ──────────────────────────────────────────────────────────

    def predict_preferences(self, recent_logs: list[dict],
                            target_meal: str = "Lunch",
                            target_dow: int = 0) -> dict[str, float]:
        if not self._trained or len(recent_logs) < 3:
            return self._fallback_preferences(recent_logs)

        encoded, _ = self._encode_logs(recent_logs[-self.SEQ_LENGTH:])
        query = np.zeros(self.INPUT_SIZE)
        meal_idx = MEAL_TYPES.index(target_meal) if target_meal in MEAL_TYPES else 1
        query[10 + meal_idx] = 1.0
        query[14 + (target_dow % 7)] = 1.0
        encoded.append(query)

        probs, _ = self._forward(encoded)
        return {cat: round(float(probs[i]), 4) for i, cat in enumerate(FOOD_CATEGORIES)}

    def _fallback_preferences(self, food_logs: list[dict]) -> dict[str, float]:
        counts: Counter = Counter()
        for log in food_logs:
            counts[categorize_food(log.get("name", ""))] += 1
        total = max(sum(counts.values()), 1)
        prefs = {cat: round(counts.get(cat, 0) / total, 4) for cat in FOOD_CATEGORIES}
        if total <= 1:
            prefs = {cat: round(1.0 / len(FOOD_CATEGORIES), 4) for cat in FOOD_CATEGORIES}
        return prefs

    # ── analytics helpers ───────────────────────────────────────────────────

    def get_top_foods_by_meal(self, food_logs: list[dict]) -> dict[str, list[str]]:
        meal_foods: dict[str, Counter] = {m: Counter() for m in MEAL_TYPES}
        for log in food_logs:
            meal = log.get("meal", "Snack")
            if meal not in meal_foods:
                meal = "Snack"
            meal_foods[meal][log.get("name", "Unknown")] += 1
        return {m: [f for f, _ in c.most_common(5)] for m, c in meal_foods.items()}

    def get_avg_macros_by_meal(self, food_logs: list[dict]) -> dict[str, dict]:
        buckets: dict[str, dict[str, list]] = {
            m: {"calories": [], "carbs": [], "protein": [], "fat": []}
            for m in MEAL_TYPES
        }
        for log in food_logs:
            meal = log.get("meal", "Snack")
            if meal not in buckets:
                meal = "Snack"
            for key in ("calories", "carbs", "protein", "fat"):
                buckets[meal][key].append(log.get(key, 0))

        result = {}
        for meal, macros in buckets.items():
            if macros["calories"]:
                n = len(macros["calories"])
                result[meal] = {
                    f"avg_{k}": round(sum(v) / n) for k, v in macros.items()
                }
            else:
                result[meal] = {f"avg_{k}": 0 for k in ("calories", "carbs", "protein", "fat")}
        return result

    # ── serialisation ───────────────────────────────────────────────────────

    def serialize(self) -> dict:
        return {
            "W_ih": self.lstm.W_ih.tolist(),
            "W_hh": self.lstm.W_hh.tolist(),
            "b": self.lstm.b.tolist(),
            "W_out": self.W_out.tolist(),
            "b_out": self.b_out.tolist(),
            "trained": self._trained,
        }

    def load(self, data: dict):
        self.lstm.W_ih = np.array(data["W_ih"])
        self.lstm.W_hh = np.array(data["W_hh"])
        self.lstm.b = np.array(data["b"])
        self.W_out = np.array(data["W_out"])
        self.b_out = np.array(data["b_out"])
        self._trained = data.get("trained", False)
