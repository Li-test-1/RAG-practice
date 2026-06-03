from typing import List
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import AppConfig
from src.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT


class Generator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.llm_model,
            base_url=config.llm_base_url,
            api_key=config.dashscope_api_key,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
        )

    @staticmethod
    def _format_context(documents: List[Document]) -> str:
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source_file", "unknown")
            heading = doc.metadata.get("heading", "")
            tag = doc.metadata.get("tag", "")
            context_parts.append(
                f"[文档{i}] 来源: {source} | 章节: {heading} | 标签: {tag}\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(context_parts)

    def generate_answer(
        self,
        query: str,
        documents: List[Document],
    ) -> dict:
        context = self._format_context(documents)
        user_content = RAG_USER_PROMPT.format(context=context, question=query)

        messages = [
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = self.llm.invoke(messages)

        return {
            "question": query,
            "answer": response.content,
            "system_prompt": RAG_SYSTEM_PROMPT,
            "user_prompt": user_content,
            "context_formatted": context,
            "context_documents": [
                {
                    "source_file": doc.metadata.get("source_file", ""),
                    "heading": doc.metadata.get("heading", ""),
                    "tag": doc.metadata.get("tag", ""),
                    "rrf_score": doc.metadata.get("rrf_score", None),
                    "rerank_score": doc.metadata.get("rerank_score", None),
                    "text_content": doc.page_content,
                }
                for doc in documents
            ],
        }
