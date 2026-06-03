import pickle
from typing import List, Tuple
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
import jieba
from config import AppConfig


class BM25Store:
    def __init__(self, config: AppConfig):
        self.config = config
        self._bm25 = None
        self._documents = None

    @staticmethod
    def _tokenize_zh(text: str) -> List[str]:
        return list(jieba.cut(text))

    def build(self, documents: List[Document]):
        self._documents = documents
        tokenized_corpus = [
            self._tokenize_zh(doc.page_content) for doc in documents
        ]
        self._bm25 = BM25Okapi(tokenized_corpus)
        self._save()
        print(f"BM25 index built: {len(documents)} documents")

    def _save(self):
        self.config.bm25_db_dir.mkdir(parents=True, exist_ok=True)
        index_path = self.config.bm25_db_dir / "bm25_index.pkl"
        with open(index_path, "wb") as f:
            pickle.dump(
                {
                    "bm25": self._bm25,
                    "documents": [
                        {"text": doc.page_content, "metadata": doc.metadata}
                        for doc in self._documents
                    ],
                },
                f,
            )
        print(f"BM25 index saved to: {index_path}")

    def load(self):
        index_path = self.config.bm25_db_dir / "bm25_index.pkl"
        if not index_path.exists():
            raise FileNotFoundError(f"BM25 index not found: {index_path}")
        with open(index_path, "rb") as f:
            data = pickle.load(f)
        self._bm25 = data["bm25"]
        self._documents = [
            Document(page_content=d["text"], metadata=d["metadata"])
            for d in data["documents"]
        ]
        print(f"BM25 index loaded: {len(self._documents)} documents")

    def search(
        self,
        query: str,
        top_k: int = 10,
        tag_filter: str = None,
    ) -> List[Tuple[Document, float]]:
        if self._bm25 is None:
            raise RuntimeError("BM25 index not built or loaded")

        tokenized_query = self._tokenize_zh(query)
        scores = self._bm25.get_scores(tokenized_query)

        scored_docs = list(zip(self._documents, scores))

        if tag_filter:
            scored_docs = [
                (doc, score)
                for doc, score in scored_docs
                if doc.metadata.get("tag") == tag_filter
            ]

        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:top_k]
