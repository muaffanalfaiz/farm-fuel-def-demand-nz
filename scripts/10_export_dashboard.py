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
    copy_if_exists("outputs/tables/regional_diesel_by_tier.csv", "dashboard/regional_diesel_by_tier.csv")
    copy_if_exists("outputs/tables/regional_def_estimates.csv", "dashboard/regional_def_estimates.csv")
    copy_if_exists("outputs/predictions/feature_importance.csv", "dashboard/feature_importance.csv")
    copy_if_exists("outputs/predictions/model_metrics.csv", "dashboard/model_metrics.csv")
    print("Exported dashboard-ready CSV files.")

if __name__ == "__main__":
    main()
