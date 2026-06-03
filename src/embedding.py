from langchain_core.embeddings import Embeddings
from config import AppConfig, EMBEDDING_MODELS


class DashScopeEmbeddings(Embeddings):
    def __init__(self, model_name: str = "text-embedding-v3", api_key: str = ""):
        self.model_name = model_name
        import dashscope
        dashscope.api_key = api_key
        self._dashscope = dashscope

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self._dashscope.TextEmbedding.call(
                model=self.model_name,
                input=batch,
            )
            # print(f"DashScope embedding API response: {resp}")
            if "output" in resp and "embeddings" in resp["output"]:
                for emb in resp["output"]["embeddings"]:
                    embeddings.append(emb["embedding"])
            else:
                # print(f"DashScope embedding API error: {resp}")
                raise RuntimeError(f"DashScope embedding API error: {resp}")
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        resp = self._dashscope.TextEmbedding.call(
            model=self.model_name,
            input=[text],
        )
        if "output" in resp and "embeddings" in resp["output"]:
            return resp["output"]["embeddings"][0]["embedding"]
        raise RuntimeError(f"DashScope embedding API error: {resp}")


def get_embeddings(config: AppConfig) -> Embeddings:
    emb_config = config.embedding_config
    provider = emb_config["provider"]
    model_name = emb_config["model_name"]

    if provider == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=model_name)

    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=model_name,
            api_key=config.openai_api_key,
        )

    elif provider == "dashscope":
        return DashScopeEmbeddings(
            model_name=model_name,
            api_key=config.dashscope_api_key,
        )

    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
