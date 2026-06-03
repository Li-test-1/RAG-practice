from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional
from dotenv import load_dotenv
import os

load_dotenv()

EMBEDDING_MODELS = {
    "bge-large-zh": {
        "model_name": "BAAI/bge-large-zh-v1.5",
        "dimension": 1024,
        "provider": "huggingface",
    },
    "text-embedding-3-small": {
        "model_name": "text-embedding-3-small",
        "dimension": 1536,
        "provider": "openai",
    },
    "text-embedding-v3": {
        "model_name": "text-embedding-v3",
        "dimension": 1024,
        "provider": "dashscope",
    },
}

RERANK_MODELS = {
    "bge-reranker-v2-m3": {
        "model_name": "BAAI/bge-reranker-v2-m3",
        "provider": "huggingface",
    },
    "jina-reranker-v2": {
        "model_name": "jina-reranker-v2-base-multilingual",
        "provider": "jina",
    },
    "gte-rerank": {
        "model_name": "gte-rerank",
        "provider": "dashscope",
    },
    "qwen3-rerank": {
        "model_name": "qwen3-rerank",
        "provider": "dashscope",
    },
}

TAG_MAPPING = {
    "财报": "financial_report",
    "研报": "research_report",
    "调研纪要": "research_memo",
    "研究报告": "research_report",
    "深度研究": "research_report",
    "业绩点评": "earnings_review",
    "季报点评": "earnings_review",
}


@dataclass
class AppConfig:
    project_root: Path = field(default_factory=lambda: Path(__file__).parent)

    data_dir: Path = field(init=False)
    pdf_dir: Path = field(init=False)
    markdown_dir: Path = field(init=False)
    vector_db_dir: Path = field(init=False)
    bm25_db_dir: Path = field(init=False)

    embedding_model: Literal["bge-large-zh", "text-embedding-3-small", "text-embedding-v3"] = "text-embedding-v3"
    embedding_dimension: int = field(init=False)

    enable_rerank: bool = True
    rerank_model: Literal["bge-reranker-v2-m3", "jina-reranker-v2",
                          "gte-rerank", "qwen3-rerank"] = "qwen3-rerank"

    use_bm25: bool = True
    use_vector: bool = True
    top_k_vector: int = 10
    top_k_bm25: int = 10
    rrf_k: int = 60

    llm_model: str = "qwen-plus"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    default_tag: str = "general"

    def __post_init__(self):
        self.data_dir = self.project_root / "data"
        self.pdf_dir = self.data_dir / "pdf"
        self.markdown_dir = self.data_dir / "markdown"
        self.vector_db_dir = self.data_dir / "lancedb"
        self.bm25_db_dir = self.data_dir / "bm25"
        self.embedding_dimension = EMBEDDING_MODELS[self.embedding_model]["dimension"]

    @property
    def embedding_config(self) -> dict:
        return EMBEDDING_MODELS[self.embedding_model]

    @property
    def rerank_config(self) -> dict:
        return RERANK_MODELS[self.rerank_model]

    @property
    def dashscope_api_key(self) -> str:
        return os.getenv("DASHSCOPE_API_KEY", "")

    @property
    def openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def deepseek_api_key(self) -> str:
        return os.getenv("DEEPSEEK_API_KEY", "")

    @property
    def jina_api_key(self) -> str:
        return os.getenv("JINA_API_KEY", "")

    @property
    def mineru_api_key(self) -> str:
        return os.getenv("MINERU_API_KEY", "")

    def to_dict(self) -> dict:
        return {
            "embedding_model": self.embedding_model,
            "enable_rerank": self.enable_rerank,
            "rerank_model": self.rerank_model,
            "use_bm25": self.use_bm25,
            "use_vector": self.use_vector,
            "top_k_vector": self.top_k_vector,
            "top_k_bm25": self.top_k_bm25,
            "rrf_k": self.rrf_k,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "default_tag": self.default_tag,
        }

    def update_from_dict(self, data: dict) -> "AppConfig":
        if "embedding_model" in data and data["embedding_model"] in EMBEDDING_MODELS:
            self.embedding_model = data["embedding_model"]
            self.embedding_dimension = EMBEDDING_MODELS[self.embedding_model]["dimension"]
        if "enable_rerank" in data:
            self.enable_rerank = data["enable_rerank"]
        if "rerank_model" in data and data["rerank_model"] in RERANK_MODELS:
            self.rerank_model = data["rerank_model"]
        if "use_bm25" in data:
            self.use_bm25 = data["use_bm25"]
        if "use_vector" in data:
            self.use_vector = data["use_vector"]
        if "top_k_vector" in data:
            self.top_k_vector = int(data["top_k_vector"])
        if "top_k_bm25" in data:
            self.top_k_bm25 = int(data["top_k_bm25"])
        if "rrf_k" in data:
            self.rrf_k = int(data["rrf_k"])
        if "llm_model" in data:
            self.llm_model = data["llm_model"]
        if "llm_base_url" in data:
            self.llm_base_url = data["llm_base_url"]
        if "llm_temperature" in data:
            self.llm_temperature = float(data["llm_temperature"])
        if "llm_max_tokens" in data:
            self.llm_max_tokens = int(data["llm_max_tokens"])
        if "default_tag" in data:
            self.default_tag = data["default_tag"]
        return self

    @staticmethod
    def get_options() -> dict:
        return {
            "embedding_models": list(EMBEDDING_MODELS.keys()),
            "rerank_models": list(RERANK_MODELS.keys()),
            "tags": list(set(TAG_MAPPING.values())) + ["general"],
        }
