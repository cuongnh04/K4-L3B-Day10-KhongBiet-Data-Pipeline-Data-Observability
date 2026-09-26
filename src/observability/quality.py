from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    import great_expectations as gx
    import great_expectations.expectations as gxe
    import json

    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name="papers_suite")
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=100000))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=1))

    validation_result = batch.validate(suite)
    res_dict = validation_result.to_json_dict()
    
    out_dir = settings.paths.data_dir / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report_name}_quality.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res_dict, f, indent=2)
        
    return res_dict

def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    import json
    
    if df.empty:
        return {}
        
    latest_published = df['published'].max().isoformat()
    oldest_published = df['published'].min().isoformat()
    
    stale_rows = int((df['age_days'] > 180).sum())
    total_rows = len(df)
    
    stale_ratio = stale_rows / total_rows if total_rows > 0 else 0
    is_fresh = stale_ratio <= 0.25
    
    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    return payload
