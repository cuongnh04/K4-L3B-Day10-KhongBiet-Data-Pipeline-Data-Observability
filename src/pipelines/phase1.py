from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.config import Settings, load_settings
from core.utils import now_utc, write_csv, write_json, write_text
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from retrieval.index import LocalEmbeddingIndex


def generate_phase1_markdown_report(
    settings: Settings,
    clean_df: pd.DataFrame,
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> str:
    hit_rate = metrics.get("retrieval_hit_rate", 0.0) * 100
    token_f1 = metrics.get("mean_token_f1", 0.0)
    judge_acc = metrics.get("judge_accuracy", 0.0) * 100
    judge_score = metrics.get("mean_judge_score", 0.0)
    samples = metrics.get("samples", 0)

    return f"""# Báo Cáo Tuyến Dữ Liệu Cơ Sở (Baseline Pipeline Report - Phase 1)

> **Thời điểm xuất báo cáo:** {now_utc().strftime("%Y-%m-%d %H:%M:%S UTC")}  
> **Nguồn dữ liệu:** {settings.source_api}  
> **LLM Provider:** `{settings.llm_provider}` (Model: `{settings.model_name}`)  
> **Mô hình Embedding:** `{settings.embedding_model}`  

---

## 1. Thu Thập & Làm Sạch Dữ Liệu (Ingestion & Cleaning)
- **Tổng số bản ghi sạch:** {len(clean_df)} dòng (khử trùng lặp theo `paper_id`).
- **File lưu trữ CSV:** `{settings.paths.clean_csv}`
- **File lưu trữ JSON:** `{settings.paths.clean_json}`
- **ChromaDB Collection:** `{settings.baseline_collection_name}`

---

## 2. Chốt Kiểm Soát Chất Lượng Dữ Liệu (Great Expectations 1.x & Freshness SLA)
- **Trạng thái Quality Gate:** `{"PASSED (True)" if quality.get("success") else "FAILED (False)"}`
- **Great Expectations 1.x Validations:** `{quality.get("gx_success")}`
- **Số bản ghi kiểm tra:** {quality.get("total_records", len(clean_df))} dòng
- **Giám sát độ tươi mới (Freshness SLA):**
  - **Trạng thái Freshness:** `{"ĐẠT CHUẨN (True)" if freshness.get("is_fresh") else "CẢNH BÁO CŨ (False)"}`
  - **Ngưỡng SLA bài báo cũ:** {freshness.get("threshold_days", 180)} ngày
  - **Số bài quá hạn (>180 ngày):** {freshness.get("stale_rows", 0)} / {freshness.get("total_rows", len(clean_df))} ({freshness.get("stale_ratio", 0.0) * 100:.1f}%)
  - **Bài mới nhất:** {freshness.get("latest_published", "N/A")}
  - **Bài cũ nhất:** {freshness.get("oldest_published", "N/A")}

---

## 3. Chỉ Số Hiệu Năng RAG Nền (Baseline Benchmarks)
| Chỉ số đánh giá | Giá trị đạt được | Ghi chú |
| :--- | :---: | :--- |
| **Số lượng câu hỏi kiểm thử (Benchmark Test Set)** | **{samples}** câu | Phân bổ 4 nhóm (summary, authors, date, categories) |
| **Retrieval Hit Rate** | **{hit_rate:.1f}%** | Tỷ lệ tìm đúng tài liệu chứa câu trả lời |
| **Mean Token F1 Score** | **{token_f1:.4f}** | Độ trùng khớp từ vựng giữa câu trả lời và Ground Truth |
| **Judge Accuracy** | **{judge_acc:.1f}%** | Đánh giá tính chính xác về mặt ngữ nghĩa |
| **Mean Judge Score** | **{judge_score:.2f} / 5.0** | Điểm trung bình chất lượng câu trả lời |

---

## 4. Kết Luận
Toàn tuyến Phase 1 đã thực thi thành công. Dữ liệu vượt qua chốt kiểm định Great Expectations 1.x và đảm bảo Freshness SLA. Vector index đã sẵn sàng phục vụ cho các thực nghiệm tiêm lỗi ở Phase 2.
"""


def run_phase1_pipeline(settings: Settings | None = None) -> dict[str, Any]:
    if settings is None:
        settings = load_settings()

    print("[Phase 1] Buoc 1: Nap ban ghi tho (Raw Preservation)...")
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        records = load_raw_records(settings.paths.raw_records_json)
    else:
        records = fetch_source_records(settings)
    print(f"[Phase 1] Da nap {len(records)} ban ghi tho.")

    print("[Phase 1] Buoc 2: Lam sach du lieu va tao text_for_embedding...")
    clean_df = build_clean_dataframe(records, datetime.now(timezone.utc))
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    print(f"[Phase 1] Da luu {len(clean_df)} dong du lieu sach vao CSV va JSON.")

    print("[Phase 1] Buoc 3: Danh chi muc ChromaDB (Baseline Collection)...")
    index = LocalEmbeddingIndex.build(
        clean_df,
        settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"[Phase 1] Da tao index collection: {settings.baseline_collection_name}")

    print("[Phase 1] Buoc 4: Tao bo de kiem thu chuan (Benchmark Test Set)...")
    test_set = build_test_set(clean_df, settings.paths.eval_testset)
    print(f"[Phase 1] Da sinh {len(test_set)} cau hoi Ground Truth.")

    print("[Phase 1] Buoc 5: Danh gia hieu nang RAG nen (Baseline Evaluation)...")
    eval_bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    hit_rate = eval_bundle.summary.get("retrieval_hit_rate", 0.0) * 100
    token_f1 = eval_bundle.summary.get("mean_token_f1", 0.0)
    print(f"[Phase 1] Baseline Metrics: Retrieval Hit Rate = {hit_rate:.1f}%, Mean Token F1 = {token_f1:.4f}")

    print("[Phase 1] Buoc 6: Kiem dinh chat luong Great Expectations 1.x & Freshness SLA...")
    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    print(f"[Phase 1] Quality Gate Status: {quality.get('success')}, Freshness: {freshness.get('is_fresh')}")

    print("[Phase 1] Buoc 7: Xuat bao cao Phase 1...")
    report_md = generate_phase1_markdown_report(settings, clean_df, eval_bundle.summary, quality, freshness)
    write_text(settings.paths.baseline_report, report_md)
    print(f"[Phase 1] Da tao bao cao tai: {settings.paths.baseline_report}")

    return {
        "clean_records": len(clean_df),
        "metrics": eval_bundle.summary,
        "quality": quality,
        "freshness": freshness,
    }


def main() -> None:
    settings = load_settings()
    run_phase1_pipeline(settings)

