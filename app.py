"""PersonaPulse Streamlit app - Grounded Customer Simulation Engine."""

import streamlit as st

from presets import PRESETS_DATA, get_preset_categories
from rag_engine import PersonaPulseVectorStore
from simulation_engine import (
    run_multi_persona_simulation,
    generate_decision_report,
    generate_cold_start_archetypes,
)

MODE_PRESETS = "Mode 1: Verified Historical Presets (Pre-loaded CRM/Reviews)"
MODE_COLDSTART = "Mode 2: Cold-Start Generator (Synthetic Archetypes for New Ideas)"

CHURN_STYLE = {
    "Low": ("green", "success", "🟢 Low churn risk — customers are likely to stay."),
    "Medium": ("orange", "warning", "🟠 Medium churn risk — some friction, act on objections."),
    "High": ("red", "error", "🔴 High churn risk — immediate mitigation recommended."),
}

st.set_page_config(
    page_title="PersonaPulse — Grounded Customer Simulation Engine",
    layout="wide",
)

st.title("PersonaPulse — Grounded Customer Simulation Engine")
st.caption("RAG-grounded multi-persona simulation with audit trail. No hallucinations — every claim traces to retrieved feedback.")

# ---------- Sidebar controls ----------
with st.sidebar:
    st.header("Controls")

    mode = st.radio(
        "Select Mode",
        [MODE_PRESETS, MODE_COLDSTART],
        index=0,
        help="Mode 1 uses verified pre-loaded reviews. Mode 2 synthesizes archetypes for brand-new ideas.",
    )
    use_cold_start = mode == MODE_COLDSTART

    st.divider()

    if use_cold_start:
        st.subheader("New Idea")
        cold_domain = st.text_input(
            "Business domain / idea",
            value="Online Pharmacy / Medicine Delivery",
            help="Cold-start archetypes are synthesized for this domain.",
        )
        preset = get_preset_categories()[0]
    else:
        st.subheader("Customer Base")
        preset = st.selectbox("Preset customer base", get_preset_categories(), index=0)
        cold_domain = ""

    raw_key = st.text_input("Cohere API key (CO_API_KEY / COHERE_API_KEY)", type="password", help="Required for live LLM simulation. Falls back to heuristic report if missing. Or set CO_API_KEY / COHERE_API_KEY env var.")
    st.markdown("[Get a free Cohere API key](https://dashboard.cohere.com/api-keys)")
    api_key = (raw_key or "").strip()

    query_text = st.text_area(
        "Proposed change / business question",
        value="We plan to increase prices by 15% and shorten the return window to 5 days. How will customers react?",
        height=140,
    )

    with st.expander("Advanced retrieval settings"):
        top_k = st.slider("Top-K retrieval", 1, 5, 3)
        threshold = st.slider("OOD distance threshold", 0.5, 2.0, 1.2, step=0.05)

    run_btn = st.button("Run Simulation", type="primary", use_container_width=True)


@st.cache_resource(show_spinner="Loading embedding model + vector store...")
def get_store():
    return PersonaPulseVectorStore()


def run_pipeline(preset_category: str, query: str, key: str, k: int, dist_threshold: float, use_cold_start: bool = False, cold_domain: str = ""):
    from simulation_engine import resolve_api_key

    # Validate: only trigger the Cohere client with a valid, non-empty key.
    # Empty keys stay None so the pipeline uses heuristic fallback without a 401 round-trip.
    effective_key = resolve_api_key(key) or None
    store = get_store()
    # Re-index preset each run on a fresh ephemeral store per session is cached,
    # so clear and re-add to avoid duplicates across preset switches.
    try:
        store.client.delete_collection("personapulse")
    except Exception:
        pass
    store.collection = store.client.get_or_create_collection(
        name="personapulse", metadata={"hnsw:space": "cosine"}
    )
    is_synthetic = False
    if use_cold_start:
        archetypes = generate_cold_start_archetypes(
            cold_domain or "new business", count=6, api_key=effective_key
        )
        label = (cold_domain or "new business").strip() or "new business"
        store.index_preset(f"Cold-Start: {label}", archetypes)
        is_synthetic = True
    else:
        store.index_preset(preset_category, PRESETS_DATA[preset_category])

    retrieval = store.query_customer_base(query, top_k=k, distance_threshold=dist_threshold)
    retrieval["is_synthetic"] = is_synthetic
    retrieval["has_api_key"] = bool(effective_key)
    context = retrieval["context"]

    persona_responses = run_multi_persona_simulation(
        query, context, api_key=effective_key
    )
    report = generate_decision_report(query, persona_responses, context, api_key=effective_key)
    return retrieval, persona_responses, report


def mode_badge(is_synthetic: bool) -> str:
    if is_synthetic:
        return ":orange[[Synthetic Cold-Start]]"
    return ":blue[[Verified Historical RAG]]"


if run_btn:
    if not query_text.strip():
        st.warning("Please enter a proposed change.")
        st.stop()
    if use_cold_start and not (cold_domain or "").strip():
        st.warning("Please enter a business domain for Cold-Start mode.")
        st.stop()

    with st.spinner("Retrieving feedback + simulating personas..."):
        retrieval, personas, report = run_pipeline(preset, query_text, api_key, top_k, threshold, use_cold_start, cold_domain)

    # ---------- Grounding banner ----------
    if retrieval["is_out_of_distribution"]:
        st.warning(f"⚠️ Out-of-distribution query — zero-context fallback. {retrieval['message']}")
    elif retrieval.get("is_synthetic"):
        st.success(f"Grounded on {len(retrieval['documents'])} synthetic cold-start snippet(s) for '{cold_domain}'. {mode_badge(True)}")
    else:
        st.success(f"Grounded on {len(retrieval['documents'])} retrieved snippet(s) from '{preset}'. {mode_badge(False)}")

    # ---------- Auth / fallback notice ----------
    # No client call is made without a non-empty key; fallbacks here mean either
    # no key was provided (heuristic mode) or the provided key was rejected (401).
    fallback_text = " ".join(str(v) for v in personas.values())
    if "LLM unavailable" in fallback_text:
        if not retrieval.get("has_api_key"):
            st.info(
                "ℹ️ No Cohere API key provided — running in heuristic mode (no LLM call made). "
                "Paste a key into the sidebar or set CO_API_KEY / COHERE_API_KEY for live personas."
            )
        elif "invalid_api_key" in fallback_text or "401" in fallback_text:
            st.error(
                "🔑 Cohere API rejected the key (401 invalid_api_key) — showing heuristic fallback instead. "
                "Get a fresh key at https://dashboard.cohere.com/api-keys, paste it into the sidebar "
                "(no extra spaces), and re-run."
            )
        else:
            st.warning(f"⚠️ Live LLM unavailable — heuristic fallback active. Details: {fallback_text[:300]}")

    # ---------- Decision Report with churn callouts ----------
    churn = report.get("churn_risk_score", "Medium")
    color, callout_fn, callout_text = CHURN_STYLE.get(churn, CHURN_STYLE["Medium"])
    st.subheader(f"Decision Report  {mode_badge(retrieval.get('is_synthetic', False))}")
    c1, c2 = st.columns([1, 3])
    with c1:
        with st.container(border=True):
            st.metric("Churn Risk Score", churn)
            st.markdown(f":{color}[● {churn} risk]")
    with c2:
        getattr(st, callout_fn)(f"**Churn outlook:** {callout_text}")
        with st.container(border=True):
            st.markdown("**Primary Objections**")
            for obj in report.get("primary_objections", []):
                st.markdown(f"- {obj}")
        with st.container(border=True):
            st.markdown("**Mitigation Strategies**")
            for mit in report.get("mitigation_strategies", []):
                st.markdown(f"- ✅ {mit}")

    # ---------- Focus Group Dashboard: persona cards ----------
    st.subheader("Focus Group Dashboard — Persona Reactions")
    names = list(personas.keys())
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        with st.container(border=True):
            st.markdown(f"### 💬 {names[0]}  {mode_badge(retrieval.get('is_synthetic', False))}")
            st.info(personas[names[0]])
    with pcol2:
        name2 = names[1] if len(names) > 1 else names[0]
        with st.container(border=True):
            st.markdown(f"### 💬 {name2}  {mode_badge(retrieval.get('is_synthetic', False))}")
            st.success(personas[name2])

    # ---------- Executive summary ----------
    st.subheader("Executive Summary")
    base = cold_domain if retrieval.get("is_synthetic") else preset
    st.info(
        f"**Proposal:** {query_text}\n\n"
        f"**Churn risk:** {churn} | **Base:** {base} | "
        f"**Grounded:** {'No (OOD)' if retrieval['is_out_of_distribution'] else 'Yes'}\n\n"
        f"**Bottom line:** {'; '.join(report.get('primary_objections', [])[:2])}. "
        f"Recommended: {'; '.join(report.get('mitigation_strategies', [])[:2])}."
    )

    # ---------- Audit Trail ----------
    with st.expander("🔍 Retrieved Historical Evidence (RAG Audit Trail)", expanded=False):
        st.caption("Every persona claim must trace to these retrieved snippets.")
        if retrieval["is_out_of_distribution"]:
            st.error("🔴 OOD — zero context")
            st.write(retrieval["message"])
        else:
            base_label = f"Cold-Start: {cold_domain}" if retrieval.get("is_synthetic") else f"Preset: {preset}"
            st.markdown(f"🔵 **{base_label}** | 🟢 **Grounded:** {len(retrieval['documents'])} quotes  {mode_badge(retrieval.get('is_synthetic', False))}")
            sources = retrieval.get("sources", [])
            for i, (doc, dist) in enumerate(
                zip(retrieval["documents"], retrieval["distances"]), start=1
            ):
                src = sources[i - 1] if i - 1 < len(sources) else "preset"
                similarity = max(0.0, min(1.0, 1.0 - float(dist)))
                tag = "`source=cold-start-synthetic`" if src == "cold-start-synthetic" else "`source=verified-preset`"
                with st.container(border=True):
                    st.markdown(f"**Evidence #{i}** {mode_badge(src == 'cold-start-synthetic')}  📏 distance `{dist:.4f}` · similarity `{similarity:.4f}`  🏷️ {tag}")
                    st.markdown(f"> {doc}")
else:
    st.info("👈 Pick a mode at the top of the sidebar, enter your Cohere API key + proposed change, then click **Run Simulation**.")
