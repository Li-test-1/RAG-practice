from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from config import AppConfig
import lancedb


class VectorStore:
    TABLE_NAME = "documents"

    def __init__(self, config: AppConfig, embeddings: Embeddings):
        self.config = config
        self.embeddings = embeddings
        self.db_path = str(config.vector_db_dir)
        self._db = None
        self._table = None

    @property
    def db(self):
        if self._db is None:
            self._db = lancedb.connect(self.db_path)
        return self._db

    @property
    def table(self):
        if self._table is None:
            try:
                self._table = self.db.open_table(self.TABLE_NAME)
            except Exception:
                self._table = None
        return self._table

    def build(self, documents: List[Document]):
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        vectors = self.embeddings.embed_documents(texts)

        data = []
        for i, (text, meta, vector) in enumerate(zip(texts, metadatas, vectors)):
            row = {
                "id": i,
                "vector": vector,
                "text": text,
                "source_file": meta.get("source_file", ""),
                "chunk_id": meta.get("chunk_id", 0),
                "heading": meta.get("heading", ""),
                "tag": meta.get("tag", ""),
                "file_type": meta.get("file_type", ""),
                "institution": meta.get("institution", ""),
            }
            data.append(row)

        try:
            self.db.drop_table(self.TABLE_NAME)
        except Exception:
            pass

        self._table = self.db.create_table(self.TABLE_NAME, data)
        print(f"Vector store built: {len(data)} documents")

    def similarity_search(
        self,
        query: str,
        top_k: int = 10,
        tag_filter: Optional[str] = None,
    ) -> List[Document]:
        if self.table is None:
            raise RuntimeError("Vector store not built yet")

        query_vector = self.embeddings.embed_query(query)

        filter_str = None
        if tag_filter:
            filter_str = f"tag = '{tag_filter}'"

        search = self.table.search(query_vector)
        if filter_str:
            search = search.where(filter_str)
        results = search.limit(top_k).to_list()

        documents = []
        for row in results:
            doc = Document(
                page_content=row["text"],
                metadata={
                    "source_file": row.get("source_file", ""),
                    "chunk_id": row.get("chunk_id", 0),
                    "heading": row.get("heading", ""),
                    "tag": row.get("tag", ""),
                    "file_type": row.get("file_type", ""),
                    "institution": row.get("institution", ""),
                    "score": row.get("_distance", 0.0),
                },
            )
            documents.append(doc)
        return documents
