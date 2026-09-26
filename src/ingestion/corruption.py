from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Tiêm 6 dạng sự cố dữ liệu thực nghiệm vào DataFrame sạch và ghi log vào output_log_path.

    1. Drop latest records: Bỏ rơi 20% các bài báo mới nhất.
    2. Blank summary: Xóa trắng phần tóm tắt ở một số dòng.
    3. Inject noise: Chèn các chuỗi ký tự rác vào tóm tắt.
    4. Truncate title: Cắt ngắn tiêu đề xuống dưới 8 ký tự.
    5. Stale date: Lùi ngày xuất bản về 365 ngày trước.
    6. Duplicate rows: Nhân đôi các dòng để tạo trùng lặp.
    7. Tái tạo lại trường text_for_embedding cho tất cả các bản ghi.
    """
    if df.empty:
        return df.copy()

    corrupted = df.copy()
    logs: list[dict[str, Any]] = []

    # 1. Drop latest records: Bỏ rơi 20% các bài báo mới nhất
    if "published" in corrupted.columns:
        corrupted = corrupted.sort_values(by="published", ascending=False).reset_index(drop=True)
    num_to_drop = max(1, int(len(corrupted) * 0.2))
    dropped_records = corrupted.iloc[:num_to_drop]
    for _, row in dropped_records.iterrows():
        logs.append(
            {
                "operation": "drop_latest_records",
                "paper_id": str(row.get("paper_id", "")),
                "title": str(row.get("title", "")),
                "detail": f"Bỏ rơi bài báo mới nhất (published={row.get('published', '')})",
            }
        )
    corrupted = corrupted.iloc[num_to_drop:].reset_index(drop=True)

    n_remaining = len(corrupted)

    # 2. Blank summary: Xóa trắng phần tóm tắt ở một số dòng
    if n_remaining > 0:
        idx_blank = [0]
        if n_remaining > 1:
            idx_blank.append(1)
        for i in idx_blank:
            paper_id = corrupted.at[i, "paper_id"]
            corrupted.at[i, "summary"] = ""
            corrupted.at[i, "summary_chars"] = 0
            logs.append(
                {
                    "operation": "blank_summary",
                    "paper_id": str(paper_id),
                    "detail": "Xóa rỗng nội dung summary",
                }
            )

    # 3. Inject noise: Chèn các chuỗi ký tự rác vào tóm tắt
    if n_remaining > 2:
        idx_noise = 2
        paper_id = corrupted.at[idx_noise, "paper_id"]
        original_summary = corrupted.at[idx_noise, "summary"]
        noise_str = " [CORRUPTED_NOISE: %$#@!?? INVALID_BYTE_SEQUENCE 0xFF 0xAA 0x99]"
        corrupted.at[idx_noise, "summary"] = str(original_summary) + noise_str
        corrupted.at[idx_noise, "summary_chars"] = len(corrupted.at[idx_noise, "summary"])
        logs.append(
            {
                "operation": "inject_noise",
                "paper_id": str(paper_id),
                "detail": f"Chèn ký tự rác vào summary: '{noise_str}'",
            }
        )

    # 4. Truncate title: Cắt ngắn tiêu đề xuống dưới 8 ký tự
    if n_remaining > 3:
        idx_trunc = 3
        paper_id = corrupted.at[idx_trunc, "paper_id"]
        original_title = corrupted.at[idx_trunc, "title"]
        corrupted.at[idx_trunc, "title"] = (
            str(original_title)[:5] if len(str(original_title)) > 5 else "Short"
        )
        logs.append(
            {
                "operation": "truncate_title",
                "paper_id": str(paper_id),
                "detail": f"Cắt ngắn tiêu đề từ '{original_title}' xuống còn '{corrupted.at[idx_trunc, 'title']}' (< 8 ký tự)",
            }
        )

    # 5. Stale date: Lùi ngày xuất bản về 365 ngày trước
    if n_remaining > 4:
        idx_stale = 4
        paper_id = corrupted.at[idx_stale, "paper_id"]
        original_pub = str(corrupted.at[idx_stale, "published"])
        try:
            pub_date = datetime.strptime(original_pub[:10], "%Y-%m-%d")
            stale_pub = (pub_date - timedelta(days=365)).strftime("%Y-%m-%d")
        except Exception:
            stale_pub = "2020-01-01"
        corrupted.at[idx_stale, "published"] = stale_pub
        if "age_days" in corrupted.columns:
            corrupted.at[idx_stale, "age_days"] = int(corrupted.at[idx_stale, "age_days"]) + 365
        logs.append(
            {
                "operation": "stale_date",
                "paper_id": str(paper_id),
                "detail": f"Lùi ngày xuất bản từ {original_pub} về {stale_pub} (+365 ngày tuổi)",
            }
        )

    # 6. Duplicate rows: Nhân đôi các dòng để tạo trùng lặp
    if n_remaining > 5:
        rows_to_dup = corrupted.iloc[5:7].copy()
        for _, row in rows_to_dup.iterrows():
            logs.append(
                {
                    "operation": "duplicate_rows",
                    "paper_id": str(row.get("paper_id", "")),
                    "detail": "Nhân đôi dòng bản ghi để tạo vi phạm trùng lặp (duplicate)",
                }
            )
        corrupted = pd.concat([corrupted, rows_to_dup], ignore_index=True)

    # 7. Tái tạo lại trường text_for_embedding đồng bộ với các trường đã biến đổi
    corrupted["text_for_embedding"] = (
        "Title: "
        + corrupted["title"].astype(str)
        + "\nAuthors: "
        + corrupted["authors_joined"].astype(str)
        + "\nPublished: "
        + corrupted["published"].astype(str)
        + "\nCategories: "
        + corrupted["categories_joined"].astype(str)
        + "\nSummary: "
        + corrupted["summary"].astype(str)
    )

    # Ghi nhật ký biến đổi ra file
    log_path = Path(output_log_path)
    write_json(log_path, logs)

    return corrupted

