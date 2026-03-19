from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_csv

BASELINE_NAME = "baseline_current_structure"

def main() -> None:
    national = pd.read_csv(root_path("outputs/scenarios/scenario_national_summary.csv")).copy()
    regional = pd.read_csv(root_path("outputs/scenarios/scenario_regional_summary.csv")).copy()

    national.columns = [c.strip().lower() for c in national.columns]
    regional.columns = [c.strip().lower() for c in regional.columns]

    baseline_nat = national.loc[national["scenario_name"] == BASELINE_NAME].copy()
    if len(baseline_nat) != 1:
        raise ValueError("Expected exactly one baseline scenario row")

    baseline_nat = baseline_nat.iloc[0].to_dict()

    compare = national.copy()
    for col in ["national_diesel_ml", "national_scr_tractor_count", "national_scr_diesel_ml", "def_central_ml", "modern_tiers_share_pct", "scr_share_pct"]:
        compare[f"delta_{col}_vs_baseline"] = compare[col] - baseline_nat[col]
        if baseline_nat[col] != 0:
            compare[f"pct_delta_{col}_vs_baseline"] = (compare[col] - baseline_nat[col]) / baseline_nat[col] * 100
        else:
            compare[f"pct_delta_{col}_vs_baseline"] = None

    write_csv(compare, "outputs/scenarios/scenario_national_compare.csv")

    region_key_candidates = ["tla", "postcode", "geo_unit"]
    region_key = None
    for c in region_key_candidates:
        if c in regional.columns:
            region_key = c
            break
    if region_key is None:
        raise KeyError("No region key found in scenario_regional_summary")

    baseline_reg = regional.loc[regional["scenario_name"] == BASELINE_NAME, [region_key, "regional_diesel_ml", "def_central_ml"]].copy()
    baseline_reg = baseline_reg.rename(columns={
        "regional_diesel_ml": "baseline_regional_diesel_ml",
        "def_central_ml": "baseline_def_central_ml"
    })

    regional_compare = regional.merge(baseline_reg, on=region_key, how="left")
    regional_compare["delta_regional_diesel_ml_vs_baseline"] = regional_compare["regional_diesel_ml"] - regional_compare["baseline_regional_diesel_ml"]
    regional_compare["delta_def_central_ml_vs_baseline"] = regional_compare["def_central_ml"] - regional_compare["baseline_def_central_ml"]

    write_csv(regional_compare, "outputs/scenarios/scenario_regional_compare.csv")

    top_gains = (
        regional_compare.loc[regional_compare["scenario_name"] != BASELINE_NAME]
        .sort_values(["scenario_name", "delta_def_central_ml_vs_baseline"], ascending=[True, False])
        .groupby("scenario_name")
        .head(15)
        .copy()
    )
    write_csv(top_gains, "outputs/scenarios/scenario_top_regional_def_gains.csv")

    print("Scenario national comparison:")
    print(compare.to_string(index=False))
    print("\nTop regional DEF gains vs baseline:")
    print(top_gains[[region_key, "scenario_name", "def_central_ml", "delta_def_central_ml_vs_baseline"]].to_string(index=False))

if __name__ == "__main__":
    main()
