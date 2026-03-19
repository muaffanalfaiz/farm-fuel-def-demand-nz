from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_csv

def validate_required_files() -> None:
    required = [
        "data/raw/internal/tier_summary.csv",
        "data/raw/internal/cohort_tier_distribution.csv",
        "data/raw/internal/def_rules.csv",
    ]
    for rel in required:
        p = root_path(rel)
        if not p.exists():
            raise FileNotFoundError(f"Missing required internal file: {p}")

def main() -> None:
    validate_required_files()
    tier = pd.read_csv(root_path("data/raw/internal/tier_summary.csv"))
    cohort = pd.read_csv(root_path("data/raw/internal/cohort_tier_distribution.csv"))
    rules = pd.read_csv(root_path("data/raw/internal/def_rules.csv"))

    # Basic standardisation
    tier.columns = [c.strip().lower() for c in tier.columns]
    cohort.columns = [c.strip().lower() for c in cohort.columns]
    rules.columns = [c.strip().lower() for c in rules.columns]

    write_csv(tier, "data/staging/internal_tier_summary.csv")
    write_csv(cohort, "data/staging/internal_cohort_tier_distribution.csv")
    write_csv(rules, "data/staging/internal_def_rules.csv")
    print("Prepared internal tables.")

if __name__ == "__main__":
    main()
