from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_parquet, write_csv

def main() -> None:
    fleet = pd.read_parquet(root_path("data/marts/fleet_with_tiers.parquet")).copy()
    tier_summary = pd.read_csv(root_path("data/staging/internal_tier_summary.csv")).copy()

    fleet.columns = [c.strip().lower() for c in fleet.columns]
    tier_summary.columns = [c.strip().lower() for c in tier_summary.columns]

    tier_summary["count"] = pd.to_numeric(tier_summary["count"], errors="coerce")
    tier_summary["fuel_ml"] = pd.to_numeric(tier_summary["fuel_ml"], errors="coerce")
    tier_summary["litres_per_tractor"] = (tier_summary["fuel_ml"] * 1_000_000) / tier_summary["count"]

    tier_lpt = tier_summary[["tier", "litres_per_tractor"]].rename(columns={"tier": "tier_assigned"})
    fleet = fleet.merge(tier_lpt, on="tier_assigned", how="left")

    fleet["weighted_tractor_count"] = pd.to_numeric(fleet["weighted_tractor_count"], errors="coerce").fillna(0)
    fleet["annual_diesel_litres"] = fleet["weighted_tractor_count"] * fleet["litres_per_tractor"]

    group_col = "tla" if "tla" in fleet.columns else ("postcode" if "postcode" in fleet.columns else "geo_unit")
    if group_col == "geo_unit":
        fleet[group_col] = "National"

    regional = (
        fleet.groupby([group_col, "tier_assigned"], dropna=False)["annual_diesel_litres"]
        .sum()
        .reset_index()
        .sort_values("annual_diesel_litres", ascending=False)
    )

    national = (
        fleet.groupby("tier_assigned", dropna=False)
        .agg(
            weighted_tractor_count=("weighted_tractor_count", "sum"),
            annual_diesel_litres=("annual_diesel_litres", "sum")
        )
        .reset_index()
        .sort_values("annual_diesel_litres", ascending=False)
    )

    regional_total = (
        fleet.groupby(group_col, dropna=False)["annual_diesel_litres"]
        .sum()
        .reset_index()
        .sort_values("annual_diesel_litres", ascending=False)
    )

    write_parquet(fleet, "data/marts/fleet_diesel_estimates.parquet")
    write_csv(regional, "outputs/tables/regional_diesel_by_tier.csv")
    write_csv(national, "outputs/tables/national_diesel_by_tier.csv")
    write_csv(regional_total, "outputs/tables/regional_diesel_total.csv")

    total_l = fleet["annual_diesel_litres"].sum()
    total_ml = total_l / 1_000_000

    national["annual_diesel_ml"] = national["annual_diesel_litres"] / 1_000_000

    print(f"Using grouping column: {group_col}")
    print(f"National active licensed fleet (weighted): {fleet['weighted_tractor_count'].sum():,.2f}")
    print(f"National diesel total (L): {total_l:,.2f}")
    print(f"National diesel total (ML): {total_ml:,.3f}")
    print("\\nNational diesel by tier (ML):")
    print(national[['tier_assigned', 'weighted_tractor_count', 'annual_diesel_ml']].to_string(index=False))

if __name__ == "__main__":
    main()
