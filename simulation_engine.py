"""Simulation engine for PersonaPulse - Cohere multi-persona simulation + decision report."""

import json
import os

DEFAULT_MODEL = "command-a-plus-05-2026"

PERSONAS = {
    "Price-Sensitive Customer": (
        "You are a Price-Sensitive Customer. You care primarily about value for money, "
        "discounts, hidden fees, and price increases. "
        "Base your response STRICTLY on the provided Customer Feedback Context snippets. "
        "Do not invent pricing or facts not present in the context. "
        "Quote or paraphrase relevant snippets about pricing, seat limits, delivery charges, "
        "or return costs. If the context is empty, state that you have no relevant prior "
        "feedback to base your decision on."
    ),
    "Long-Term Loyalist": (
        "You are a Long-Term Loyalist. You value consistency, trust, service quality, "
        "and relationship history, and you tolerate minor issues if the brand is reliable. "
        "Base your response STRICTLY on the provided Customer Feedback Context snippets. "
        "Do not invent experiences not present in the context. "
        "Reference relevant snippets about delivery, packaging, support, or return experience. "
        "If the context is empty, state that you have no relevant prior feedback to base "
        "your decision on."
    ),
}


def resolve_api_key(api_key: str | None = None) -> str:
    """Resolve the effective Cohere key: explicit UI param first, then env vars.

    Checks CO_API_KEY and COHERE_API_KEY. Always strips whitespace.
    Returns "" when no key is available.
    """
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()
    for var in ("CO_API_KEY", "COHERE_API_KEY"):
        env_key = (os.getenv(var) or "").strip()
        if env_key:
            return env_key
    return ""


def _get_client(api_key: str | None = None):
    from cohere import ClientV2

    if isinstance(api_key, str):
        key = api_key.strip()
    else:
        key = ""
    if not key:
        key = resolve_api_key()
    if not key:
        raise ValueError("COHERE_API_KEY not set. Set CO_API_KEY/COHERE_API_KEY env var or pass api_key.")
    return ClientV2(api_key=key)


def parse_cohere_text(response) -> str:
    """Extract clean text from a Cohere ClientV2 chat response.

    Checks response.message and response.message.content, loops over content
    items and keeps ONLY items where type == 'text' or which expose a 'text'
    attribute ('thinking' items are always skipped). Joins all extracted
    strings into a single clean string. If no text item is found or an
    exception occurs, safely tries response.message.content[0].text, else
    returns "". Never returns the raw object or str(response).
    """
    try:
        message = getattr(response, "message", None)
        content = getattr(message, "content", None) if message is not None else None
        if isinstance(content, list) and content:
            texts = []
            for item in content:
                if getattr(item, "type", None) == "thinking":
                    continue
                if getattr(item, "type", None) == "text" or hasattr(item, "text"):
                    t = getattr(item, "text", None)
                    if isinstance(t, str) and t.strip():
                        texts.append(t.strip())
            if texts:
                return "\n".join(texts).strip()
            # Safe fallback: first non-thinking item's text attribute, if usable.
            for item in content:
                if getattr(item, "type", None) == "thinking":
                    continue
                first_text = getattr(item, "text", None)
                if isinstance(first_text, str) and first_text.strip():
                    return first_text.strip()
            return ""
        if isinstance(content, str) and content.strip():
            return content.strip()
    except Exception:
        pass
    # Last safe attempt: first non-thinking content item's text; final fallback "".
    try:
        for item in response.message.content:
            if getattr(item, "type", None) == "thinking":
                continue
            t = getattr(item, "text", None)
            if isinstance(t, str) and t.strip():
                return t.strip()
    except Exception:
        pass
    return ""


# Backward-compatible aliases.
extract_response_text = parse_cohere_text
_extract_text = parse_cohere_text


def _chat(
    client,
    model: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    json_mode: bool = False,
) -> str:
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "thinking": None,  # disable reasoning traces; text-only output
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = client.chat(**kwargs)
    except TypeError as e:
        # Older SDKs without the 'thinking' parameter: retry without it.
        if "thinking" in str(e):
            kwargs.pop("thinking", None)
            resp = client.chat(**kwargs)
        else:
            raise
    return parse_cohere_text(resp)


def simulate_persona(
    persona_name: str,
    query_text: str,
    context: str,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client=None,
) -> str:
    """Simulate a single persona conditioned strictly on RAG context."""
    if persona_name not in PERSONAS:
        raise ValueError(f"Unknown persona: {persona_name}. Choose from {list(PERSONAS)}")

    system_prompt = PERSONAS[persona_name]
    context_block = context.strip() if context and context.strip() else "(No relevant customer feedback retrieved.)"

    user_prompt = (
        f"Customer Feedback Context:\n{context_block}\n\n"
        f"Business question / proposal:\n{query_text}\n\n"
        "Respond in character as this persona in 3-6 sentences, "
        "grounded ONLY in the context above. "
        "Mention whether you would accept, hesitate, or churn."
    )

    active_client = None
    try:
        active_client = client or _get_client(api_key)
        text = _chat(
            active_client,
            model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        ).strip()
        if not text:
            raise ValueError("Empty text content in Cohere response.")
        return text
    except Exception as e:
        # Graceful fallback: invalid/missing key or API error should not crash the app.
        # Return a grounded stub so the heuristic decision report can still run.
        return (
            f"[{persona_name} fallback — live LLM unavailable ({e}). "
            f"Judging only from the retrieved context above: "
            f"{'no relevant feedback was retrieved, so I cannot give a grounded reaction.' if context_block.startswith('(No relevant') else 'my reaction follows the quoted feedback snippets.'}]"
        )


def simulate_price_sensitive(query_text: str, context: str, **kwargs) -> str:
    """Simulate the Price-Sensitive Customer persona."""
    return simulate_persona("Price-Sensitive Customer", query_text, context, **kwargs)


def simulate_loyalist(query_text: str, context: str, **kwargs) -> str:
    """Simulate the Long-Term Loyalist persona."""
    return simulate_persona("Long-Term Loyalist", query_text, context, **kwargs)


def run_multi_persona_simulation(query_text: str, context: str, **kwargs) -> dict:
    """Run all personas and return {persona_name: response}."""
    return {
        name: simulate_persona(name, query_text, context, **kwargs)
        for name in PERSONAS
    }


def _heuristic_report(query_text: str, persona_responses: dict) -> dict:
    """Rule-based fallback report when Cohere is unavailable."""
    combined = " ".join(persona_responses.values()).lower() if persona_responses else ""
    q = (query_text or "").lower()

    price_signals = ["price", "pricing", "expensive", "cost", "fee", "seat", "rs.", "$", "zyada", "discount"]
    risk_signals = ["churn", "leave", "cancel", "too much", "disappointed", "kharab", "late", "confusing"]

    price_hits = sum(1 for s in price_signals if s in combined or s in q)
    risk_hits = sum(1 for s in risk_signals if s in combined)

    if risk_hits >= 3 or price_hits >= 4:
        churn = "High"
    elif risk_hits >= 1 or price_hits >= 2:
        churn = "Medium"
    else:
        churn = "Low"

    return {
        "churn_risk_score": churn,
        "primary_objections": [
            "Pricing / value-for-money concerns raised in retrieved feedback",
            "Delivery / packaging / seat-limit friction from prior reviews",
        ],
        "mitigation_strategies": [
            "Offer transparent pricing or a limited-time discount tied to the proposal",
            "Proactively address delivery / packaging / seat-limit pain points from context",
            "Follow up with loyalty reassurance and a clear return / support path",
        ],
    }


def _heuristic_archetypes(domain: str, count: int) -> list:
    """Fallback synthetic reviews when Cohere is unavailable."""
    domain = (domain or "new business").strip() or "new business"
    templates = [
        f"As a new {domain} customer, delivery time really matters to me. Agar delivery late hui to I will switch to a competitor.",
        f"Tried {domain} once, pricing felt high for the value. Price thora zyada laga, discount hona chahiye for first-time buyers.",
        f"Packaging for my {domain} order was average. Achhi packaging hoti to premium feel aata, unboxing matters a lot.",
        f"Considering a {domain} subscription but seat limits confuse me. Per-user pricing samajh nahi aayi, clear plans chahiye.",
        f"My {domain} return experience will decide loyalty. Return window kam hua to I won't reorder, easy returns build trust.",
        f"Heard good things about {domain} service quality. Support fast hona chahiye, especially for new customers like me.",
        f"For {domain}, value for money is key. Agar quality consistent rahi to I will become a loyal customer.",
        f"Comparing {domain} options online. Delivery charges zyada hue to cart abandon kar dunga, free delivery attracts me.",
    ]
    out = []
    for i in range(count):
        out.append(
            {
                "text": templates[i % len(templates)],
                "source": "cold-start-synthetic",
                "domain": domain,
            }
        )
    return out


def generate_cold_start_archetypes(
    domain_description: str,
    count: int = 6,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client=None,
) -> list:
    """Synthesize 5-8 customer reviews for a new business domain using Cohere.

    Each item is tagged with source='cold-start-synthetic'.
    Returns list of dicts: {"text": str, "source": ..., "domain": ...}.
    Falls back to heuristic templates when Cohere is unavailable.
    """
    count = max(5, min(8, int(count or 6)))
    domain = (domain_description or "new business").strip() or "new business"

    system_prompt = (
        "You are a market-research copywriter. Generate realistic, diverse customer "
        "reviews for a NEW business domain with no historical feedback. "
        "Mix English with occasional Roman Urdu/English phrases (e.g. 'bohat late', "
        "'price zyada', 'samajh nahi aayi') for authenticity. Cover delivery, pricing, "
        "packaging, seat limits / plans, and return windows where relevant. "
        "Output STRICT JSON: {\"reviews\": [\"...\", \"...\"] } with exactly "
        f"{count} reviews, each 1-3 sentences."
    )
    user_prompt = f"Business domain: {domain}\nGenerate {count} archetypal customer reviews."

    try:
        client = client or _get_client(api_key)
        raw = _chat(
            client,
            model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            max_tokens=1500,
            json_mode=True,
        )
        data = json.loads(raw)
        reviews = data.get("reviews", [])
        if not isinstance(reviews, list) or not reviews:
            raise ValueError("Empty reviews from LLM")
        reviews = [str(r).strip() for r in reviews if str(r).strip()][:8]
        while len(reviews) < 5:
            reviews.append(_heuristic_archetypes(domain, 1)[0]["text"])
        return [
            {"text": r, "source": "cold-start-synthetic", "domain": domain}
            for r in reviews[:count]
        ]
    except Exception:
        return _heuristic_archetypes(domain, count)


def generate_decision_report(
    query_text: str,
    persona_responses: dict,
    context: str,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client=None,
) -> dict:
    """Generate a decision report with churn risk, objections, and mitigations.

    Returns dict with:
      - churn_risk_score: 'Low' | 'Medium' | 'High'
      - primary_objections: list[str]
      - mitigation_strategies: list[str]
    """
    context_block = context.strip() if context and context.strip() else "(No relevant customer feedback retrieved.)"
    persona_block = "\n\n".join(
        f"{name}:\n{resp}" for name, resp in (persona_responses or {}).items()
    ) or "(No persona responses.)"

    system_prompt = (
        "You are a customer-insights analyst. Given the business proposal, "
        "the RAG customer feedback context, and the persona reactions, "
        "output STRICT JSON with keys: churn_risk_score ('Low'|'Medium'|'High'), "
        "primary_objections (list of 2-4 strings), mitigation_strategies (list of 2-4 strings). "
        "Ground objections strictly in the provided context and persona responses."
    )
    user_prompt = (
        f"Proposal:\n{query_text}\n\nContext:\n{context_block}\n\n"
        f"Persona reactions:\n{persona_block}\n\nReturn JSON only."
    )

    try:
        client = client or _get_client(api_key)
        raw = _chat(
            client,
            model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
            json_mode=True,
        )
        data = json.loads(raw)
        churn = data.get("churn_risk_score", "Medium")
        if churn not in ("Low", "Medium", "High"):
            churn = "Medium"
        return {
            "churn_risk_score": churn,
            "primary_objections": list(data.get("primary_objections", []))[:5],
            "mitigation_strategies": list(data.get("mitigation_strategies", []))[:5],
        }
    except Exception:
        return _heuristic_report(query_text, persona_responses)
