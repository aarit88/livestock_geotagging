"""
Styles module — All custom CSS for the dark-themed Streamlit frontend.
"""


def get_css():
    """Return the complete custom CSS string for the app."""
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ─────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(145deg, #0a0e14 0%, #0d1220 40%, #0a0e14 100%);
}

/* ── Animated header ────────────────────────── */
.hero-header {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
    animation: fadeSlideDown 0.8s ease-out;
}
.hero-header h1 {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4ff, #7b2fef, #00d4ff);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 4s linear infinite;
    margin-bottom: 0.3rem;
}
.hero-header p {
    color: #8b9dc3;
    font-size: 1.05rem;
    font-weight: 300;
}

@keyframes shimmer {
    0% { background-position: 0% center; }
    100% { background-position: 200% center; }
}
@keyframes fadeSlideDown {
    from { opacity: 0; transform: translateY(-20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 8px rgba(0,212,255,0.3); }
    50%      { box-shadow: 0 0 22px rgba(0,212,255,0.6); }
}

/* ── Glass cards ─────────────────────────────── */
.glass-card {
    background: rgba(19, 25, 34, 0.65);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    animation: fadeIn 0.6s ease-out;
}
.glass-card h3 {
    color: #00d4ff;
    font-weight: 600;
    font-size: 1.15rem;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Metric cards ────────────────────────────── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}
.metric-card {
    flex: 1;
    background: linear-gradient(145deg, rgba(0,212,255,0.08), rgba(123,47,239,0.08));
    border: 1px solid rgba(0,212,255,0.15);
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    text-align: center;
    animation: fadeIn 0.7s ease-out;
}
.metric-card .label {
    color: #8b9dc3;
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 0.4rem;
}
.metric-card .value {
    color: #00d4ff;
    font-size: 1.55rem;
    font-weight: 700;
}

/* ── Object pills ────────────────────────────── */
.pill-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.6rem;
}
.pill {
    background: rgba(0,212,255,0.12);
    border: 1px solid rgba(0,212,255,0.25);
    color: #00d4ff;
    padding: 0.35rem 0.9rem;
    border-radius: 50px;
    font-size: 0.82rem;
    font-weight: 500;
    animation: fadeIn 0.5s ease-out;
    transition: all 0.2s;
}
.pill:hover {
    background: rgba(0,212,255,0.22);
    transform: translateY(-1px);
}

/* ── Scan button ─────────────────────────────── */
div.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #00d4ff 0%, #7b2fef 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    transition: all 0.3s ease !important;
    animation: pulse 2.5s infinite;
}
div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0,212,255,0.35) !important;
}
div.stButton > button:active {
    transform: scale(0.97) !important;
}

/* ── Sidebar ─────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1220 0%, #0a0e14 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    color: #00d4ff;
}

/* ── Selectbox styling ───────────────────────── */
div[data-baseweb="select"] {
    border-radius: 12px;
}

/* ── Status / spinner overrides ──────────────── */
.stSpinner > div {
    border-top-color: #00d4ff !important;
}

/* ── Hide streamlit footer ───────────────────── */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* ── Map container ───────────────────────────── */
.map-container {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(0,212,255,0.15);
    animation: fadeIn 0.8s ease-out;
}

/* ── Section divider ─────────────────────────── */
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,212,255,0.3), transparent);
    margin: 1.5rem 0;
}
</style>
"""
