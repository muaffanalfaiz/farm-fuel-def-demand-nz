from __future__ import annotations
import shutil
from pathlib import Path
from scripts.common import root_path

def copy_if_exists(src_rel: str, dst_rel: str) -> None:
    src = root_path(src_rel)
    dst = root_path(dst_rel)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dst)

def main() -> None:
    files = [
        ("outputs/tables/project_summary.csv", "dashboard/project_summary.csv"),
        ("outputs/tables/validation_checks.csv", "dashboard/validation_checks.csv"),
        ("outputs/tables/regional_master_table.csv", "dashboard/regional_master_table.csv"),
        ("outputs/tables/regional_feature_store.csv", "dashboard/regional_feature_store.csv"),
        ("outputs/tables/geography_qa_summary.csv", "dashboard/geography_qa_summary.csv"),
        ("outputs/tables/geography_qa_flags.csv", "dashboard/geography_qa_flags.csv"),

        ("outputs/scenarios/scenario_national_summary.csv", "dashboard/scenario_national_summary.csv"),
        ("outputs/scenarios/scenario_national_compare.csv", "dashboard/scenario_national_compare.csv"),
        ("outputs/scenarios/scenario_regional_summary.csv", "dashboard/scenario_regional_summary.csv"),
        ("outputs/scenarios/scenario_regional_compare.csv", "dashboard/scenario_regional_compare.csv"),
        ("outputs/scenarios/scenario_top_regional_def_gains.csv", "dashboard/scenario_top_regional_def_gains.csv"),

        ("outputs/forecast/forecast_national_annual.csv", "dashboard/forecast_national_annual.csv"),
        ("outputs/forecast/forecast_national_by_tier_annual.csv", "dashboard/forecast_national_by_tier_annual.csv"),
        ("outputs/forecast/forecast_regional_annual.csv", "dashboard/forecast_regional_annual.csv"),
        ("outputs/forecast/forecast_top15_regional_def_2030.csv", "dashboard/forecast_top15_regional_def_2030.csv"),
    ]

    for src, dst in files:
        copy_if_exists(src, dst)

    print("Dashboard export complete: core + scenarios + forecast")

if __name__ == "__main__":
    main()
