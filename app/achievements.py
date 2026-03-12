import streamlit as st
import math

from core.database import get_achievement_stats

# Badge definitions: (id, name, emoji, description, category, check_fn)
# check_fn takes stats dict and returns (earned: bool, progress: float 0-1, detail: str)
BADGES = [
    # ── First Steps ──
    {
        "id": "first_log", "name": "First Bite", "emoji": "🍽️",
        "desc": "Log your first food entry",
        "category": "Milestones",
        "check": lambda s: (s["total_entries"] >= 1, min(s["total_entries"] / 1, 1.0),
                            f"{s['total_entries']}/1 entries"),
    },
    {
        "id": "log_10", "name": "Getting Started", "emoji": "📝",
        "desc": "Log 10 food entries",
        "category": "Milestones",
        "check": lambda s: (s["total_entries"] >= 10, min(s["total_entries"] / 10, 1.0),
                            f"{s['total_entries']}/10 entries"),
    },
    {
        "id": "log_50", "name": "Dedicated Logger", "emoji": "📊",
        "desc": "Log 50 food entries",
        "category": "Milestones",
        "check": lambda s: (s["total_entries"] >= 50, min(s["total_entries"] / 50, 1.0),
                            f"{s['total_entries']}/50 entries"),
    },
    {
        "id": "log_100", "name": "Centurion", "emoji": "💯",
        "desc": "Log 100 food entries",
        "category": "Milestones",
        "check": lambda s: (s["total_entries"] >= 100, min(s["total_entries"] / 100, 1.0),
                            f"{s['total_entries']}/100 entries"),
    },
    {
        "id": "log_500", "name": "Nutrition Master", "emoji": "🏆",
        "desc": "Log 500 food entries",
        "category": "Milestones",
        "check": lambda s: (s["total_entries"] >= 500, min(s["total_entries"] / 500, 1.0),
                            f"{s['total_entries']}/500 entries"),
    },

    # ── Streaks ──
    {
        "id": "streak_3", "name": "Hat Trick", "emoji": "🎯",
        "desc": "Maintain a 3-day logging streak",
        "category": "Streaks",
        "check": lambda s: (s["streak"] >= 3, min(s["streak"] / 3, 1.0),
                            f"{s['streak']}/3 day streak"),
    },
    {
        "id": "streak_7", "name": "Week Warrior", "emoji": "🔥",
        "desc": "Maintain a 7-day logging streak",
        "category": "Streaks",
        "check": lambda s: (s["streak"] >= 7, min(s["streak"] / 7, 1.0),
                            f"{s['streak']}/7 day streak"),
    },
    {
        "id": "streak_14", "name": "Fortnight Force", "emoji": "⚡",
        "desc": "Maintain a 14-day logging streak",
        "category": "Streaks",
        "check": lambda s: (s["streak"] >= 14, min(s["streak"] / 14, 1.0),
                            f"{s['streak']}/14 day streak"),
    },
    {
        "id": "streak_30", "name": "Monthly Champion", "emoji": "👑",
        "desc": "Maintain a 30-day logging streak",
        "category": "Streaks",
        "check": lambda s: (s["streak"] >= 30, min(s["streak"] / 30, 1.0),
                            f"{s['streak']}/30 day streak"),
    },

    # ── Hydration ──
    {
        "id": "hydration_1", "name": "First Sip", "emoji": "💧",
        "desc": "Hit your hydration goal (3000ml) for the first time",
        "category": "Hydration",
        "check": lambda s: (s["hydration_perfect_days"] >= 1,
                            min(s["hydration_perfect_days"] / 1, 1.0),
                            f"{s['hydration_perfect_days']}/1 perfect days"),
    },
    {
        "id": "hydration_7", "name": "Hydro Hero", "emoji": "🌊",
        "desc": "Hit hydration goal 7 times",
        "category": "Hydration",
        "check": lambda s: (s["hydration_perfect_days"] >= 7,
                            min(s["hydration_perfect_days"] / 7, 1.0),
                            f"{s['hydration_perfect_days']}/7 perfect days"),
    },
    {
        "id": "hydration_30", "name": "Water Master", "emoji": "🐟",
        "desc": "Hit hydration goal 30 times",
        "category": "Hydration",
        "check": lambda s: (s["hydration_perfect_days"] >= 30,
                            min(s["hydration_perfect_days"] / 30, 1.0),
                            f"{s['hydration_perfect_days']}/30 perfect days"),
    },

    # ── Exercise ──
    {
        "id": "exercise_1", "name": "First Workout", "emoji": "🏃",
        "desc": "Log your first exercise session",
        "category": "Exercise",
        "check": lambda s: (s["exercise_sessions"] >= 1,
                            min(s["exercise_sessions"] / 1, 1.0),
                            f"{s['exercise_sessions']}/1 sessions"),
    },
    {
        "id": "exercise_10", "name": "Fitness Fan", "emoji": "💪",
        "desc": "Complete 10 exercise sessions",
        "category": "Exercise",
        "check": lambda s: (s["exercise_sessions"] >= 10,
                            min(s["exercise_sessions"] / 10, 1.0),
                            f"{s['exercise_sessions']}/10 sessions"),
    },
    {
        "id": "exercise_50", "name": "Gym Rat", "emoji": "🏋️",
        "desc": "Complete 50 exercise sessions",
        "category": "Exercise",
        "check": lambda s: (s["exercise_sessions"] >= 50,
                            min(s["exercise_sessions"] / 50, 1.0),
                            f"{s['exercise_sessions']}/50 sessions"),
    },
    {
        "id": "ex_streak_7", "name": "Exercise Streak", "emoji": "🔥",
        "desc": "Exercise 7 days in a row",
        "category": "Exercise",
        "check": lambda s: (s["exercise_streak"] >= 7,
                            min(s["exercise_streak"] / 7, 1.0),
                            f"{s['exercise_streak']}/7 day exercise streak"),
    },

    # ── Goals ──
    {
        "id": "under_goal_7", "name": "On Track", "emoji": "🎯",
        "desc": "Stay within calorie goal for 7 days",
        "category": "Goals",
        "check": lambda s: (s["under_goal_days"] >= 7,
                            min(s["under_goal_days"] / 7, 1.0),
                            f"{s['under_goal_days']}/7 on-goal days"),
    },
    {
        "id": "under_goal_30", "name": "Calorie Commander", "emoji": "⭐",
        "desc": "Stay within calorie goal for 30 days",
        "category": "Goals",
        "check": lambda s: (s["under_goal_days"] >= 30,
                            min(s["under_goal_days"] / 30, 1.0),
                            f"{s['under_goal_days']}/30 on-goal days"),
    },

    # ── Weight Tracking ──
    {
        "id": "weight_1", "name": "Scale Starter", "emoji": "⚖️",
        "desc": "Log your weight for the first time",
        "category": "Milestones",
        "check": lambda s: (s["weight_logs"] >= 1,
                            min(s["weight_logs"] / 1, 1.0),
                            f"{s['weight_logs']}/1 weight logs"),
    },
    {
        "id": "weight_10", "name": "Weight Watcher", "emoji": "📉",
        "desc": "Log your weight 10 times",
        "category": "Milestones",
        "check": lambda s: (s["weight_logs"] >= 10,
                            min(s["weight_logs"] / 10, 1.0),
                            f"{s['weight_logs']}/10 weight logs"),
    },

    # ── Active Days ──
    {
        "id": "active_7", "name": "Week Active", "emoji": "📅",
        "desc": "Log food on 7 different days",
        "category": "Milestones",
        "check": lambda s: (s["active_days"] >= 7,
                            min(s["active_days"] / 7, 1.0),
                            f"{s['active_days']}/7 active days"),
    },
    {
        "id": "active_30", "name": "Month Active", "emoji": "🗓️",
        "desc": "Log food on 30 different days",
        "category": "Milestones",
        "check": lambda s: (s["active_days"] >= 30,
                            min(s["active_days"] / 30, 1.0),
                            f"{s['active_days']}/30 active days"),
    },
]


def _compute_level(earned_count: int) -> tuple[int, str, int, int]:
    """Return (level, title, current_xp, xp_to_next)."""
    xp = earned_count * 100  # 100 XP per badge
    level = 1 + int(math.sqrt(xp / 50))  # level = 1 + sqrt(xp/50)
    titles = [
        "Beginner", "Learner", "Explorer", "Achiever", "Warrior",
        "Champion", "Master", "Legend", "Mythic", "Transcendent",
    ]
    title = titles[min(level - 1, len(titles) - 1)]
    xp_for_current = int(50 * (level - 1) ** 2)
    xp_for_next = int(50 * level ** 2)
    return level, title, xp - xp_for_current, xp_for_next - xp_for_current


def render_achievements():
    uid = st.session_state["user_id"]

    st.markdown(
        "<h2 style='color:#00E676;'>🏅 Achievements & Badges</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Earn badges, build streaks, and level up your health journey!")
    st.write("---")

    stats = get_achievement_stats(uid)

    # Evaluate all badges
    results = []
    earned_count = 0
    for badge in BADGES:
        earned, progress, detail = badge["check"](stats)
        results.append({
            **badge,
            "earned": earned,
            "progress": progress,
            "detail": detail,
        })
        if earned:
            earned_count += 1

    # ── LEVEL & XP ──────────────────────────────────────
    level, title, current_xp, xp_needed = _compute_level(earned_count)

    l1, l2, l3 = st.columns([1, 2, 1])
    l1.markdown(
        f"<div style='text-align:center; padding:20px; background:#1e1e1e; "
        f"border-radius:15px; border:1px solid #FFD700;'>"
        f"<h1 style='color:#FFD700; margin:0;'>⭐ {level}</h1>"
        f"<p style='color:#FFD700; margin:0;'>{title}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with l2:
        st.markdown(
            f"<div style='padding:20px; background:#1e1e1e; "
            f"border-radius:15px; border:1px solid #333;'>"
            f"<h3 style='color:#00E676; margin:0;'>🏅 {earned_count} / {len(BADGES)} Badges Earned</h3>"
            f"<p style='color:#bbb; margin:5px 0;'>XP: {current_xp} / {xp_needed} to next level</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.progress(min(current_xp / max(xp_needed, 1), 1.0))

    l3.markdown(
        f"<div style='text-align:center; padding:20px; background:#1e1e1e; "
        f"border-radius:15px; border:1px solid #FF512F;'>"
        f"<h2 style='color:#FF512F; margin:0;'>🔥 {stats['streak']}</h2>"
        f"<p style='color:#FF512F; margin:0;'>Day Streak</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── QUICK STATS ─────────────────────────────────────
    st.write("---")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("📝 Food Logs", stats["total_entries"])
    s2.metric("📅 Active Days", stats["active_days"])
    s3.metric("💧 Hydration Goals", stats["hydration_perfect_days"])
    s4.metric("🏃 Workouts", stats["exercise_sessions"])
    s5.metric("⚖️ Weight Logs", stats["weight_logs"])

    # ── BADGE GRID BY CATEGORY ──────────────────────────
    st.write("---")

    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    for cat_name, cat_badges in categories.items():
        st.markdown(f"### {cat_name}")

        cols = st.columns(min(len(cat_badges), 4))
        for i, badge in enumerate(cat_badges):
            col = cols[i % 4]
            earned = badge["earned"]
            border_color = "#FFD700" if earned else "#333"
            opacity = "1.0" if earned else "0.5"
            check = "✅" if earned else ""

            col.markdown(
                f"<div style='text-align:center; padding:15px; background:#1e1e1e; "
                f"border-radius:12px; border:2px solid {border_color}; "
                f"opacity:{opacity}; margin-bottom:10px;'>"
                f"<p style='font-size:2rem; margin:0;'>{badge['emoji']}</p>"
                f"<h4 style='color:{'#FFD700' if earned else '#888'}; margin:5px 0;'>"
                f"{badge['name']} {check}</h4>"
                f"<p style='color:#888; margin:0; font-size:0.75rem;'>{badge['desc']}</p>"
                f"<p style='color:#aaa; margin:5px 0; font-size:0.8rem;'>{badge['detail']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if not earned:
                col.progress(badge["progress"])

        st.write("")
