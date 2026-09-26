from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Biến đổi danh sách PaperRecord thành DataFrame sạch phục vụ tạo vector embedding.

    1. Chuẩn hóa title, summary, authors, categories.
    2. Parse ngày published/updated và tính tuổi đời age_days.
    3. Tạo các cột helper: authors_joined, categories_joined, summary_chars, text_for_embedding.
    4. Khử trùng lặp theo paper_id và lọc bỏ dữ liệu rác.
    """
    rows: list[dict] = []

    # Đảm bảo run_date có thông tin múi giờ để tính toán
    if run_date.tzinfo is None:
        run_date_tz = run_date.replace(tzinfo=timezone.utc)
    else:
        run_date_tz = run_date

    for r in records:
        paper_id = normalize_whitespace(r.paper_id)
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)

        if not paper_id or not title:
            continue

        authors = [normalize_whitespace(a) for a in r.authors if normalize_whitespace(a)]
        authors_joined = ", ".join(authors)

        categories = [normalize_whitespace(c) for c in r.categories if normalize_whitespace(c)]
        categories_joined = ", ".join(categories)
        primary_category = (
            normalize_whitespace(r.primary_category)
            if r.primary_category
            else (categories[0] if categories else "General")
        )

        published = normalize_whitespace(r.published)
        updated = normalize_whitespace(r.updated) or published

        # Tính toán tuổi đời dữ liệu: age_days = (run_date - published).days
        age_days = 0
        if published:
            try:
                pub_dt = datetime.strptime(published[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                age_days = max(0, (run_date_tz - pub_dt).days)
            except Exception:
                age_days = 0

        summary_chars = len(summary)

        # Định dạng văn bản phục vụ Embedding đúng chuẩn 5 phần
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        abs_url = normalize_whitespace(r.abs_url) or f"https://doi.org/{paper_id}"
        pdf_url = normalize_whitespace(r.pdf_url) or f"https://doi.org/{paper_id}"
        comment = normalize_whitespace(r.comment) or f"Crossref record {paper_id}"

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "authors_joined": authors_joined,
                "categories": categories,
                "categories_joined": categories_joined,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "age_days": age_days,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
                "abs_url": abs_url,
                "pdf_url": pdf_url,
                "comment": comment,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Khử trùng lặp bản ghi theo khóa duy nhất paper_id
    df = df.drop_duplicates(subset=["paper_id"], keep="first").reset_index(drop=True)
    return df

