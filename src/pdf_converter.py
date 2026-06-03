import os
import re
import time
import zipfile
import shutil
import tempfile
import requests
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from config import AppConfig


class PDFConverter:
    MAX_PAGES = 200
    SPLIT_SIZE = 100
    PART_SEP = "__p"

    def __init__(self, config: AppConfig):
        self.config = config
        self.api_key = config.mineru_api_key
        self.base_url = "https://mineru.net/api/v4"

    @staticmethod
    def _truncate_by_utf8(s: str, max_bytes: int = 50) -> str:
        encoded = s.encode("utf-8")
        if len(encoded) <= max_bytes:
            return s
        truncated = encoded[:max_bytes]
        return truncated.decode("utf-8", errors="ignore")

    @staticmethod
    def _get_page_count(pdf_path: Path) -> int:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)

    @staticmethod
    def _split_pdf(pdf_path: Path, chunk_size: int = 100) -> list[Path]:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        if total_pages <= chunk_size:
            return [pdf_path]

        parts = []
        num_parts = (total_pages + chunk_size - 1) // chunk_size
        tmp_dir = tempfile.mkdtemp(prefix="pdf_split_")

        for i in range(num_parts):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, total_pages)
            writer = PdfWriter()
            for page_idx in range(start, end):
                writer.add_page(reader.pages[page_idx])
            part_name = f"{pdf_path.stem}{PDFConverter.PART_SEP}{i + 1}of{num_parts}.pdf"
            part_path = Path(tmp_dir) / part_name
            with open(str(part_path), "wb") as f:
                writer.write(f)
            parts.append(part_path)
            print(f"  Split part {i + 1}/{num_parts}: pages {start + 1}-{end} -> {part_name}")

        return parts

    @staticmethod
    def _merge_split_mds(output_dir: Path) -> list[Path]:
        merged = []
        md_files = sorted(output_dir.glob("*.md"))

        groups: dict[str, list[Path]] = {}
        for md_path in md_files:
            stem = md_path.stem
            match = re.match(r"^(.+)" + re.escape(PDFConverter.PART_SEP) + r"(\d+)of(\d+)$", stem)
            if match:
                prefix = match.group(1)
                groups.setdefault(prefix, []).append(md_path)
            else:
                merged.append(md_path)

        for prefix, parts in groups.items():
            parts.sort(key=lambda p: int(
                re.match(r"^(.+)" + re.escape(PDFConverter.PART_SEP) + r"(\d+)of(\d+)$", p.stem).group(2)
            ))
            combined = ""
            for part_path in parts:
                combined += part_path.read_text(encoding="utf-8") + "\n"
            target = output_dir / f"{prefix}.md"
            target.write_text(combined.strip(), encoding="utf-8")
            for part_path in parts:
                part_path.unlink()
            print(f"  Merged {len(parts)} parts -> {target.name}")
            merged.append(target)

        return merged

    def _upload_files(self, file_paths: list[Path], data_ids: list[str] | None = None) -> str:
        url = f"{self.base_url}/file-urls/batch"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        if data_ids is None:
            files_data = [
                {"name": fp.name, "data_id": self._truncate_by_utf8(fp.stem, 50)}
                for fp in file_paths
            ]
        else:
            files_data = [
                {"name": fp.name, "data_id": did}
                for fp, did in zip(file_paths, data_ids)
            ]

        data = {
            "files": files_data,
            "model_version": "vlm",
            "file.is_ocr": True,
        }
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()
        result = res.json()
        if result.get("code") != 0:
            print(result.get("code"))
            raise RuntimeError(f"申请上传链接失败: {result.get('msg')}")
        batch_id = result["data"]["batch_id"]
        file_urls = result["data"]["file_urls"]
        for i, file_url in enumerate(file_urls):
            with open(file_paths[i], "rb") as f:
                res_upload = requests.put(file_url, data=f)
                if res_upload.status_code != 200:
                    raise RuntimeError(f"上传文件失败: {file_paths[i].name}")
        return batch_id

    def _wait_for_batch_result(self, batch_id: str) -> list[dict]:
        url = f"{self.base_url}/extract-results/batch/{batch_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        while True:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            result = res.json()
            if result.get("code") != 0:
                print(result.get("code"))
                raise RuntimeError(f"MinerU任务状态错误: {result.get('msg')}")
            items = result["data"]["extract_result"]
            all_done = True
            for item in items:
                state = item.get("state")
                if state in ["pending", "running"]:
                    all_done = False
                    break
                err_msg = item.get("err_msg", "")
                if err_msg:
                    raise RuntimeError(f"MinerU任务错误: {err_msg}")
            if all_done:
                return items
            time.sleep(5)

    def _download_and_extract(self, result_item: dict, extract_dir: str) -> str:
        full_zip_url = result_item.get("full_zip_url")
        if not full_zip_url:
            raise RuntimeError("No full_zip_url found in MinerU result")
        local_zip = f"{result_item.get('data_id', 'result')}.zip"
        r = requests.get(full_zip_url, stream=True)
        with open(local_zip, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        with zipfile.ZipFile(local_zip, "r") as zf:
            zf.extractall(extract_dir)
        os.remove(local_zip)
        return extract_dir

    def convert_all_pdfs(self) -> list[Path]:
        pdf_dir = self.config.pdf_dir
        output_dir = self.config.markdown_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_files = sorted(pdf_dir.glob("*.pdf"))
        existing_mds = {p.stem for p in output_dir.glob("*.md")}
        pending = [p for p in pdf_files if p.stem not in existing_mds]
        for p in pdf_files:
            if p.stem in existing_mds:
                print(f"  Skipping (already exists): {p.name}")
        results = [output_dir / f"{p.stem}.md" for p in pdf_files if p.stem in existing_mds]

        upload_list: list[tuple[Path, str]] = []
        split_tmp_dirs: list[str] = []

        for pdf_path in pending:
            page_count = self._get_page_count(pdf_path)
            print(f"  {pdf_path.name}: {page_count} pages")

            if page_count <= self.MAX_PAGES:
                data_id = self._truncate_by_utf8(pdf_path.stem, 50)
                upload_list.append((pdf_path, data_id))
            else:
                print(f"  Splitting {pdf_path.name} ({page_count} pages > {self.MAX_PAGES})")
                parts = self._split_pdf(pdf_path, self.SPLIT_SIZE)
                if parts[0].parent != pdf_path.parent:
                    split_tmp_dirs.append(str(parts[0].parent))
                num_parts = len(parts)
                for idx, part_path in enumerate(parts, 1):
                    suffix = f"{self.PART_SEP}{idx}of{num_parts}"
                    prefix = self._truncate_by_utf8(pdf_path.stem, 40)
                    data_id = f"{prefix}{suffix}"
                    upload_list.append((part_path, data_id))

        batch_size = 50
        for batch_start in range(0, len(upload_list), batch_size):
            batch = upload_list[batch_start:batch_start + batch_size]
            batch_paths = [item[0] for item in batch]
            batch_ids = [item[1] for item in batch]
            print(f"Uploading batch: {[p.name for p in batch_paths]}")
            try:
                batch_id = self._upload_files(batch_paths, batch_ids)
                print(f"  Batch ID: {batch_id}")
                batch_results = self._wait_for_batch_result(batch_id)
                for result_item in batch_results:
                    data_id = result_item.get("data_id")
                    try:
                        extract_dir = f"{batch_id}_{data_id}"
                        self._download_and_extract(result_item, extract_dir)
                        md_path = os.path.join(extract_dir, "full.md")
                        if not os.path.exists(md_path):
                            print(f"  Warning: Markdown not found for {data_id}")
                            continue
                        target_path = output_dir / f"{data_id}.md"
                        shutil.move(md_path, str(target_path))
                        shutil.rmtree(extract_dir, ignore_errors=True)
                        print(f"  Saved to: {target_path}")
                        results.append(target_path)
                    except Exception as e:
                        print(f"  Error downloading result for {data_id}: {e}")
            except Exception as e:
                print(f"  Error in batch starting with {batch_paths[0].name}: {e}")

        self._merge_split_mds(output_dir)
        results = list(output_dir.glob("*.md"))

        for tmp_dir in split_tmp_dirs:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        return results
