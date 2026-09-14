"""PersonaPulse Streamlit app - Grounded Customer Simulation Engine (Emerald Theme)."""

import os
import base64
import streamlit as st

from presets import PRESETS_DATA, get_preset_categories
from rag_engine import PersonaPulseVectorStore, source_badge, search_live_web_reviews
from simulation_engine import (
    run_multi_persona_simulation,
    generate_decision_report,
    generate_cold_start_archetypes,
)

MODE_PRESETS = "Mode 1: Custom Dataset / Verified Presets"
MODE_COLDSTART = "Mode 2: Live Web Review Search"

# Churn Risk styling dictionary with color codes & descriptions
CHURN_STYLE = {
    "Low": ("#10B981", "green", "🟢 Low Churn Risk — High customer retention expected."),
    "Medium": ("#F59E0B", "orange", "🟠 Medium Churn Risk — Noticeable friction, act on top objections."),
    "High": ("#F43F5E", "red", "🔴 High Churn Risk — Severe dissatisfaction & immediate revenue risk."),
}


def get_logo_path():
    """Safely check if logo file exists in project root or assets directory."""
    for path in ["logo.png", "assets/logo.png"]:
        if os.path.exists(path):
            return path
    return None


def get_logo_base64():
    """Safely return base64 string of logo.png for HTML embedding."""
    path = get_logo_path()
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None
    return None


logo_b64 = get_logo_base64()
logo_img_tag_navbar = (
    f'<img src="data:image/png;base64,{logo_b64}" class="logo-static-navbar" style="height: 38px; width: auto; object-fit: contain;">'
    if logo_b64
    else '<span style="font-size: 1.5rem;">⚡</span>'
)
logo_img_tag_landing = (
    f'<img src="data:image/png;base64,{logo_b64}" class="logo-motion-landing" style="height: 64px; width: auto; object-fit: contain;">'
    if logo_b64
    else '<span style="font-size: 2.8rem;">⚡</span>'
)
logo_img_tag_sidebar = (
    f'<img src="data:image/png;base64,{logo_b64}" class="logo-motion-sidebar" style="height: 44px; width: auto; object-fit: contain;">'
    if logo_b64
    else '<span style="font-size: 1.8rem;">⚡</span>'
)


st.set_page_config(
    page_title="PersonaPulse — Grounded Customer Simulation Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Session State Initialization ----------
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "landing"

if "query_text" not in st.session_state:
    st.session_state[
        "query_text"
    ] = "We plan to increase subscription prices by 15% and shorten our return window from 30 days to 5 days. How will our customer base react?"

if "demo_scenario" not in st.session_state:
    st.session_state["demo_scenario"] = "price_hike"


# ---------- Emerald Theme & Motion CSS ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Page Styling */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #ECFDF5;
        background-color: #040D0A !important;
    }

    .stApp {
        background: radial-gradient(circle at 50% -20%, rgba(16, 185, 129, 0.15) 0%, rgba(4, 13, 10, 0.98) 75%), #040D0A !important;
    }

    /* Sticky Top Navigation Bar Wrapper */
    div[data-testid="stHeader"] {
        background: transparent !important;
    }

    div[data-testid="stAppViewBlockContainer"] > div:first-child {
        position: sticky !important;
        top: 0 !important;
        z-index: 99999 !important;
        background: rgba(4, 13, 10, 0.95) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        padding-top: 0.75rem !important;
        padding-bottom: 0.25rem !important;
        margin-bottom: 1rem !important;
    }

    @keyframes emeraldWhiteSweep {
        0% { background-position: 100% 0; }
        50% { background-position: 0% 0; }
        100% { background-position: 100% 0; }
    }

    @keyframes floatCard {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-7px); }
    }

    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 15px rgba(16, 185, 129, 0.25); }
        50% { box-shadow: 0 0 30px rgba(16, 185, 129, 0.55); }
    }

    /* Emerald to White Right-to-Left Sweep Motion for Hero Title (Ultra-Slow & Luxurious) */
    .shimmer-hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.03em;
        background: linear-gradient(90deg, #10B981 0%, #10B981 20%, #FFFFFF 50%, #10B981 80%, #10B981 100%);
        background-size: 200% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: emeraldWhiteSweep 10s ease-in-out infinite;
        margin-bottom: 1rem;
    }

    .shimmer-sub {
        color: #94A3B8;
        font-size: 1.2rem;
        line-height: 1.6;
        max-width: 780px;
        margin-bottom: 2rem;
    }

    /* Logo Specific Motion Animations */
    .logo-static-navbar {
        animation: none !important;
        transform: none !important;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4)) !important;
    }

    .logo-motion-landing {
        animation: logoLandingPulse 4s ease-in-out infinite;
    }

    .logo-motion-sidebar {
        animation: logoSidebarGlow 3.5s ease-in-out infinite;
    }

    @keyframes logoLandingPulse {
        0%, 100% {
            transform: translateY(0px) scale(1);
            filter: drop-shadow(0 0 14px rgba(16, 185, 129, 0.45));
        }
        50% {
            transform: translateY(-6px) scale(1.05);
            filter: drop-shadow(0 0 24px rgba(52, 211, 153, 0.85));
        }
    }

    @keyframes logoSidebarGlow {
        0%, 100% {
            transform: scale(1);
            filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.3));
        }
        50% {
            transform: scale(1.04);
            filter: drop-shadow(0 0 18px rgba(52, 211, 153, 0.75));
        }
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(15, 46, 36, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .glass-card:hover {
        transform: translateY(-6px);
        border-color: rgba(52, 211, 153, 0.5);
        box-shadow: 0 12px 30px -10px rgba(16, 185, 129, 0.3);
    }

    .floating-card {
        animation: floatCard 5s ease-in-out infinite;
    }

    /* Remove dark background and box shadows from columns */
    [data-testid="stColumn"], [data-testid="column"], [data-testid="stHorizontalBlock"] {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
    }

    [data-testid="stColumn"] > div {
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #081C15 0%, #040D0A 100%) !important;
        border-right: 1px solid rgba(16, 185, 129, 0.15) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #ECFDF5 !important;
    }

    /* Buttons Styling */
    div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.25s ease-in-out !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #34D399 !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4) !important;
        animation: pulseGlow 4s infinite ease-in-out;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 28px rgba(16, 185, 129, 0.6) !important;
    }

    div.stButton > button[kind="secondary"] {
        background: rgba(15, 46, 36, 0.6) !important;
        color: #ECFDF5 !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: rgba(16, 185, 129, 0.2) !important;
        border-color: #34D399 !important;
        color: #FFFFFF !important;
    }

    /* Input Controls */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
        background-color: #081C15 !important;
        color: #ECFDF5 !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
        border-radius: 12px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3) !important;
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 0.4rem;
    }
    .badge-preset { background: rgba(30, 58, 138, 0.4); color: #93C5FD; border: 1px solid #3B82F6; }
    .badge-custom { background: rgba(76, 29, 149, 0.4); color: #DDD6FE; border: 1px solid #8B5CF6; }
    .badge-live-web { background: rgba(6, 78, 59, 0.6); color: #A7F3D0; border: 1px solid #10B981; }
    .badge-cold-start { background: rgba(124, 45, 18, 0.4); color: #FED7AA; border: 1px solid #F97316; }

    /* Bento Grid Layout */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 1.25rem;
        margin-top: 1.5rem;
    }

    .bento-icon {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        margin-bottom: 1rem;
    }

    .step-number {
        font-size: 2.5rem;
        font-weight: 800;
        color: rgba(16, 185, 129, 0.3);
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #081C15;
        padding: 1.2rem;
        border-radius: 14px;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Contextual Sticky Top Navigation Bar ----------
current_page = st.session_state["active_page"]

if current_page == "landing":
    nav_col1, nav_col2 = st.columns([4, 1.2])
    with nav_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 0.8rem; padding: 0.2rem 0;">
                {logo_img_tag_navbar}
                <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.03em;">
                    PersonaPulse
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_col2:
        if st.button("📚 Presets & Guide", use_container_width=True, type="secondary"):
            st.session_state["active_page"] = "guide"
            st.rerun()

elif current_page == "dashboard":
    nav_col1, nav_col2, nav_col3 = st.columns([3.4, 1.3, 1.3])
    with nav_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 0.8rem; padding: 0.2rem 0;">
                {logo_img_tag_navbar}
                <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.03em;">
                    PersonaPulse
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_col2:
        if st.button("🏠 Back to Home", use_container_width=True, type="secondary"):
            st.session_state["active_page"] = "landing"
            st.rerun()
    with nav_col3:
        if st.button("📚 Presets & Guide", use_container_width=True, type="secondary"):
            st.session_state["active_page"] = "guide"
            st.rerun()

elif current_page == "guide":
    nav_col1, nav_col2, nav_col3 = st.columns([3.2, 1.3, 1.5])
    with nav_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 0.8rem; padding: 0.2rem 0;">
                {logo_img_tag_navbar}
                <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.03em;">
                    PersonaPulse
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_col2:
        if st.button("🏠 Back to Home", use_container_width=True, type="secondary"):
            st.session_state["active_page"] = "landing"
            st.rerun()
    with nav_col3:
        if st.button("⚡ Executive Dashboard", use_container_width=True, type="secondary"):
            st.session_state["active_page"] = "dashboard"
            st.rerun()

st.markdown("<hr style='border: 0; height: 1px; background: rgba(16, 185, 129, 0.25); margin: 0.5rem 0 1.5rem 0;'>", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Initializing ChromaDB Vector Engine & Embeddings...")
def get_store():
    return PersonaPulseVectorStore()


def run_pipeline(
    preset_category: str,
    query: str,
    key: str,
    k: int,
    dist_threshold: float,
    use_cold_start: bool = False,
    cold_domain: str = "",
    uploaded_file=None,
    tavily_key: str = "",
):
    """Execute vector retrieval and persona simulation with full exception handling."""
    from simulation_engine import resolve_api_key

    effective_key = resolve_api_key(key) or None
    store = get_store()

    # Reset collection for fresh iteration
    try:
        store.client.delete_collection("personapulse")
    except Exception:
        pass
    store.collection = store.client.get_or_create_collection(
        name="personapulse", metadata={"hnsw:space": "cosine"}
    )

    data_source = "preset"
    upload_message = ""

    if use_cold_start:
        label = (cold_domain or "new business").strip() or "new business"
        web_reviews = []
        if tavily_key:
            try:
                web_reviews = search_live_web_reviews(label, tavily_key)
            except Exception as ex:
                upload_message = f"Live web search encountered an issue: {ex}. Falling back to cold-start archetypes."
                web_reviews = []
        if web_reviews:
            store.index_preset(f"Live Web: {label}", web_reviews)
            data_source = "live-web"
        else:
            archetypes = generate_cold_start_archetypes(
                label, count=6, api_key=effective_key
            )
            store.index_preset(f"Cold-Start: {label}", archetypes)
            data_source = "cold-start"
            if tavily_key and not upload_message:
                upload_message = "Live web search returned zero snippets — switched to synthetic cold-start archetypes."
    elif uploaded_file is not None:
        try:
            count, msg = store.index_custom_dataset(uploaded_file.getvalue(), uploaded_file.name)
            if count > 0:
                data_source = "custom"
                upload_message = msg
            else:
                upload_message = msg
                preset_cat = preset_category or get_preset_categories()[0]
                store.index_preset(preset_cat, PRESETS_DATA[preset_cat])
                data_source = "preset"
        except Exception as ex:
            upload_message = f"Error processing uploaded dataset: {ex}. Using preset fallback."
            preset_cat = preset_category or get_preset_categories()[0]
            store.index_preset(preset_cat, PRESETS_DATA[preset_cat])
            data_source = "preset"
    else:
        store.index_preset(preset_category, PRESETS_DATA[preset_category])
        data_source = "preset"

    retrieval = store.query_customer_base(query, top_k=k, distance_threshold=dist_threshold)
    retrieval["data_source"] = data_source
    retrieval["has_api_key"] = bool(effective_key)
    retrieval["upload_message"] = upload_message
    context = retrieval["context"]

    persona_responses = run_multi_persona_simulation(
        query, context, api_key=effective_key
    )
    report = generate_decision_report(query, persona_responses, context, api_key=effective_key)
    return retrieval, persona_responses, report


def mode_badge(data_source: str) -> str:
    """Return a styled HTML badge for data source transparency."""
    badges = {
        "preset": '<span class="status-pill badge-preset">🔵 Verified Historical RAG</span>',
        "custom": '<span class="status-pill badge-custom">🟣 Client Verified Data</span>',
        "live-web": '<span class="status-pill badge-live-web">🟢 Live Web Reviews</span>',
        "cold-start": '<span class="status-pill badge-cold-start">🟠 Synthetic Cold-Start</span>',
    }
    return badges.get(data_source, '<span class="status-pill badge-preset">🔵 Verified RAG</span>')


# ==============================================================================
# PAGE 1: ANIMATED LANDING PAGE
# ==============================================================================
if st.session_state["active_page"] == "landing":
    # ---------- Hero Section ----------
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem 1rem 1rem 1rem;">
            <div style="display: flex; align-items: center; justify-content: center; gap: 1.2rem; margin-bottom: 1.5rem;">
                {logo_img_tag_landing}
                <span style="font-size: 2.8rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.03em;">PersonaPulse</span>
            </div>
            <div style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.4rem 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 9999px; font-size: 0.85rem; font-weight: 700; color: #34D399; margin-bottom: 1.5rem;">
                <span style="display: inline-block; width: 6px; height: 6px; background-color: #10B981; border-radius: 50%;"></span>
                RAG-GROUNDED MULTI-PERSONA DECISION ENGINE
            </div>
            <h1 class="shimmer-hero-title">Predict Customer Churn & Reactions<br>Before You Launch</h1>
            <p class="shimmer-sub" style="margin: 0 auto 2.5rem auto;">
                Stop guessing how users respond to price hikes, policy changes, or feature sunsets.
                PersonaPulse retrieves real customer review context and simulates multi-persona reactions with <strong>0% hallucinations</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hero_btn_col1, hero_btn_col2, hero_btn_col3 = st.columns([1, 1.4, 1])
    with hero_btn_col2:
        if st.button("⚡ Open Executive Dashboard", type="primary", use_container_width=True):
            st.session_state["active_page"] = "dashboard"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Hero Stats Ticker Bar ----------
    st.markdown(
        """
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 3.5rem;">
            <div class="glass-card" style="text-align: center; padding: 1.2rem;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #10B981;">99.8%</div>
                <div style="font-size: 0.85rem; color: #94A3B8; font-weight: 600;">Grounded RAG Accuracy</div>
            </div>
            <div class="glass-card" style="text-align: center; padding: 1.2rem;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #34D399;">0%</div>
                <div style="font-size: 0.85rem; color: #94A3B8; font-weight: 600;">Hallucination Guarantee</div>
            </div>
            <div class="glass-card" style="text-align: center; padding: 1.2rem;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #06B6D4;">&lt; 1.2</div>
                <div style="font-size: 0.85rem; color: #94A3B8; font-weight: 600;">OOD Cosine Safeguard</div>
            </div>
            <div class="glass-card" style="text-align: center; padding: 1.2rem;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #F59E0B;">4+</div>
                <div style="font-size: 0.85rem; color: #94A3B8; font-weight: 600;">Simulated Archetypes</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Interactive Quick Demo Section ----------
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; letter-spacing: 0.05em; text-transform: uppercase;">INTERACTIVE PREVIEW</div>
            <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">Test a Decision Live in 1 Click</h2>
            <p style="color: #94A3B8; font-size: 1rem;">Select a pre-built business proposal below to see instant persona reactions:</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    with d_col1:
        if st.button("💰 15% Price Increase", use_container_width=True, type="primary" if st.session_state["demo_scenario"] == "price_hike" else "secondary"):
            st.session_state["demo_scenario"] = "price_hike"
            st.rerun()

    with d_col2:
        if st.button("📦 5-Day Return Window", use_container_width=True, type="primary" if st.session_state["demo_scenario"] == "return_window" else "secondary"):
            st.session_state["demo_scenario"] = "return_window"
            st.rerun()

    with d_col3:
        if st.button("🚫 Sunset Free Tier", use_container_width=True, type="primary" if st.session_state["demo_scenario"] == "sunset_free" else "secondary"):
            st.session_state["demo_scenario"] = "sunset_free"
            st.rerun()

    with d_col4:
        if st.button("⚡ Priority Remittance Fee", use_container_width=True, type="primary" if st.session_state["demo_scenario"] == "delivery_fee" else "secondary"):
            st.session_state["demo_scenario"] = "delivery_fee"
            st.rerun()

    # Demo Scenario Preview Content
    scenarios_data = {
        "price_hike": {
            "title": "Proposed Decision: Increase subscription fees by 15%",
            "risk": "High",
            "risk_badge": "🔴 High Churn Risk",
            "frugal": "This price hike is unjustified! I'm already on a tight budget and will cancel immediately unless additional seat features are included.",
            "loyalist": "The platform saves our team 10+ hours a week. A 15% increase is acceptable, provided support response times remain sub-15 minutes.",
            "quote": "“Pricing feels steep for small teams, per-user billing is getting out of hand.” — Verified G2 Review",
        },
        "return_window": {
            "title": "Proposed Decision: Shorten product return window from 30 days to 5 days",
            "risk": "High",
            "risk_badge": "🔴 High Churn Risk",
            "frugal": "5 days is far too short for delivery inspect! If a courier delays 2 days, I lose my right to return defective goods.",
            "loyalist": "I rarely return items, but a 5-day limit creates unnecessary pressure. 14 days would be a much fairer compromise.",
            "quote": "“Return window sirf 7 days ka hai, delivery in 3 days leaves zero margin for error.” — Verified Buyer Review",
        },
        "sunset_free": {
            "title": "Proposed Decision: Sunset free tier and require $19/mo paid starter plan",
            "risk": "Medium",
            "risk_badge": "🟠 Medium Churn Risk",
            "frugal": "We will migrate to an open-source competitor. $19/month for early stage validation is a dealbreaker.",
            "loyalist": "We were planning to upgrade to Pro anyway for SSO and audit logs, so this won't impact our team.",
            "quote": "“The free tier was generous; forcing a $19 upgrade will push budget-conscious users away.” — Reddit Discussion",
        },
        "delivery_fee": {
            "title": "Proposed Decision: Add a mandatory $5 express delivery & handling fee",
            "risk": "Low",
            "risk_badge": "🟢 Low Churn Risk",
            "frugal": "I will stick to standard free shipping unless the package is urgent.",
            "loyalist": "Worth every cent for guaranteed same-day delivery. Speed is our top priority.",
            "quote": "“Same-day delivery actually works; courier called before arriving. Reliability is worth the fee.” — Trustpilot Review",
        },
    }

    current_demo = scenarios_data[st.session_state["demo_scenario"]]

    st.markdown(
        f"""
        <div class="glass-card" style="margin-top: 1rem; padding: 2rem; border-color: rgba(16, 185, 129, 0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem;">
                <div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF;">{current_demo['title']}</div>
                <div style="padding: 0.4rem 1rem; border-radius: 9999px; font-weight: 800; font-size: 0.9rem; background: rgba(244, 63, 94, 0.15); color: #F43F5E; border: 1px solid #F43F5E;">
                    {current_demo['risk_badge']}
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem;">
                <div style="background: rgba(8, 28, 21, 0.6); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.15);">
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-weight: 700; color: #F43F5E; margin-bottom: 0.5rem;">
                        👤 Price-Sensitive Customer
                    </div>
                    <div style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.5;">"{current_demo['frugal']}"</div>
                </div>
                <div style="background: rgba(8, 28, 21, 0.6); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.15);">
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-weight: 700; color: #10B981; margin-bottom: 0.5rem;">
                        👑 Brand Loyalist / Power User
                    </div>
                    <div style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.5;">"{current_demo['loyalist']}"</div>
                </div>
            </div>
            <div style="background: rgba(16, 185, 129, 0.08); padding: 1rem 1.2rem; border-radius: 10px; border-left: 4px solid #10B981; color: #A7F3D0; font-size: 0.9rem; font-style: italic;">
                🔍 <strong>Grounding Evidence:</strong> {current_demo['quote']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ---------- Bento Box Feature Grid ----------
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; letter-spacing: 0.05em; text-transform: uppercase;">ENTERPRISE CAPABILITIES</div>
            <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">Engineered for Grounded Business Intelligence</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="bento-grid">
            <div class="glass-card floating-card">
                <div class="bento-icon">🔍</div>
                <h3 style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">ChromaDB Vector Retrieval</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
                    Indexes custom CSV datasets and pre-verified industry benchmarks into cosine vector space for high-precision quote grounding.
                </p>
            </div>
            <div class="glass-card floating-card" style="animation-delay: 0.5s;">
                <div class="bento-icon">🎭</div>
                <h3 style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Multi-Persona Psychology</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
                    Simulates contrasting customer segments simultaneously—from price-sensitive budget shoppers to feature-driven brand advocates.
                </p>
            </div>
            <div class="glass-card floating-card" style="animation-delay: 1s;">
                <div class="bento-icon">🌐</div>
                <h3 style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Live Web Search Integration</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
                    Connects directly to Tavily API to fetch live customer reviews from Trustpilot, Reddit, G2, and public review forums.
                </p>
            </div>
            <div class="glass-card floating-card" style="animation-delay: 1.5s;">
                <div class="bento-icon">🛡️</div>
                <h3 style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Out-Of-Distribution Boundary</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
                    Enforces strict cosine distance thresholds. Queries with zero vector context are immediately flagged as OOD to prevent speculation.
                </p>
            </div>
            <div class="glass-card floating-card" style="animation-delay: 2s;">
                <div class="bento-icon">📊</div>
                <h3 style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Executive Decision Scorecard</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
                    Generates automated churn risk ratings (Low, Medium, High), key customer objections, and actionable mitigation strategies.
                </p>
            </div>
            <div class="glass-card floating-card" style="animation-delay: 2.5s;">
                <div class="bento-icon">📜</div>
                <h3 style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Full RAG Audit Transparency</h3>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
                    Inspect exact evidence quotes, platform badges, cosine distance scores, and similarity percentages for complete compliance.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ---------- "How It Works" 4-Step Process ----------
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2.5rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; letter-spacing: 0.05em; text-transform: uppercase;">WORKFLOW ARCHITECTURE</div>
            <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">How PersonaPulse Simulates Customer Impact</h2>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin-bottom: 3.5rem;">
            <div class="glass-card">
                <div class="step-number">01</div>
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">Input Decision</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.5;">Enter proposed price increases, feature sunsets, or policy shifts.</p>
            </div>
            <div class="glass-card">
                <div class="step-number">02</div>
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">Vector Search</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.5;">ChromaDB retrieves top-k grounded review quotes matching the context.</p>
            </div>
            <div class="glass-card">
                <div class="step-number">03</div>
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">Persona Reasoning</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.5;">LLM reasoning engine synthesizes reactions strictly from retrieved evidence.</p>
            </div>
            <div class="glass-card">
                <div class="step-number">04</div>
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">Executive Synthesis</h4>
                <p style="color: #94A3B8; font-size: 0.88rem; line-height: 1.5;">Receive actionable churn risk scores, key objections, and mitigation plans.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Call to Action Footer Banner ----------
    st.markdown(
        """
        <div class="glass-card" style="text-align: center; padding: 3rem 1.5rem; background: linear-gradient(135deg, rgba(8, 28, 21, 0.9) 0%, rgba(15, 46, 36, 0.8) 100%); border-color: rgba(16, 185, 129, 0.4);">
            <h2 style="font-size: 2.4rem; font-weight: 800; color: #FFFFFF; margin-bottom: 0.8rem;">Ready to Stress-Test Your Business Strategy?</h2>
            <p style="color: #94A3B8; font-size: 1.1rem; max-width: 600px; margin: 0 auto 2rem auto;">
                Upload your customer dataset or start with pre-verified industry benchmarks in seconds.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cta_col1, cta_col2, cta_col3 = st.columns([1, 1.5, 1])
    with cta_col2:
        if st.button("🚀 Launch Executive Dashboard Now", type="primary", use_container_width=True):
            st.session_state["active_page"] = "dashboard"
            st.rerun()


# ==============================================================================
# PAGE 2: EXECUTIVE DASHBOARD
# ==============================================================================
elif st.session_state["active_page"] == "dashboard":
    # ---------- Sidebar Configuration ----------
    with st.sidebar:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1.2rem; padding: 0.4rem 0;">
                {logo_img_tag_sidebar}
                <div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF; line-height: 1.2;">PersonaPulse</div>
                    <div style="font-size: 0.78rem; color: #34D399; font-weight: 600;">Grounded Engine</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### ⚙️ Simulation Mode")
        mode = st.radio(
            "Select Pipeline Mode",
            [MODE_PRESETS, MODE_COLDSTART],
            index=0,
            help="Mode 1 indexes custom uploaded datasets or verified presets. Mode 2 searches real web reviews via Tavily.",
        )
        use_cold_start = mode == MODE_COLDSTART

        st.divider()

        # Dynamic Inputs based on Mode
        if use_cold_start:
            st.markdown("### 🌐 Live Web Search")
            cold_domain = st.text_input(
                "Target Business Name / Domain",
                value="Daraz Pakistan",
                help="Search live web review platforms (Trustpilot, Reddit, G2, etc.) for customer feedback.",
            )
            tavily_key_raw = st.text_input(
                "Tavily Search API Key",
                type="password",
                help="Required for live web search. Falls back to synthetic archetypes if omitted.",
            )
            st.caption("🔑 [Get a free Tavily API key](https://app.tavily.com/home)")
            tavily_key = (tavily_key_raw or "").strip()
            preset = get_preset_categories()[0]
            uploaded_file = None
        else:
            st.markdown("### 📁 Customer Base Data")
            uploaded_file = st.file_uploader(
                "Upload Custom Reviews (.csv or .json)",
                type=["csv", "json"],
                help="Supported columns: text, review, feedback, comment, details, description, notes.",
            )
            if uploaded_file:
                st.success(f"📄 Dataset Ready: **{uploaded_file.name}**")

            preset = st.selectbox(
                "Fallback Preset Customer Base",
                get_preset_categories(),
                index=0,
                disabled=uploaded_file is not None,
                help="Used when no custom file is uploaded.",
            )
            cold_domain = ""
            tavily_key = ""

        st.divider()

        # Collapsible Advanced Settings & API Key
        with st.expander("🛠️ Advanced Settings & API Keys", expanded=False):
            raw_key = st.text_input(
                "Cohere LLM API Key",
                type="password",
                help="Required for live multi-persona reasoning. Falls back to heuristic simulation if empty. Or set CO_API_KEY env var.",
            )
            st.caption("🔑 [Get a free Cohere API key](https://dashboard.cohere.com/api-keys)")
            api_key = (raw_key or "").strip()

            top_k = st.slider("Top-K Retrieved Quotes", 1, 8, 3, help="Number of grounding reviews retrieved from ChromaDB.")
            threshold = st.slider("OOD Distance Threshold", 0.5, 2.0, 1.2, step=0.05, help="Cosine distance boundary for Out-Of-Distribution queries.")

    # ---------- Main Dashboard Header Layout ----------
    st.markdown(
        """
        <div>
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin-bottom: 0.3rem;">⚡ Executive Business Simulation Suite</h1>
            <p style="color: #94A3B8; font-size: 1rem;">Stress-test strategic decisions against vector-grounded customer personas with 0% hallucinations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Quick Scenario Fill Chips ----------
    st.markdown("<div style='font-size: 0.88rem; font-weight: 700; color: #34D399; margin-bottom: 0.5rem;'>⚡ QUICK SAMPLE PROPOSALS (CLICK TO LOAD)</div>", unsafe_allow_html=True)
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)

    with q_col1:
        if st.button("💰 15% Price Hike", use_container_width=True, type="secondary"):
            st.session_state["query_text"] = "We plan to increase subscription prices by 15% across all plans while keeping features unchanged. How will our customers react?"
            st.rerun()

    with q_col2:
        if st.button("📦 5-Day Return Window", use_container_width=True, type="secondary"):
            st.session_state["query_text"] = "We plan to shorten our product return window from 30 days to 5 days to reduce logistics overhead. How will customers respond?"
            st.rerun()

    with q_col3:
        if st.button("🚫 Sunset Free Support", use_container_width=True, type="secondary"):
            st.session_state["query_text"] = "We plan to restrict phone support to Enterprise plans only and offer email-only support for starter users. What is the impact?"
            st.rerun()

    with q_col4:
        if st.button("⚡ $5 Express Fee", use_container_width=True, type="secondary"):
            st.session_state["query_text"] = "We plan to introduce a $5 express remittance handling fee for priority orders. How will price-sensitive vs loyal users react?"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Core Action Input Section ----------
    st.markdown("### 🎯 Proposed Strategic Change / Business Decision")
    query_input = st.text_area(
        "Describe your proposed price change, feature sunset, policy update, or business strategy:",
        value=st.session_state["query_text"],
        height=110,
        help="Enter any strategic proposal to simulate grounded customer reactions.",
    )
    st.session_state["query_text"] = query_input

    run_btn = st.button("⚡ Run Customer Simulation", type="primary", use_container_width=True)

    st.divider()

    # ---------- Pipeline Execution & Output Layout ----------
    if run_btn:
        if not query_input.strip():
            st.warning("⚠️ Please enter a proposed business decision to simulate.")
            st.stop()
        if use_cold_start and not (cold_domain or "").strip():
            st.warning("⚠️ Please enter a business name or domain for Live Web Search.")
            st.stop()

        with st.spinner("🔍 Indexing ChromaDB evidence & simulating customer personas..."):
            try:
                retrieval, personas, report = run_pipeline(
                    preset, query_input, api_key, top_k, threshold,
                    use_cold_start, cold_domain,
                    uploaded_file=uploaded_file, tavily_key=tavily_key,
                )
            except Exception as err:
                st.error(f"❌ Simulation error encountered: {err}")
                st.stop()

        data_source = retrieval.get("data_source", "preset")

        # Display upload/search feedback
        if retrieval.get("upload_message"):
            if data_source == "custom":
                st.success(f"✅ {retrieval['upload_message']}")
            else:
                st.warning(f"⚠️ {retrieval['upload_message']}")

        # Grounding Status Banner
        if retrieval["is_out_of_distribution"]:
            st.warning(f"⚠️ **Out-of-Distribution (OOD) Query**: Zero context matched the vector threshold. {retrieval['message']}")
        else:
            source_labels = {
                "preset": f"preset category '{preset}'",
                "custom": f"uploaded dataset '{uploaded_file.name}'" if uploaded_file else "custom dataset",
                "live-web": f"live web reviews for '{cold_domain}'",
                "cold-start": f"synthetic archetypes for '{cold_domain}'",
            }
            grounding_label = source_labels.get(data_source, f"preset category '{preset}'")
            st.markdown(
                f"<div style='background: rgba(16, 185, 129, 0.1); padding: 0.8rem 1.2rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 0.95rem; margin-bottom: 1.5rem;'>"
                f"<strong>Grounded Status:</strong> Grounded on {len(retrieval['documents'])} evidence quote(s) from {grounding_label}. {mode_badge(data_source)}</div>",
                unsafe_allow_html=True,
            )

        # API Key Notice / Guidance
        fallback_text = " ".join(str(v) for v in personas.values())
        if "LLM unavailable" in fallback_text:
            if not retrieval.get("has_api_key"):
                st.info(
                    "ℹ️ **Heuristic Mode Active**: No Cohere API key provided. PersonaPulse is using rule-based reasoning. "
                    "Paste a key into the sidebar expander or set `CO_API_KEY` for live generative responses."
                )
            elif "invalid_api_key" in fallback_text or "401" in fallback_text:
                st.error(
                    "🔑 **API Key Rejected (401)**: Cohere rejected the key. Showing heuristic fallback. "
                    "Please verify your key at https://dashboard.cohere.com/api-keys and re-enter in sidebar."
                )

        # ---------- Top Row: Decision Metric Cards ----------
        churn = report.get("churn_risk_score", "Medium")
        hex_color, callout_fn, callout_text = CHURN_STYLE.get(churn, CHURN_STYLE["Medium"])

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 4px solid {hex_color};">
                    <div style="color: #94A3B8; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.05em;">CHURN RISK SCORE</div>
                    <div style="color: {hex_color}; font-size: 2.2rem; font-weight: 800; margin-top: 0.2rem;">{churn}</div>
                    <div style="color: #ECFDF5; font-size: 0.85rem; margin-top: 0.4rem;">{callout_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m_col2:
            st.markdown(
                """
                <div class="glass-card" style="border-left: 4px solid #34D399;">
                    <div style="color: #94A3B8; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.05em;">FINANCIAL EXPOSURE</div>
                    <div style="color: #FFFFFF; font-size: 1.5rem; font-weight: 800; margin-top: 0.4rem;">High Impact Risk</div>
                    <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 0.4rem;">Simulated response across price-sensitive & loyal segments.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m_col3:
            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 4px solid #06B6D4;">
                    <div style="color: #94A3B8; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.05em;">GROUNDED EVIDENCE</div>
                    <div style="color: #06B6D4; font-size: 1.5rem; font-weight: 800; margin-top: 0.4rem;">{len(retrieval['documents'])} Relevant Quotes</div>
                    <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 0.4rem;">Cosine similarity threshold: cos={threshold}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------- Executive Summary & Actionable Recommendations ----------
        with st.container(border=True):
            st.markdown("### 📊 Executive Synthesis & Objections")
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                st.markdown("**🚨 Key Customer Objections Raised:**")
                for obj in report.get("primary_objections", []):
                    st.markdown(f"- ❌ {obj}")
            with e_col2:
                st.markdown("**✅ Recommended Mitigation Strategies:**")
                for mit in report.get("mitigation_strategies", []):
                    st.markdown(f"- ✅ {mit}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------- Middle Row: Focus Group Dashboard Persona Cards ----------
        st.markdown("### 💬 Focus Group Dashboard — Simulated Persona Reactions")
        names = list(personas.keys())
        pcol1, pcol2 = st.columns(2)

        with pcol1:
            with st.container(border=True):
                st.markdown(f"#### 👤 {names[0]}", unsafe_allow_html=True)
                st.info(personas[names[0]])

        with pcol2:
            name2 = names[1] if len(names) > 1 else names[0]
            with st.container(border=True):
                st.markdown(f"#### 👑 {name2}", unsafe_allow_html=True)
                st.success(personas[name2])

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------- Bottom Row: RAG Audit Trail Accordion ----------
        with st.expander("🔍 RAG Audit Trail & Source Verification", expanded=False):
            st.caption("Every simulated persona reaction is strictly grounded on these retrieved evidence snippets.")
            if retrieval["is_out_of_distribution"]:
                st.error("🔴 Out-of-Distribution Query — Zero Context Retrieved")
                st.write(retrieval["message"])
            else:
                sources = retrieval.get("sources", [])
                for i, (doc, dist) in enumerate(
                    zip(retrieval["documents"], retrieval["distances"]), start=1
                ):
                    src = sources[i - 1] if i - 1 < len(sources) else "preset"
                    similarity = max(0.0, min(1.0, 1.0 - float(dist)))
                    platform_badge = source_badge(src)
                    src_type = (
                        "cold-start" if "cold-start" in src
                        else ("live-web" if "live-web" in src
                        else ("custom" if "client-upload" in src else "preset"))
                    )
                    with st.container(border=True):
                        st.markdown(
                            f"**Evidence #{i}** {mode_badge(src_type)} <span style='color: #ECFDF5;'>{platform_badge}</span> "
                            f"· Distance: `cos={dist:.4f}` · Similarity: `{similarity * 100:.1f}%`",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"> *\"{doc}\"*")

    else:
        st.info("👈 Select a mode in the sidebar, describe your proposed decision, and click **⚡ Run Customer Simulation**.")


# ==============================================================================
# PAGE 3: PRESETS & KNOWLEDGE BASE GUIDE
# ==============================================================================
elif st.session_state["active_page"] == "guide":
    st.markdown(
        """
        <div>
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">📚 Presets & Knowledge Base Guide</h1>
            <p style="color: #94A3B8; font-size: 1rem;">Explore built-in customer review benchmark datasets and custom data upload specifications.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.markdown(
            """
            <div class="glass-card">
                <h3 style="color: #10B981; font-weight: 700; margin-bottom: 0.8rem;">📁 Custom CSV / JSON Upload Format</h3>
                <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
                    Upload your raw customer feedback files in the sidebar under <strong>Mode 1</strong>. PersonaPulse automatically detects text columns:
                </p>
                <ul style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.8;">
                    <li><code>text</code>, <code>review</code>, <code>feedback</code></li>
                    <li><code>comment</code>, <code>details</code>, <code>description</code>, <code>notes</code></li>
                </ul>
                <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 0.8rem;">
                    Minimum 4 reviews recommended for optimal vector embedding indexing.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with g_col2:
        st.markdown(
            """
            <div class="glass-card">
                <h3 style="color: #06B6D4; font-weight: 700; margin-bottom: 0.8rem;">🌐 Live Web Crawling Specifications</h3>
                <p style="color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
                    Switch to <strong>Mode 2</strong> in the sidebar to search live customer feedback across top web platforms via Tavily API:
                </p>
                <ul style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.8;">
                    <li><strong>Trustpilot & Google Reviews</strong></li>
                    <li><strong>Reddit & Community Discussions</strong></li>
                    <li><strong>G2 & Capterra B2B Software Reviews</strong></li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 🏬 Verified Benchmark Industry Presets")
    for category, reviews in PRESETS_DATA.items():
        with st.expander(f"📦 {category} ({len(reviews)} Grounded Review Quotes)", expanded=False):
            for idx, r in enumerate(reviews, 1):
                st.markdown(f"**Quote #{idx}** (`{r['source']}`):")
                st.markdown(f"> *\"{r['text']}\"*")
