import streamlit as st

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ─── GLOBAL DARK THEME ─── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0a0a12 0%, #0e1117 50%, #0a0a12 100%);
}

/* HIDE DEFAULT SIDEBAR ON AUTH */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c0c18 0%, #0e1117 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* ─── GLASS CARDS ─── */
.glass-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.02));
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    color: white;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

/* ─── FEATURE CARDS (HOME) ─── */
.feature-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.06);
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.feature-box:hover {
    transform: scale(1.04) translateY(-3px);
    border-color: #00E676;
    box-shadow: 0 8px 30px rgba(0, 230, 118, 0.15);
}

/* ─── METRICS ─── */
div[data-testid="stMetricValue"] {
    background: linear-gradient(135deg, #FFD700, #00E676);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
}

/* ─── BUTTONS ─── */
.stButton>button {
    background: linear-gradient(135deg, #FF512F 0%, #DD2476 100%);
    color: white;
    border-radius: 12px;
    border: none;
    height: 48px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.3px;
    transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    box-shadow: 0 4px 15px rgba(221, 36, 118, 0.2);
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(221, 36, 118, 0.35);
}
.stButton>button:active {
    transform: translateY(0);
}

/* ─── PRIMARY BUTTON OVERRIDE ─── */
button[kind="primary"] {
    background: linear-gradient(135deg, #FF512F 0%, #DD2476 100%) !important;
}

/* ─── TABS ─── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(255,255,255,0.03);
    border-radius: 14px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 0.85rem;
    color: #888;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #FF512F, #DD2476) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(221, 36, 118, 0.25);
}

/* ─── INPUTS ─── */
input, textarea, [data-baseweb="input"], [data-baseweb="textarea"] {
    border-radius: 12px !important;
}

/* ─── EXPANDERS ─── */
details {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    background: rgba(255,255,255,0.02) !important;
}

/* ─── ONBOARDING ─── */
.onboarding-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem 1rem;
}
.onboarding-header {
    text-align: center;
    margin-bottom: 2rem;
}
.onboarding-header h1 {
    color: #00E676;
    font-size: 2.8rem;
    margin-bottom: 0.2rem;
    font-weight: 900;
    letter-spacing: -1px;
}
.onboarding-header p { color: #888; font-size: 1rem; }

.step-progress {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 2rem;
}
.step-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    background: #333;
    transition: all 0.3s;
}
.step-dot.active { background: #00E676; transform: scale(1.3); }
.step-dot.done { background: #00E676; opacity: 0.5; }

.step-label {
    text-align: center;
    color: #00E676;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    letter-spacing: 0.5px;
}
.step-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
}
.step-emoji { font-size: 2.5rem; text-align: center; margin-bottom: 0.5rem; }
.step-title { text-align: center; font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem; }
.step-subtitle { text-align: center; color: #aaa; font-size: 0.95rem; margin-bottom: 1.5rem; }

/* ─── TOP NAV BAR ─── */
.topnav {
    display: flex;
    justify-content: center;
    gap: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 6px;
    margin-bottom: 1.5rem;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
}
.topnav-item {
    flex: 1;
    text-align: center;
    padding: 10px 8px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    color: #888;
    font-size: 0.85rem;
    font-weight: 600;
    text-decoration: none;
}
.topnav-item:hover { background: rgba(255,255,255,0.06); color: #fff; }
.topnav-item.active {
    background: linear-gradient(90deg, #FF512F, #DD2476);
    color: #fff;
    box-shadow: 0 4px 15px rgba(221, 36, 118, 0.3);
}
.topnav-icon { font-size: 1.3rem; display: block; margin-bottom: 2px; }

/* ─── SMART LOG BAR ─── */
.smart-log-bar {
    background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
    backdrop-filter: blur(8px);
}

/* ─── GOAL PROGRESS ─── */
.goal-progress-container {
    background: linear-gradient(135deg, rgba(0,230,118,0.06), rgba(0,230,118,0.01));
    border: 1px solid rgba(0,230,118,0.12);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(8px);
}
.progress-bar-outer {
    background: rgba(255,255,255,0.06);
    border-radius: 12px;
    height: 24px;
    overflow: hidden;
    margin: 8px 0;
}
.progress-bar-fill {
    height: 100%;
    border-radius: 12px;
    transition: width 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    background: linear-gradient(90deg, #00E676, #00BCD4);
    box-shadow: 0 0 12px rgba(0, 230, 118, 0.3);
}
.progress-bar-fill.warn {
    background: linear-gradient(90deg, #FF9800, #FF5722);
    box-shadow: 0 0 12px rgba(255, 152, 0, 0.3);
}
.progress-bar-fill.over {
    background: linear-gradient(90deg, #F44336, #D32F2F);
    box-shadow: 0 0 12px rgba(244, 67, 54, 0.3);
}

/* ─── TODAY CARDS ─── */
.today-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 1.2rem;
    text-align: center;
    transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    height: 100%;
    backdrop-filter: blur(6px);
}
.today-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0,230,118,0.25);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}
.today-card-icon { font-size: 2rem; margin-bottom: 0.3rem; }
.today-card-label {
    color: #666;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.today-card-value {
    color: #fff;
    font-size: 1.8rem;
    font-weight: 900;
    line-height: 1.2;
}
.today-card-sub { color: #888; font-size: 0.78rem; }

/* ─── AI RECOMMENDATION CARD ─── */
.ai-card {
    background: linear-gradient(135deg, rgba(103,58,183,0.12), rgba(33,150,243,0.08));
    border: 1px solid rgba(103,58,183,0.18);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    transition: all 0.2s;
    backdrop-filter: blur(6px);
}
.ai-card:hover {
    border-color: rgba(103,58,183,0.3);
    transform: translateX(3px);
}
.ai-card-title { font-weight: 700; color: #BB86FC; margin-bottom: 0.3rem; font-size: 0.95rem; }
.ai-card-text { color: #ccc; font-size: 0.88rem; line-height: 1.5; }

/* ─── SECTION HEADER ─── */
.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    margin: 1.5rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    letter-spacing: -0.3px;
}

/* ─── AUTH PAGE ─── */
.auth-container {
    max-width: 450px;
    margin: 0 auto;
    padding: 2rem;
}
.auth-brand {
    text-align: center;
    padding: 2rem 0 1.5rem 0;
}
.auth-brand h1 {
    font-size: 3rem;
    font-weight: 900;
    margin: 0;
    background: linear-gradient(135deg, #00E676, #00BCD4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1.5px;
}
.auth-brand p {
    color: #666;
    font-size: 1rem;
    margin-top: 0.3rem;
}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.1);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* ─── ANIMATIONS ─── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in {
    animation: fadeInUp 0.4s ease-out;
}

/* ─── STAT BADGE ─── */
.stat-badge {
    display: inline-block;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 6px 14px;
    font-size: 0.82rem;
    color: #ccc;
    font-weight: 600;
}
</style>
"""


def inject_css():
    st.markdown(APP_CSS, unsafe_allow_html=True)
