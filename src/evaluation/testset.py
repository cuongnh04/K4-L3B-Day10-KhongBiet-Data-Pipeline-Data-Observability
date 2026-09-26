from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Tạo bộ đề kiểm thử Ground Truth gồm 10 câu hỏi thuộc 4 dạng: summary, authors, date, categories."""
    if len(df) < 10:
        raise ValueError(f"Dữ liệu cần tối thiểu 10 bản ghi để sinh test set, hiện có {len(df)} dòng.")

    # Chọn 10 bài báo đại diện phân bổ đều
    records = df.to_dict(orient="records")[:10]
    test_set: list[dict[str, Any]] = []

    # Phân bổ: 3 câu summary, 3 câu authors, 2 câu date, 2 câu categories
    specs = [
        ("summary", 0, "What is the summary of the paper '{title}'?", lambda r: first_sentence(r["summary"])),
        ("summary", 1, "What is the summary of the paper '{title}'?", lambda r: first_sentence(r["summary"])),
        ("summary", 2, "What is the summary of the paper '{title}'?", lambda r: first_sentence(r["summary"])),
        ("authors", 3, "Who are the authors of the paper '{title}'?", lambda r: str(r["authors_joined"])),
        ("authors", 4, "Who are the authors of the paper '{title}'?", lambda r: str(r["authors_joined"])),
        ("authors", 5, "Who are the authors of the paper '{title}'?", lambda r: str(r["authors_joined"])),
        ("date", 6, "When was the paper '{title}' published?", lambda r: str(r["published"])),
        ("date", 7, "When was the paper '{title}' published?", lambda r: str(r["published"])),
        ("categories", 8, "What are the primary categories of the paper '{title}'?", lambda r: str(r["categories_joined"])),
        ("categories", 9, "What are the primary categories of the paper '{title}'?", lambda r: str(r["categories_joined"])),
    ]

    for q_idx, (q_type, r_idx, q_template, gt_func) in enumerate(specs, start=1):
        row = records[r_idx]
        title = row["title"]
        paper_id = row["paper_id"]
        question = q_template.format(title=title)
        ground_truth = gt_func(row)

        test_set.append(
            {
                "id": f"eval_{q_idx:03d}",
                "question_type": q_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    out_p = Path(output_path)
    write_json(out_p, test_set)
    return test_set

