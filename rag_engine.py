"""RAG engine for PersonaPulse - in-memory ChromaDB + sentence-transformers."""

import chromadb
from sentence_transformers import SentenceTransformer

ZERO_CONTEXT_MESSAGE = (
    "No relevant customer feedback found for this query. "
    "The question appears out-of-distribution relative to the indexed customer base, "
    "so no persona context was retrieved. Please try a query related to "
    "delivery, pricing, packaging, seat limits, or return windows."
)


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
