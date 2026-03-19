from __future__ import annotations
import pandas as pd
from pathlib import Path
from scripts.common import root_path, write_csv

def approx_equal(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol

def main() -> None:
    diesel = pd.read_parquet(root_path("data/marts/fleet_diesel_estimates.parquet")).copy()
    tier_counts = pd.read_csv(root_path("outputs/tables/tier_counts_assigned_weighted.csv")).copy()
    national_diesel = pd.read_csv(root_path("outputs/tables/national_diesel_by_tier.csv")).copy()
    regional_total = pd.read_csv(root_path("outputs/tables/regional_diesel_total.csv")).copy()
    def_summary = pd.read_csv(root_path("outputs/tables/def_summary.csv")).copy()
    internal = pd.read_csv(root_path("data/staging/internal_tier_summary.csv")).copy()

    diesel.columns = [c.strip().lower() for c in diesel.columns]
    tier_counts.columns = [c.strip().lower() for c in tier_counts.columns]
    national_diesel.columns = [c.strip().lower() for c in national_diesel.columns]
    regional_total.columns = [c.strip().lower() for c in regional_total.columns]
    def_summary.columns = [c.strip().lower() for c in def_summary.columns]
    internal.columns = [c.strip().lower() for c in internal.columns]

    fleet_total_model = float(diesel["weighted_tractor_count"].sum())
    diesel_total_model_ml = float(diesel["annual_diesel_litres"].sum() / 1_000_000)

    fleet_total_internal = float(internal["count"].sum())
    diesel_total_internal_ml = float(internal["fuel_ml"].sum())

    national_diesel_sum_ml = float(national_diesel["annual_diesel_litres"].sum() / 1_000_000)
    regional_diesel_sum_ml = float(regional_total["annual_diesel_litres"].sum() / 1_000_000)

    scr_count = float(def_summary.loc[0, "weighted_scr_tractor_count"])
    scr_diesel_ml = float(def_summary.loc[0, "scr_diesel_ml"])
    def_low_ml = float(def_summary.loc[0, "def_low_ml"])
    def_central_ml = float(def_summary.loc[0, "def_central_ml"])
    def_high_ml = float(def_summary.loc[0, "def_high_ml"])

    checks = pd.DataFrame([
        {
            "check_name": "fleet_total_vs_internal",
            "actual": fleet_total_model,
            "expected": fleet_total_internal,
            "difference": fleet_total_model - fleet_total_internal,
            "pass": approx_equal(fleet_total_model, fleet_total_internal, tol=5)
        },
        {
            "check_name": "diesel_total_vs_internal_ml",
            "actual": diesel_total_model_ml,
            "expected": diesel_total_internal_ml,
            "difference": diesel_total_model_ml - diesel_total_internal_ml,
            "pass": approx_equal(diesel_total_model_ml, diesel_total_internal_ml, tol=0.01)
        },
        {
            "check_name": "national_diesel_sum_vs_model_ml",
            "actual": national_diesel_sum_ml,
            "expected": diesel_total_model_ml,
            "difference": national_diesel_sum_ml - diesel_total_model_ml,
            "pass": approx_equal(national_diesel_sum_ml, diesel_total_model_ml, tol=0.01)
        },
        {
            "check_name": "regional_diesel_sum_vs_model_ml",
            "actual": regional_diesel_sum_ml,
            "expected": diesel_total_model_ml,
            "difference": regional_diesel_sum_ml - diesel_total_model_ml,
            "pass": approx_equal(regional_diesel_sum_ml, diesel_total_model_ml, tol=0.01)
        },
        {
            "check_name": "def_low_vs_scr_3pct",
            "actual": def_low_ml,
            "expected": scr_diesel_ml * 0.03,
            "difference": def_low_ml - (scr_diesel_ml * 0.03),
            "pass": approx_equal(def_low_ml, scr_diesel_ml * 0.03, tol=0.001)
        },
        {
            "check_name": "def_central_vs_scr_4pct",
            "actual": def_central_ml,
            "expected": scr_diesel_ml * 0.04,
            "difference": def_central_ml - (scr_diesel_ml * 0.04),
            "pass": approx_equal(def_central_ml, scr_diesel_ml * 0.04, tol=0.001)
        },
        {
            "check_name": "def_high_vs_scr_5pct",
            "actual": def_high_ml,
            "expected": scr_diesel_ml * 0.05,
            "difference": def_high_ml - (scr_diesel_ml * 0.05),
            "pass": approx_equal(def_high_ml, scr_diesel_ml * 0.05, tol=0.001)
        }
    ])

    write_csv(checks, "outputs/tables/validation_checks.csv")

    print("Validation checks:")
    print(checks.to_string(index=False))

if __name__ == "__main__":
    main()
