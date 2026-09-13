"""PersonaPulse Streamlit app - Grounded Customer Simulation Engine."""

import os
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
    "Low": ("#22C55E", "green", "🟢 Low Churn Risk — High customer retention expected."),
    "Medium": ("#F59E0B", "orange", "🟠 Medium Churn Risk — Noticeable friction, act on top objections."),
    "High": ("#EF4444", "red", "🔴 High Churn Risk — Severe dissatisfaction & immediate revenue risk."),
}


def get_logo_path():
    """Safely check if logo file exists in project root or assets directory."""
    for path in ["logo.png", "assets/logo.png"]:
        if os.path.exists(path):
            return path
    return None


st.set_page_config(
    page_title="PersonaPulse — Grounded Customer Simulation Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Executive Dark Theme CSS Injection ----------
st.markdown(
    """
    <style>
    /* Fonts & General Contrast */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #F8FAFC;
    }

    /* Sidebar Gradient & Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E1B4B 0%, #0F172A 50%, #1E293B 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Sidebar High-Contrast Text & Headings */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {
        color: #E2E8F0 !important;
    }

    /* Sidebar Glassmorphic Input Controls */
    [data-testid="stSidebar"] .stTextInput input, 
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    /* Active Radio Buttons & Toggle Accents */
    [data-testid="stSidebar"] div[role="radiogroup"] label span {
        color: #F8FAFC !important;
    }

    /* Main Input Fields, Text Areas & Selectboxes */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #FF4B4B !important;
        box-shadow: 0 0 0 1px #FF4B4B !important;
    }

    /* Input Labels & Headers */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label, .stSlider label, .stFileUploader label {
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }

    /* Glassmorphism Containers & Cards */
    [data-testid="stMetricValue"], .stContainer, div[data-testid="stExpander"] {
        border-radius: 12px;
    }
    
    div[data-testid="stExpander"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
    }

    /* High-Visibility Gradient Primary Button */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF4B4B 0%, #E11D48 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.65rem 1.5rem !important;
        box-shadow: 0 4px 14px 0 rgba(255, 75, 75, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(225, 29, 72, 0.6) !important;
    }

    /* Status Pill Badges */
    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.3rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        background-color: #334155;
        color: #38BDF8;
        border: 1px solid #0284C7;
        margin-left: 0.5rem;
    }
    
    .badge-preset { background-color: #1E3A8A; color: #93C5FD; border: 1px solid #3B82F6; }
    .badge-custom { background-color: #4C1D95; color: #DDD6FE; border: 1px solid #8B5CF6; }
    .badge-live-web { background-color: #064E3B; color: #A7F3D0; border: 1px solid #10B981; }
    .badge-cold-start { background-color: #7C2D12; color: #FED7AA; border: 1px solid #F97316; }

    /* Speech Bubble & Custom Containers */
    .speech-bubble {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        position: relative;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1E293B;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_path = get_logo_path()

# ---------- Sidebar Ergonomics ----------
with st.sidebar:
    if logo_path:
        st.image(logo_path, width=180)
        st.markdown("<div style='margin-top: -10px; margin-bottom: 15px; font-size: 0.85rem; color: #94A3B8;'><strong>PersonaPulse</strong> | Grounded Decision Engine</div>", unsafe_allow_html=True)
    else:
        st.header("⚡ PersonaPulse")

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


@st.cache_resource(show_spinner="Initializing vector engine & embedding models...")
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


# ---------- Main Dashboard Header Layout ----------
if logo_path:
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image(logo_path, width=90)
    with col_title:
        st.title("PersonaPulse — Grounded Customer Simulation Engine")
        st.caption("RAG-driven multi-persona decision stress-testing. No hallucinations — every claim is grounded on retrieved customer feedback.")
else:
    st.title("PersonaPulse — Grounded Customer Simulation Engine")
    st.caption("RAG-driven multi-persona decision stress-testing. No hallucinations — every claim is grounded on retrieved customer feedback.")

st.divider()

# ---------- Core Action Input Section ----------
st.markdown("### 🎯 Proposed Business Decision / Strategic Change")
query_text = st.text_area(
    "Describe your proposed price change, feature sunset, policy update, or business strategy:",
    value="We plan to increase subscription prices by 15% and shorten our return window from 30 days to 5 days. How will our customer base react?",
    height=120,
    help="Enter any strategic proposal to simulate grounded customer reactions.",
)

run_btn = st.button("⚡ Run Customer Simulation", type="primary", use_container_width=True)

st.divider()

# ---------- Pipeline Execution & Output Layout ----------
if run_btn:
    if not query_text.strip():
        st.warning("⚠️ Please enter a proposed business decision to simulate.")
        st.stop()
    if use_cold_start and not (cold_domain or "").strip():
        st.warning("⚠️ Please enter a business name or domain for Live Web Search.")
        st.stop()

    with st.spinner("🔍 Indexing evidence & simulating customer personas..."):
        try:
            retrieval, personas, report = run_pipeline(
                preset, query_text, api_key, top_k, threshold,
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
            f"<div><strong>Grounded Status:</strong> Grounded on {len(retrieval['documents'])} evidence quote(s) from {grounding_label}. {mode_badge(data_source)}</div>",
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Top Row: Decision Metric Cards ----------
    churn = report.get("churn_risk_score", "Medium")
    hex_color, callout_fn, callout_text = CHURN_STYLE.get(churn, CHURN_STYLE["Medium"])

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(
            f"""
            <div style="background-color: #1E293B; border: 1px solid #334155; padding: 1.2rem; border-radius: 12px;">
                <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 600;">CHURN RISK SCORE</div>
                <div style="color: {hex_color}; font-size: 2.2rem; font-weight: 800; margin-top: 0.2rem;">{churn}</div>
                <div style="color: #E2E8F0; font-size: 0.85rem; margin-top: 0.4rem;">{callout_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col2:
        st.markdown(
            """
            <div style="background-color: #1E293B; border: 1px solid #334155; padding: 1.2rem; border-radius: 12px;">
                <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 600;">FINANCIAL EXPOSURE</div>
                <div style="color: #F8FAFC; font-size: 1.4rem; font-weight: 700; margin-top: 0.4rem;">High Impact Risk</div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 0.4rem;">Simulated response across price-sensitive & loyal segments.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_col3:
        st.markdown(
            """
            <div style="background-color: #1E293B; border: 1px solid #334155; padding: 1.2rem; border-radius: 12px;">
                <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 600;">GROUNDED EVIDENCE</div>
                <div style="color: #38BDF8; font-size: 1.4rem; font-weight: 700; margin-top: 0.4rem;">"""
            + f"{len(retrieval['documents'])} Relevant Quotes"
            + """</div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 0.4rem;">Cosine similarity threshold: """
            + f"{threshold}"
            + """</div>
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
            st.markdown("**🚨 Key Objections Raised:**")
            for obj in report.get("primary_objections", []):
                st.markdown(f"- ❌ {obj}")
        with e_col2:
            st.markdown("**✅ Recommended Mitigation Strategies:**")
            for mit in report.get("mitigation_strategies", []):
                st.markdown(f"- ✅ {mit}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Middle Row: Focus Group Dashboard Persona Cards ----------
    st.markdown("### 💬 Focus Group Dashboard — Persona Reactions")
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
                        f"**Evidence #{i}** {mode_badge(src_type)} <span style='color: #F1F5F9;'>{platform_badge}</span> "
                        f"· Distance: `cos={dist:.4f}` · Similarity: `{similarity * 100:.1f}%`",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"> *\"{doc}\"*")

else:
    st.info("👈 Select a mode in the sidebar, describe your proposed decision, and click **⚡ Run Customer Simulation**.")
