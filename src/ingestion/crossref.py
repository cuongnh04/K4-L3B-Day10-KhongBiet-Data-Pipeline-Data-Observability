from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any
import requests

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def clean_abstract(text: str) -> str:
    """Loại bỏ thẻ HTML/XML rác như <jats:p> và chuẩn hóa khoảng trắng."""
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = (
        cleaned.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )
    return normalize_whitespace(cleaned)


def parse_crossref_payload(payload: dict[str, Any]) -> list[PaperRecord]:
    """Parse Crossref API payload JSON thành danh sách các đối tượng PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        paper_id = item.get("DOI", "").strip()
        if not paper_id:
            continue

        titles = item.get("title", [])
        title = normalize_whitespace(titles[0]) if titles else ""
        if not title:
            continue

        summary = clean_abstract(item.get("abstract", ""))

        authors: list[str] = []
        for author in item.get("author", []):
            given = author.get("given", "").strip()
            family = author.get("family", "").strip()
            full_name = normalize_whitespace(f"{given} {family}")
            if full_name:
                authors.append(full_name)

        subjects = item.get("subject", [])
        if isinstance(subjects, str):
            categories = [normalize_whitespace(subjects)]
        else:
            categories = [normalize_whitespace(s) for s in subjects if s]
        primary_category = categories[0] if categories else "General"

        pub_parts = item.get("published", {}).get("date-parts", [[]])[0]
        published = ""
        if pub_parts:
            if len(pub_parts) >= 3:
                published = f"{pub_parts[0]:04d}-{pub_parts[1]:02d}-{pub_parts[2]:02d}"
            elif len(pub_parts) == 2:
                published = f"{pub_parts[0]:04d}-{pub_parts[1]:02d}-01"
            elif len(pub_parts) == 1:
                published = f"{pub_parts[0]:04d}-01-01"

        created_dt = item.get("created", {}).get("date-time", "")
        updated = created_dt[:10] if created_dt else published

        url = item.get("URL", f"https://doi.org/{paper_id}")
        abs_url = url
        pdf_url = url
        comment = f"Crossref record {paper_id}"

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Gửi yêu cầu tới Crossref API (hoặc fallback đọc snapshot local), lưu trữ raw artifacts."""
    raw_response_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    payload: dict[str, Any] | None = None

    if settings.refresh_source:
        try:
            url = "https://api.crossref.org/works"
            params = {
                "query": settings.source_query,
                "filter": settings.source_filter,
                "rows": settings.max_results,
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                payload = resp.json()
                write_json(raw_response_path, payload)
        except Exception:
            # Tự động chuyển sang fallback offline snapshot
            payload = None

    if payload is None:
        if raw_response_path.exists():
            payload = read_json(raw_response_path)
        else:
            raise FileNotFoundError(f"Không tìm thấy raw snapshot tại {raw_response_path}")

    records = parse_crossref_payload(payload)

    # Lưu trữ bản bóc tách raw records
    records_payload = [asdict(record) for record in records]
    write_json(raw_records_path, records_payload)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Đọc JSON snapshot và chuyển đổi thành danh sách PaperRecord."""
    raw_list = read_json(path)
    records: list[PaperRecord] = []
    for item in raw_list:
        records.append(
            PaperRecord(
                paper_id=item["paper_id"],
                title=item["title"],
                summary=item["summary"],
                authors=item.get("authors", []),
                categories=item.get("categories", []),
                primary_category=item.get("primary_category", "General"),
                published=item.get("published", ""),
                updated=item.get("updated", ""),
                abs_url=item.get("abs_url", ""),
                pdf_url=item.get("pdf_url", ""),
                comment=item.get("comment", ""),
            )
        )
    return records

