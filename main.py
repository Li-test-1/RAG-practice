import sys
import click
from config import AppConfig
from src.pipeline import RAGPipeline


@click.group()
def cli():
    """RAG-ljy 问答系统命令行工具"""
    pass


@cli.command()
def convert():
    """Step 1: 将 PDF 文件转换为 Markdown (MinerU)"""
    config = AppConfig()
    pipeline = RAGPipeline(config)
    pipeline.step_convert_pdf()


@cli.command()
def chunk():
    """Step 2: 按 Markdown 二级标题切分文档"""
    config = AppConfig()
    pipeline = RAGPipeline(config)
    pipeline.step_chunk_documents()


@cli.command()
def build_index():
    """Step 3: 构建向量索引 + BM25 索引"""
    config = AppConfig()
    pipeline = RAGPipeline(config)
    pipeline.step_build_index()


@cli.command()
def index_all():
    """一键执行完整索引流程：转换 → 切分 → 建库"""
    config = AppConfig()
    pipeline = RAGPipeline(config)
    pipeline.run_indexing()


@cli.command()
@click.option("--question", "-q", required=True, help="查询问题")
@click.option("--top-k", default=5, help="返回结果数量")
@click.option("--tag-filter", default=None, help="权限标签过滤")
def ask(question, top_k, tag_filter):
    """查询问答"""
    config = AppConfig()
    pipeline = RAGPipeline(config)
    result = pipeline.query(question, top_k=top_k, tag_filter=tag_filter)
    print("\n" + "=" * 60)
    print("问题:", result["question"])
    print("=" * 60)
    print("回答:", result["answer"])
    print("=" * 60)
    print("引用文档:")
    for doc in result["context_documents"]:
        print(f"  - [{doc['source_file']}] {doc['heading']} (score={doc.get('score', 'N/A')})")


@cli.command()
def interactive():
    """交互式问答模式"""
    config = AppConfig()
    pipeline = RAGPipeline(config)
    print("RAG-ljy 问答系统 (输入 'quit' 退出)")
    print(f"配置: Embedding={config.embedding_model}, Rerank={'启用' if config.enable_rerank else '禁用'} ({config.rerank_model})")
    print(f"      BM25={'启用' if config.use_bm25 else '禁用'}, Vector={'启用' if config.use_vector else '禁用'}")
    print("-" * 60)
    while True:
        try:
            question = input("\n请输入问题: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            break
        if question.lower() in ("quit", "exit", "q"):
            print("退出")
            break
        if not question:
            continue
        result = pipeline.query(question)
        print("\n" + "=" * 60)
        print("回答:", result["answer"])
        print("=" * 60)


if __name__ == "__main__":
    cli()
