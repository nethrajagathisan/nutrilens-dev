"""
Reinforcement-learning agent for adaptive calorie-goal adjustment.

Pure-Python implementation — no ML libraries required.
Four-step loop: observe → reward → action → apply.
"""

import datetime

from core.database import (
    get_user_by_id,
    get_daily_calorie_summary,
    get_daily_hydration_summary,
    get_weight_history,
    get_last_rl_update_days,
    log_rl_transition,
    update_user,
)

# ── Constants ──────────────────────────────────────────────────────────────────

OBSERVATION_WINDOW = 7  # days of history to observe

MIN_DAYS_BETWEEN_UPDATES = 7  # cooldown between goal adjustments

# Reward weights
W_ADHERENCE   = 0.40
W_WEIGHT      = 0.35
W_HYDRATION   = 0.15
W_CONSISTENCY = 0.10

# Safety bounds
MIN_GOAL_FRACTION = 0.85   # goal never below 85 % of BMR
MAX_GOAL_FRACTION = 2.50   # goal never above 250 % of BMR
ABSOLUTE_MIN_GOAL = 1200   # hard floor in kcal

# Activity multipliers (Mifflin-St Jeor)
_ACTIVITY_MULT = {
    "Lazy":    1.2,
    "Active":  1.55,
    "Athlete": 1.9,
}


# ── Observe ────────────────────────────────────────────────────────────────────

def observe_state(user_id: int) -> dict:
    """Gather every signal the agent needs from the database."""
    user = get_user_by_id(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    # --- BMR via Mifflin-St Jeor ---
    w = user["weight_kg"]
    h = user["height_cm"]
    age = user["age"]
    gender = user["gender"]
    activity_raw = user["activity"]

    gender_offset = 5 if "Male" in gender else -161
    base_bmr = (10 * w) + (6.25 * h) - (5 * age) + gender_offset

    # Normalise activity string (may contain emoji)
    mult = 1.55  # default
    for key, val in _ACTIVITY_MULT.items():
        if key in activity_raw:
            mult = val
            break
    bmr_estimate = int(base_bmr * mult)

    # --- Calorie averages (last 7 days) ---
    cal_rows = get_daily_calorie_summary(user_id, days=OBSERVATION_WINDOW)
    avg_calories = (
        sum(r["total_cals"] for r in cal_rows) / len(cal_rows)
        if cal_rows else 0.0
    )
    daily_goal = user["daily_goal"]
    adherence_ratio = round(avg_calories / daily_goal, 3) if daily_goal else 0.0

    # --- Log consistency ---
    log_consistency = round(len(cal_rows) / OBSERVATION_WINDOW, 3)

    # --- Hydration ---
    hyd_rows = get_daily_hydration_summary(user_id, days=OBSERVATION_WINDOW)
    avg_water = (
        sum(r["total_ml"] for r in hyd_rows) / len(hyd_rows)
        if hyd_rows else 0.0
    )
    hydration_ratio = round(min(avg_water / 2500.0, 1.0), 3)

    # --- Weight delta ---
    weight_hist = get_weight_history(user_id)
    weight_delta = 0.0
    if len(weight_hist) >= 2:
        cutoff = (datetime.date.today() - datetime.timedelta(days=OBSERVATION_WINDOW)).isoformat()
        older = [r for r in weight_hist if r["logged_at"][:10] <= cutoff]
        if older:
            weight_delta = round(weight_hist[-1]["weight_kg"] - older[-1]["weight_kg"], 2)

    return {
        "user_id":          user_id,
        "daily_goal":       daily_goal,
        "bmr_estimate":     bmr_estimate,
        "avg_calories":     round(avg_calories, 1),
        "adherence_ratio":  adherence_ratio,
        "log_consistency":  log_consistency,
        "hydration_ratio":  hydration_ratio,
        "weight_delta":     weight_delta,
        "days_since_update": get_last_rl_update_days(user_id),
        "user_diet":        user.get("diet", "Balanced"),
    }


# ── Reward ─────────────────────────────────────────────────────────────────────

def compute_reward(state: dict) -> tuple[float, str]:
    """Return (total_reward, human-readable reason)."""
    ar = state["adherence_ratio"]
    wd = state["weight_delta"]
    hr = state["hydration_ratio"]
    lc = state["log_consistency"]
    diet = state["user_diet"].lower()

    parts: list[str] = []

    # -- Adherence sub-reward --
    if 0.90 <= ar <= 1.10:
        r_adh = 1.0;  parts.append("adherence on-target")
    elif 0.80 <= ar < 0.90:
        r_adh = 0.3;  parts.append("adherence slightly low")
    elif 1.10 < ar <= 1.25:
        r_adh = 0.0;  parts.append("adherence slightly high")
    elif ar > 1.25:
        r_adh = -0.3; parts.append("adherence too high")
    elif ar < 0.70 and lc > 0.70:
        r_adh = -0.5; parts.append("adherence very low despite consistent logging")
    else:
        r_adh = -0.1; parts.append("adherence low / sparse logs")

    # -- Weight-direction sub-reward --
    if "keto" in diet:
        if wd < -0.1:
            r_wt = 1.0;  parts.append("losing weight (keto goal)")
        elif -0.1 <= wd <= 0.2:
            r_wt = 0.3;  parts.append("weight stable (keto)")
        else:
            r_wt = -0.5; parts.append("gaining weight (against keto goal)")
    elif "vegan" in diet or "balanced" in diet:
        if abs(wd) <= 0.3:
            r_wt = 1.0;  parts.append("weight maintained")
        else:
            r_wt = round(max(-0.5, 1.0 - abs(wd) / 0.3 * 1.5), 2)
            parts.append(f"weight drifting ({wd:+.1f} kg)")
    else:
        if abs(wd) <= 0.3:
            r_wt = 1.0;  parts.append("weight maintained")
        else:
            r_wt = round(max(-0.5, 1.0 - abs(wd) / 0.3 * 1.5), 2)
            parts.append(f"weight drifting ({wd:+.1f} kg)")

    # -- Hydration sub-reward --
    if hr >= 0.80:
        r_hy = 1.0;  parts.append("hydration good")
    elif hr >= 0.50:
        r_hy = 0.3;  parts.append("hydration moderate")
    else:
        r_hy = -0.3; parts.append("hydration low")

    # -- Consistency sub-reward --
    if lc >= 0.85:
        r_co = 1.0;  parts.append("logging very consistent")
    elif lc >= 0.57:
        r_co = 0.3;  parts.append("logging moderate")
    else:
        r_co = -0.5; parts.append("logging inconsistent")

    total = (W_ADHERENCE * r_adh + W_WEIGHT * r_wt
             + W_HYDRATION * r_hy + W_CONSISTENCY * r_co)
    reason = "; ".join(parts)
    return round(total, 4), reason


# ── Action selection ───────────────────────────────────────────────────────────

def _wrong_weight_direction(state: dict) -> bool:
    """True when weight is trending opposite to dietary intent."""
    diet = state["user_diet"].lower()
    wd = state["weight_delta"]
    if "keto" in diet:
        return wd > 0.2          # gaining when should lose
    return abs(wd) > 0.5         # drifting too far from maintenance


def select_action(state: dict, reward: float) -> tuple[int, str]:
    """Return (action_kcal, explanation)."""
    ar  = state["adherence_ratio"]
    lc  = state["log_consistency"]
    dsu = state["days_since_update"]
    dg  = state["daily_goal"]
    bmr = state["bmr_estimate"]

    # Rule 1 – cooldown
    if dsu < MIN_DAYS_BETWEEN_UPDATES:
        return 0, f"Last update was {dsu}d ago; waiting for {MIN_DAYS_BETWEEN_UPDATES}d cooldown."

    # Rule 2 – below safety floor
    if dg < bmr * MIN_GOAL_FRACTION:
        return 100, "Goal is below safe minimum (85 % of estimated BMR). Raising."

    # Rule 3 – well-aligned
    if 0.90 <= ar <= 1.10 and reward > 0.5:
        return 0, "Goal is well-aligned with actual intake and outcomes."

    # Rule 4 – very low adherence, consistent logger
    if ar < 0.75 and lc > 0.70:
        return -100, "You log consistently but can't reach the goal — it's likely too high."

    # Rule 5 – moderately low adherence, consistent logger
    if ar < 0.85 and lc > 0.70:
        return -50, "Intake is somewhat below goal despite consistent logging — slight reduction advised."

    # Rule 6 – high adherence but bad weight trend
    if ar > 1.20 and _wrong_weight_direction(state):
        return 0, "Intake exceeds goal, but weight is trending negatively — not raising."

    # Rule 7 – high adherence, good outcomes
    if ar > 1.20 and reward > 0.5:
        return 100, "Metabolism is clearly higher than the current goal reflects."

    # Rule 8 – moderately high adherence
    if ar > 1.10 and reward > 0.3:
        return 50, "Actual metabolic need appears slightly higher than the goal."

    # Rule 9 – default
    return 0, "No significant pattern detected; keeping goal unchanged."


# ── Apply ──────────────────────────────────────────────────────────────────────

def apply_action(user_id: int, action_kcal: int, state: dict,
                 reward: float, reason: str) -> dict:
    """Clamp proposed goal, persist it, and log the transition."""
    old_goal = state["daily_goal"]
    bmr = state["bmr_estimate"]

    floor = max(ABSOLUTE_MIN_GOAL, int(bmr * MIN_GOAL_FRACTION))
    ceiling = int(bmr * MAX_GOAL_FRACTION)
    new_goal = max(floor, min(old_goal + action_kcal, ceiling))

    changed = new_goal != old_goal
    if changed:
        update_user(user_id, daily_goal=new_goal)

    log_rl_transition(
        user_id=user_id,
        old_goal=old_goal,
        new_goal=new_goal,
        action_kcal=action_kcal,
        reward=reward,
        adherence_ratio=state["adherence_ratio"],
        weight_delta=state["weight_delta"],
        log_consistency=state["log_consistency"],
        reason=reason,
    )

    return {
        "old_goal": old_goal,
        "new_goal": new_goal,
        "action":   action_kcal,
        "reward":   reward,
        "reason":   reason,
        "changed":  changed,
    }


# ── Run full cycle ─────────────────────────────────────────────────────────────

def run_rl_cycle(user_id: int) -> dict:
    """Execute one observe → reward → action → apply loop."""
    state = observe_state(user_id)
    reward, reason = compute_reward(state)
    action_kcal, explanation = select_action(state, reward)
    full_reason = f"{explanation} [{reason}]"
    return apply_action(user_id, action_kcal, state, reward, full_reason)
