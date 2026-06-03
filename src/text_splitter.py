import re
from pathlib import Path
from typing import List
from langchain_core.documents import Document
# from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from config import AppConfig, TAG_MAPPING


class MarkdownSplitter:
    def __init__(self, config: AppConfig):
        self.config = config

        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ],
            strip_headers=False,
        )

        self.chunk_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
            length_function=len,
        )

    @staticmethod
    def _extract_institution(file_name: str) -> str:
        match = re.search(r"【(.+?)】", file_name)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def _extract_file_type(file_name: str) -> str:
        for keyword, file_type in [
            ("财报", "财报"),
            ("研究报告", "研究报告"),
            ("深度研究", "深度研究报告"),
            ("调研纪要", "调研纪要"),
            ("业绩点评", "业绩点评"),
            ("季报点评", "季报点评"),
        ]:
            if keyword in file_name:
                return file_type
        return "其他"

    @staticmethod
    def _assign_tag(file_name: str) -> str:
        for keyword, tag in TAG_MAPPING.items():
            if keyword in file_name:
                return tag
        return "general"

    def split_markdown_by_h2(self, md_path: Path) -> List[Document]:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        file_name = md_path.name
        institution = self._extract_institution(file_name)
        file_type = self._extract_file_type(file_name)
        tag = self._assign_tag(file_name)

        header_docs = self.header_splitter.split_text(content)

        documents = []
        chunk_id = 0
        for doc in header_docs:
            sub_docs = self.chunk_splitter.split_documents([doc])
            for sub_doc in sub_docs:
                heading = "preface"
                for key in ("h3", "h2", "h1"):
                    if key in doc.metadata:
                        heading = doc.metadata[key]
                        break

                sub_doc.metadata.update({
                    "source_file": file_name,
                    "chunk_id": chunk_id,
                    "heading": heading,
                    "tag": tag,
                    "file_type": file_type,
                    "institution": institution,
                })
                documents.append(sub_doc)
                chunk_id += 1

        return documents

    def split_all_markdowns(self) -> List[Document]:
        md_dir = self.config.markdown_dir
        all_documents = []
        md_files = sorted(md_dir.glob("*.md"))
        for md_path in md_files:
            docs = self.split_markdown_by_h2(md_path)
            all_documents.extend(docs)
            print(f"Split {md_path.name}: {len(docs)} chunks")
        print(f"Total: {len(md_files)} files, {len(all_documents)} chunks")
        return all_documents
