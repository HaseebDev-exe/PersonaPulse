"""RAG engine for PersonaPulse - in-memory ChromaDB + sentence-transformers."""

import chromadb
from sentence_transformers import SentenceTransformer

ZERO_CONTEXT_MESSAGE = (
    "No relevant customer feedback found for this query. "
    "The question appears out-of-distribution relative to the indexed customer base, "
    "so no persona context was retrieved. Please try a query related to "
    "delivery, pricing, packaging, seat limits, or return windows."
)

# Short data badges for platform sources shown in the Audit Trail.
SOURCE_BADGES = {
    "trustpilot": "[Trustpilot]",
    "g2": "[G2]",
    "google": "[Google Review]",
    "reddit": "[Reddit]",
    "app store": "[App Store]",
    "capterra": "[Capterra]",
    "cold-start-synthetic": "[Synthetic Cold-Start]",
    "preset": "[Verified Historical RAG]",
    "client-upload": "[Client Verified Data]",
    "live-web: trustpilot": "[Live Web: Trustpilot]",
    "live-web: reddit": "[Live Web: Reddit]",
    "live-web: g2": "[Live Web: G2]",
    "live-web: google": "[Live Web: Google]",
    "live-web: capterra": "[Live Web: Capterra]",
    "live-web: sitejabber": "[Live Web: Sitejabber]",
    "live-web": "[Live Web]",
}


def source_badge(source: str) -> str:
    """Map a full platform source string to a short audit-trail badge."""
    s = (source or "").strip()
    low = s.lower()
    for key, badge in SOURCE_BADGES.items():
        if key in low:
            return badge
    return f"[{s}]" if s else "[Unknown]"


def _classify_web_source(url: str) -> str:
    """Classify a URL into a live-web source badge key."""
    url_lower = (url or "").lower()
    if "trustpilot" in url_lower:
        return "live-web: trustpilot"
    if "reddit" in url_lower:
        return "live-web: reddit"
    if "g2.com" in url_lower:
        return "live-web: g2"
    if "google" in url_lower:
        return "live-web: google"
    if "capterra" in url_lower:
        return "live-web: capterra"
    if "sitejabber" in url_lower:
        return "live-web: sitejabber"
    return "live-web"


def search_live_web_reviews(business_name: str, tavily_api_key: str, max_results: int = 8) -> list:
    """Fetch real customer reviews from the web using Tavily API.

    Searches review platforms (Trustpilot, Reddit, G2, Capterra, Sitejabber)
    for real customer feedback about the given business.

    Returns list of dicts: {"text": str, "source": str, "url": str}.
    Returns empty list on failure so callers can fall back gracefully.
    """
    from tavily import TavilyClient

    client = TavilyClient(api_key=tavily_api_key)
    review_domains = [
        "trustpilot.com", "reddit.com", "g2.com",
        "capterra.com", "sitejabber.com",
    ]
    search_queries = [
        f"{business_name} customer reviews feedback experience",
        f"{business_name} complaints issues pricing delivery",
    ]

    results = []
    seen_texts = set()

    for query in search_queries:
        if len(results) >= max_results:
            break
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_domains=review_domains,
            )
            for item in response.get("results", []):
                content = (item.get("content") or "").strip()
                url = item.get("url", "")
                if content and content not in seen_texts and len(content) > 30:
                    seen_texts.add(content)
                    source = _classify_web_source(url)
                    results.append({
                        "text": content[:500],
                        "source": source,
                        "url": url,
                    })
        except Exception:
            continue

    return results[:max_results]


class PersonaPulseVectorStore:
    """In-memory vector store for customer persona retrieval."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.EphemeralClient()
        self.collection = self.client.get_or_create_collection(
            name="personapulse",
            metadata={"hnsw:space": "cosine"},
        )

    def index_preset(self, category: str, documents: list) -> int:
        """Index a list of documents under a category. Returns count indexed.

        Accepts plain strings or dicts like {"text": ..., "source": ...}.
        Dict sources are preserved (e.g. source='cold-start-synthetic').
        """
        if not documents:
            return 0

        texts: list = []
        sources: list = []
        for doc in documents:
            if isinstance(doc, dict):
                texts.append(doc.get("text", ""))
                sources.append(doc.get("source", "preset"))
            else:
                texts.append(str(doc))
                sources.append("preset")

        existing_count = self.collection.count()
        ids = [f"{category}_{existing_count + i}" for i in range(len(texts))]
        embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()
        metadatas = [
            {"category": category, "text": t, "source": s}
            for t, s in zip(texts, sources)
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return len(texts)

    def index_custom_dataset(self, file_content: bytes, file_name: str) -> tuple:
        """Parse and index a custom CSV or JSON dataset.

        Accepts .csv files with columns like text/review/feedback/comment and
        .json files containing a list of strings or objects.  Each document is
        tagged with source='client-upload' (or 'client-upload: <platform>' when
        the file includes a source/platform field).

        Returns (count_indexed: int, status_message: str).
        """
        import csv
        import json
        import io

        TEXT_KEYS = [
            "text", "review", "feedback", "comment", "content", "message", "body",
            "feedback_text", "customer_feedback", "user_review", "review_text",
            "details", "description", "notes",
        ]
        SOURCE_KEYS = ["source", "platform", "origin", "channel"]

        file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

        try:
            decoded = file_content.decode("utf-8")
        except UnicodeDecodeError:
            decoded = file_content.decode("latin-1")

        documents: list = []
        selected_column: str = ""

        def _find_first_string_column(rows: list, headers: list) -> str:
            """Return the first column header whose values are non-numeric strings."""
            for header in headers:
                for row in rows[:20]:  # sample first 20 rows
                    val = row.get(header, "")
                    if not isinstance(val, str) or not val.strip():
                        continue
                    try:
                        float(val.strip())
                    except ValueError:
                        return header  # found a non-numeric string column
            return ""

        if file_ext == "csv":
            reader = csv.DictReader(io.StringIO(decoded))
            rows = list(reader)
            headers_lower_map = {}  # lower -> original
            if rows:
                headers_lower_map = {k.lower().strip(): k for k in rows[0].keys()}

            # Determine the text column to use
            text_col_lower = ""
            for k in TEXT_KEYS:
                if k in headers_lower_map:
                    text_col_lower = k
                    break
            if not text_col_lower and rows:
                # Fallback: pick first non-numeric string column
                lower_rows = [{k.lower().strip(): v for k, v in r.items()} for r in rows]
                text_col_lower = _find_first_string_column(lower_rows, list(headers_lower_map.keys()))

            if text_col_lower:
                selected_column = headers_lower_map.get(text_col_lower, text_col_lower)

            for row in rows:
                lower_row = {k.lower().strip(): v for k, v in row.items()}
                text = ""
                if text_col_lower:
                    val = lower_row.get(text_col_lower, "")
                    if isinstance(val, str) and val.strip():
                        text = val.strip()
                source = "client-upload"
                for k in SOURCE_KEYS:
                    val = lower_row.get(k, "")
                    if isinstance(val, str) and val.strip():
                        source = f"client-upload: {val.strip()}"
                        break
                if text:
                    documents.append({"text": text, "source": source})

        elif file_ext == "json":
            data = json.loads(decoded)
            # Handle wrapper objects like {"reviews": [...]}
            if isinstance(data, dict):
                for wrapper_key in ["reviews", "data", "feedback", "items", "records"]:
                    if wrapper_key in data and isinstance(data[wrapper_key], list):
                        data = data[wrapper_key]
                        break
                else:
                    data = [data]
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str) and item.strip():
                        documents.append({"text": item.strip(), "source": "client-upload"})
                    elif isinstance(item, dict):
                        text = ""
                        matched_key = ""
                        for k in TEXT_KEYS:
                            val = item.get(k, "")
                            if isinstance(val, str) and val.strip():
                                text = val.strip()
                                matched_key = k
                                break
                        if not text:
                            # Fallback: first non-numeric string field
                            fallback = _find_first_string_column([item], list(item.keys()))
                            if fallback:
                                text = item[fallback].strip()
                                matched_key = fallback
                        if matched_key and not selected_column:
                            selected_column = matched_key
                        source = "client-upload"
                        for k in SOURCE_KEYS:
                            val = item.get(k, "")
                            if isinstance(val, str) and val.strip():
                                source = f"client-upload: {val.strip()}"
                                break
                        if text:
                            documents.append({"text": text, "source": source})

        if not documents:
            return 0, (
                "No valid review text found in the uploaded file. "
                "Ensure your file has a column/field named one of: "
                + ", ".join(TEXT_KEYS)
                + ". Or include at least one non-numeric string column."
            )

        count = self.index_preset("Custom Upload", documents)
        col_info = f" using column '{selected_column}'" if selected_column else ""
        return count, f"Successfully indexed {count} review(s) from '{file_name}'{col_info}."

    def query_customer_base(
        self, query_text: str, top_k: int = 3, distance_threshold: float = 1.2
    ) -> dict:
        """Query the customer base with Out-of-Distribution detection.

        Returns dict with:
          - is_out_of_distribution: bool
          - context: str (empty when OOD)
          - documents: list[str]
          - distances: list[float]
          - metadatas: list[dict]
          - sources: list[str]
          - message: str (fallback message when OOD, else context)
        """
        if self.collection.count() == 0:
            return {
                "is_out_of_distribution": True,
                "context": "",
                "documents": [],
                "distances": [],
                "metadatas": [],
                "sources": [],
                "message": ZERO_CONTEXT_MESSAGE,
            }

        query_embedding = self.model.encode([query_text], convert_to_numpy=True).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
            include=["documents", "distances", "metadatas"],
        )

        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0] or []
        sources = [
            (m.get("source", "preset") if isinstance(m, dict) else "preset")
            for m in metadatas
        ]

        if not documents or not distances:
            return {
                "is_out_of_distribution": True,
                "context": "",
                "documents": [],
                "distances": [],
                "metadatas": [],
                "sources": [],
                "message": ZERO_CONTEXT_MESSAGE,
            }

        min_distance = min(distances)

        if min_distance > distance_threshold:
            return {
                "is_out_of_distribution": True,
                "context": "",
                "documents": [],
                "distances": distances,
                "metadatas": metadatas,
                "sources": sources,
                "message": ZERO_CONTEXT_MESSAGE,
            }

        context = "\n\n".join(f"- {doc}" for doc in documents)
        return {
            "is_out_of_distribution": False,
            "context": context,
            "documents": documents,
            "distances": distances,
            "metadatas": metadatas,
            "sources": sources,
            "message": context,
        }
