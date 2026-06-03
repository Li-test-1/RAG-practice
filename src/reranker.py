from typing import List
from langchain_core.documents import Document
from config import AppConfig, RERANK_MODELS


class BaseReranker:
    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        raise NotImplementedError


class HuggingFaceReranker(BaseReranker):
    def __init__(self, model_name: str):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        pairs = [[query, doc.page_content] for doc in documents]
        scores = self.model.predict(pairs)
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc, score in scored_docs[:top_k]:
            doc_copy = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "rerank_score": float(score)},
            )
            results.append(doc_copy)
        return results


class JinaReranker(BaseReranker):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.jina.ai/v1/rerank"

    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        import requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "top_n": top_k,
            "documents": [doc.page_content for doc in documents],
        }
        resp = requests.post(url=self.url, headers=headers, json=data)
        resp.raise_for_status()
        results_json = resp.json().get("results", [])
        results = []
        for item in results_json:
            idx = item["index"]
            score = item["relevance_score"]
            doc = documents[idx]
            doc_copy = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "rerank_score": score},
            )
            results.append(doc_copy)
        return results


class DashScopeReranker(BaseReranker):
    def __init__(self, api_key: str, model_name: str = "qwen3-rerank"):
        import dashscope
        dashscope.api_key = api_key
        self._dashscope = dashscope
        self.model_name = model_name

    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        texts = [doc.page_content for doc in documents]
        resp = self._dashscope.TextReRank.call(
            model=self.model_name,
            query=query,
            documents=texts,
            top_n=top_k,
            return_documents=False,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"DashScope rerank error: {resp.message}")
        results_json = resp.output.get("results", [])
        results = []
        for item in results_json:
            idx = item.get("index", 0)
            score = item.get("relevance_score", 0.0)
            doc = documents[idx]
            doc_copy = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "rerank_score": score},
            )
            results.append(doc_copy)
        return results


class Reranker:
    def __init__(self, config: AppConfig):
        self.config = config
        self._reranker = None
        if config.enable_rerank:
            self._reranker = self._create_reranker()

    def _create_reranker(self) -> BaseReranker:
        rerank_config = self.config.rerank_config
        provider = rerank_config["provider"]
        model_name = rerank_config["model_name"]
        print(model_name)

        if provider == "huggingface":
            return HuggingFaceReranker(model_name)
        elif provider == "jina":
            return JinaReranker(self.config.jina_api_key)
        elif provider == "dashscope":
            return DashScopeReranker(self.config.dashscope_api_key, model_name)
        else:
            raise ValueError(f"Unsupported rerank provider: {provider}")

    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        if not self.config.enable_rerank or self._reranker is None:
            return documents[:top_k]
        return self._reranker.rerank(query, documents, top_k)
