from typing import Optional
from config import AppConfig
from src.pdf_converter import PDFConverter
from src.text_splitter import MarkdownSplitter
from src.embedding import get_embeddings
from src.vector_store import VectorStore
from src.bm25_store import BM25Store
from src.retriever import HybridRetriever
from src.reranker import Reranker
from src.generator import Generator


class RAGPipeline:
    def __init__(self, config: AppConfig = None):
        if config is None:
            config = AppConfig()
        self.config = config

        self.converter = PDFConverter(config)
        self.splitter = MarkdownSplitter(config)
        self.embeddings = get_embeddings(config)
        self.vector_store = VectorStore(config, self.embeddings)
        self.bm25_store = BM25Store(config)
        self.reranker = Reranker(config)
        self.generator = Generator(config)

        self._retriever = None

    @property
    def retriever(self) -> HybridRetriever:
        if self._retriever is None:
            self._retriever = HybridRetriever(
                config=self.config,
                vector_store=self.vector_store,
                bm25_store=self.bm25_store,
            )
        return self._retriever

    def step_convert_pdf(self):
        print("=" * 60)
        print("Step 1: Converting PDF to Markdown (MinerU)")
        print("=" * 60)
        results = self.converter.convert_all_pdfs()
        print(f"Converted {len(results)} files\n")
        return results

    def step_chunk_documents(self):
        print("=" * 60)
        print("Step 2: Chunking Markdown (MarkdownHeaderTextSplitter + RecursiveCharacterTextSplitter)")
        print("=" * 60)
        documents = self.splitter.split_all_markdowns()
        print(f"Total chunks: {len(documents)}\n")
        return documents

    def step_build_index(self, documents=None):
        print("=" * 60)
        print("Step 3: Building vector index + BM25 index")
        print("=" * 60)
        if documents is None:
            documents = self.splitter.split_all_markdowns()

        if self.config.use_vector:
            print("Building LanceDB vector index...")
            self.vector_store.build(documents)

        if self.config.use_bm25:
            print("Building BM25 index...")
            self.bm25_store.build(documents)

        print("Index building complete\n")

    def step_query(
        self,
        question: str,
        top_k: int = 5,
        tag_filter: Optional[str] = None,
    ) -> dict:
        print("=" * 60)
        print(f"Step 4: Querying - {question}")
        print("=" * 60)

        if self.config.use_bm25:
            try:
                self.bm25_store.load()
            except FileNotFoundError:
                print("BM25 index not found, building...")
                documents = self.splitter.split_all_markdowns()
                self.bm25_store.build(documents)

        print(f"Retrieving (vector={self.config.use_vector}, bm25={self.config.use_bm25})...")
        retrieved_docs = self.retriever.retrieve(
            query=question,
            top_k=top_k * 2 if self.config.enable_rerank else top_k,
            tag_filter=tag_filter,
        )
        print(f"Retrieved {len(retrieved_docs)} documents")

        if self.config.enable_rerank:
            print(f"Reranking with {self.config.rerank_model}...")
            retrieved_docs = self.reranker.rerank(
                query=question,
                documents=retrieved_docs,
                top_k=top_k,
            )
            print(f"Reranked to {len(retrieved_docs)} documents")

        print("Generating answer with DeepSeek...")
        result = self.generator.generate_answer(
            query=question,
            documents=retrieved_docs,
        )
        print(f"\nAnswer: {result['answer'][:200]}...\n")
        return result

    def run_indexing(self):
        self.step_convert_pdf()
        documents = self.step_chunk_documents()
        self.step_build_index(documents)
        print("Indexing pipeline complete!")

    def query(
        self,
        question: str,
        top_k: int = 5,
        tag_filter: Optional[str] = None,
    ) -> dict:
        return self.step_query(question, top_k, tag_filter)

    def update_config(self, config: AppConfig):
        self.config = config
        self.reranker = Reranker(config)
        self.generator = Generator(config)
        self._retriever = None
