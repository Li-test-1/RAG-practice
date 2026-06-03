from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from api.state import get_config, get_pipeline, update_pipeline_config

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    tag_filter: Optional[str] = None


class ConfigUpdate(BaseModel):
    embedding_model: Optional[str] = None
    enable_rerank: Optional[bool] = None
    rerank_model: Optional[str] = None
    use_bm25: Optional[bool] = None
    use_vector: Optional[bool] = None
    top_k_vector: Optional[int] = None
    top_k_bm25: Optional[int] = None
    rrf_k: Optional[int] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    default_tag: Optional[str] = None


@router.get("/config")
def get_config_api():
    config = get_config()
    return {
        "current": config.to_dict(),
        "options": config.get_options(),
    }


@router.post("/config")
def update_config(data: ConfigUpdate):
    config = update_pipeline_config(data.model_dump(exclude_none=True))
    return {
        "message": "配置已更新",
        "current": config.to_dict(),
    }


@router.post("/query")
def query(data: QueryRequest):
    pipeline = get_pipeline()
    result = pipeline.query(
        question=data.question,
        top_k=data.top_k,
        tag_filter=data.tag_filter,
    )
    return result


@router.get("/tags")
def get_tags():
    config = get_config()
    options = config.get_options()
    return {"tags": options["tags"]}
