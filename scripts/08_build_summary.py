from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_csv

def main() -> None:
    diesel = pd.read_parquet(root_path("data/marts/fleet_diesel_estimates.parquet")).copy()
    def_summary = pd.read_csv(root_path("outputs/tables/def_summary.csv")).copy()
    tier_counts = pd.read_csv(root_path("outputs/tables/tier_counts_assigned_weighted.csv")).copy()
    internal = pd.read_csv(root_path("data/staging/internal_tier_summary.csv")).copy()

    diesel.columns = [c.strip().lower() for c in diesel.columns]
    def_summary.columns = [c.strip().lower() for c in def_summary.columns]
    tier_counts.columns = [c.strip().lower() for c in tier_counts.columns]
    internal.columns = [c.strip().lower() for c in internal.columns]

    national_fleet = diesel["weighted_tractor_count"].sum()
    national_diesel_l = diesel["annual_diesel_litres"].sum()
    national_diesel_ml = national_diesel_l / 1_000_000

    internal_total_count = internal["count"].sum()
    internal_total_diesel_ml = internal["fuel_ml"].sum()

    out = pd.DataFrame([{
        "project_active_licensed_weighted_fleet": national_fleet,
        "project_national_diesel_ml": national_diesel_ml,
        "internal_reference_fleet_total": internal_total_count,
        "internal_reference_diesel_ml": internal_total_diesel_ml,
        "fleet_difference_vs_internal": national_fleet - internal_total_count,
        "diesel_difference_ml_vs_internal": national_diesel_ml - internal_total_diesel_ml,
        "weighted_scr_tractor_count": def_summary.loc[0, "weighted_scr_tractor_count"],
        "scr_diesel_ml": def_summary.loc[0, "scr_diesel_ml"],
        "def_low_ml": def_summary.loc[0, "def_low_ml"],
        "def_central_ml": def_summary.loc[0, "def_central_ml"],
        "def_high_ml": def_summary.loc[0, "def_high_ml"]
    }])

    write_csv(out, "outputs/tables/project_summary.csv")
    print(out.to_string(index=False))

if __name__ == "__main__":
    main()
