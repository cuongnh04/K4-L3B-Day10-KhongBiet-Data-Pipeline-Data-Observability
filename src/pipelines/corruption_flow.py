from __future__ import annotations


def main() -> None:
    import pandas as pd
    from core.config import load_settings
    from ingestion.corruption import corrupt_clean_dataframe
    from ingestion.cleaning import build_clean_dataframe
    from ingestion.crossref import load_raw_records
    from observability.quality import run_data_quality_checks, build_freshness_report
    from observability.reporting import build_corruption_report
    from evaluation.metrics import evaluate_test_set
    from retrieval.index import LocalEmbeddingIndex
    from core.utils import read_json, write_json
    from datetime import datetime, timezone
    import os

    settings = load_settings()
    
    # 1. Load baseline metrics va clean dataset
    if not settings.paths.clean_json.exists():
        raise FileNotFoundError("Please run baseline phase 1 first.")
    df_clean = pd.read_json(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    
    # 2. Tao corrupted dataframe
    df_corrupted = corrupt_clean_dataframe(df_clean.copy(), settings)
    
    # 3. Save corrupted artifacts
    df_corrupted.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2)
    df_corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False)
    
    # 4. Rebuild index va evaluate
    corrupted_index = LocalEmbeddingIndex.build(df_corrupted, settings, settings.paths.corrupted_embeddings_json)
    corrupted_metrics = evaluate_test_set(corrupted_index, settings, settings.paths.corrupted_answers)
    write_json(settings.paths.corrupted_metrics, corrupted_metrics)
    
    # 5. Run quality checks/freshness tren corrupted data
    run_data_quality_checks(df_corrupted, settings, "corrupted")
    build_freshness_report(df_corrupted, settings, settings.paths.quality_dir / "corrupted_freshness.json")
    
    # 6. Repair lai tu raw records
    raw_records = load_raw_records(settings.paths.raw_records_json)
    run_date = datetime.now(timezone.utc)
    df_repaired = build_clean_dataframe(raw_records, run_date)
    df_repaired.to_json(settings.paths.repaired_clean_json, orient="records", indent=2)
    df_repaired.to_csv(settings.paths.repaired_clean_csv, index=False)
    
    # 7. Evaluate repaired dataset
    repaired_index = LocalEmbeddingIndex.build(df_repaired, settings, settings.paths.repaired_embeddings_json)
    repaired_metrics = evaluate_test_set(repaired_index, settings, settings.paths.repaired_answers)
    write_json(settings.paths.repaired_metrics, repaired_metrics)
    
    # 8. Tao comparison report
    build_corruption_report(baseline_metrics, corrupted_metrics, repaired_metrics, settings.paths.comparison_report)
    print("Corruption flow pipeline completed successfully.")
