from __future__ import annotations

from pathlib import Path
from typing import Any
import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import write_json


def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Giám sát độ tươi mới của dữ liệu: Cảnh báo is_fresh=False nếu tỉ lệ bài cũ (>180 ngày) > 25%."""
    threshold = settings.freshness_threshold_days
    total_rows = len(df)
    stale_rows = int((df["age_days"] > threshold).sum()) if "age_days" in df.columns and total_rows > 0 else 0
    stale_ratio = stale_rows / total_rows if total_rows > 0 else 0.0
    is_fresh = stale_ratio <= 0.25

    latest_published = str(df["published"].max()) if "published" in df.columns and not df.empty else ""
    oldest_published = str(df["published"].min()) if "published" in df.columns and not df.empty else ""

    return {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "threshold_days": threshold,
        "is_fresh": is_fresh,
    }


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | str) -> dict[str, Any]:
    """Tổng hợp và lưu báo cáo độ tươi mới ra file JSON."""
    report = evaluate_freshness_sla(df, settings)
    write_json(Path(report_path), report)
    return report


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Thiết lập chốt kiểm soát chất lượng dữ liệu với 4 Expectations bắt buộc của Great Expectations 1.x."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name=f"papers_{report_name}_suite")

    # 1. ExpectTableRowCountToBeBetween: 5 đến 5000 dòng
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
    # 2. ExpectColumnValuesToNotBeNull: paper_id, title, text_for_embedding
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    # 3. ExpectColumnValuesToBeUnique: paper_id là duy nhất
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
    # 4. ExpectColumnValueLengthsToBeBetween: summary có độ dài tối thiểu 30 ký tự
    suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))

    val_res = batch.validate(suite)

    # Đánh giá độ tươi mới SLA
    freshness = evaluate_freshness_sla(df, settings)

    overall_success = bool(val_res.success and freshness["is_fresh"])

    expectation_results = []
    for r in val_res.results:
        exp_config = r.expectation_config
        expectation_results.append(
            {
                "expectation_type": exp_config.type if hasattr(exp_config, "type") else str(type(exp_config)),
                "success": bool(r.success),
                "kwargs": dict(exp_config.kwargs) if hasattr(exp_config, "kwargs") else {},
                "result": dict(r.result) if hasattr(r, "result") else {},
            }
        )

    result_payload: dict[str, Any] = {
        "report_name": report_name,
        "success": overall_success,
        "gx_success": bool(val_res.success),
        "total_records": len(df),
        "freshness": freshness,
        "expectations": expectation_results,
    }

    report_file = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(report_file, result_payload)

    return result_payload

