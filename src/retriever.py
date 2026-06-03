from typing import List, Optional
from langchain_core.documents import Document
from config import AppConfig
from src.vector_store import VectorStore
from src.bm25_store import BM25Store


class HybridRetriever:
    def __init__(
        self,
        config: AppConfig,
        vector_store: VectorStore,
        bm25_store: BM25Store,
    ):
        self.config = config
        self.vector_store = vector_store
        self.bm25_store = bm25_store

    @staticmethod
    def _rrf_merge(
        vector_results: List[Document],
        bm25_results: List[tuple[Document, float]],
        k: int = 60,
    ) -> List[Document]:
        rrf_scores = {}

        for rank, doc in enumerate(vector_results):
            key = doc.page_content
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if not hasattr(rrf_scores[key], "_doc"):
                rrf_scores[key] = rrf_scores.get(key, 0.0)
            if key not in rrf_scores:
                rrf_scores[key] = 0.0
            rrf_scores[key] += 1.0 / (k + rank + 1)

        doc_map = {}
        for rank, doc in enumerate(vector_results):
            key = doc.page_content
            if key not in doc_map:
                doc_map[key] = doc
                doc_map[key].metadata["rrf_score"] = 0.0
            doc_map[key].metadata["rrf_score"] += 1.0 / (k + rank + 1)

        for rank, (doc, _score) in enumerate(bm25_results):
            key = doc.page_content
            if key not in doc_map:
                doc_map[key] = doc
                doc_map[key].metadata["rrf_score"] = 0.0
            doc_map[key].metadata["rrf_score"] += 1.0 / (k + rank + 1)

        sorted_docs = sorted(
            doc_map.values(),
            key=lambda d: d.metadata.get("rrf_score", 0.0),
            reverse=True,
        )
        return sorted_docs

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        tag_filter: Optional[str] = None,
    ) -> List[Document]:
        use_vector = self.config.use_vector
        use_bm25 = self.config.use_bm25

        if not use_vector and not use_bm25:
            raise ValueError("At least one retrieval method must be enabled")

        vector_results = []
        bm25_results = []

        if use_vector:
            vector_results = self.vector_store.similarity_search(
                query=query,
                top_k=self.config.top_k_vector,
                tag_filter=tag_filter,
            )

        if use_bm25:
            bm25_results = self.bm25_store.search(
                query=query,
                top_k=self.config.top_k_bm25,
                tag_filter=tag_filter,
            )

        if use_vector and use_bm25:
            merged = self._rrf_merge(
                vector_results,
                bm25_results,
                k=self.config.rrf_k,
            )
        elif use_vector:
            merged = vector_results
        else:
            merged = [doc for doc, _ in bm25_results]

        return merged[:top_k]
