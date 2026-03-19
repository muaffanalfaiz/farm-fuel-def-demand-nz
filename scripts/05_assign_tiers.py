from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_parquet, write_csv

def assign_cohort(vehicle_year) -> str:
    y = pd.to_numeric(pd.Series([vehicle_year]), errors="coerce").iloc[0]
    if pd.isna(y):
        return "Unknown"
    y = int(y)
    if y < 1996:
        return "Pre-1996"
    elif 1996 <= y <= 1999:
        return "1996-1999"
    elif 2000 <= y <= 2005:
        return "2000-2005"
    elif 2006 <= y <= 2010:
        return "2006-2010"
    elif 2011 <= y <= 2013:
        return "2011-2013"
    elif 2014 <= y <= 2018:
        return "2014-2018"
    elif 2019 <= y <= 2020:
        return "2019-2020"
    else:
        return "2021-2025"

def main() -> None:
    fleet = pd.read_parquet(root_path("data/staging/nzta_tractors.parquet")).copy()
    cohort_map = pd.read_csv(root_path("data/staging/internal_cohort_tier_distribution.csv")).copy()

    fleet.columns = [c.strip().lower() for c in fleet.columns]
    cohort_map.columns = [c.strip().lower() for c in cohort_map.columns]

    if "motive_power" in fleet.columns:
        fleet["motive_power"] = fleet["motive_power"].astype(str).str.upper().str.strip()
        fleet = fleet.loc[fleet["motive_power"] == "DIESEL"].copy()

    if "body_type" in fleet.columns:
        fleet["body_type"] = fleet["body_type"].astype(str).str.upper().str.strip()
        fleet = fleet.loc[fleet["body_type"] == "TRACTOR"].copy()

    fleet["vehicle_year"] = pd.to_numeric(fleet.get("vehicle_year"), errors="coerce")
    fleet["cohort"] = fleet["vehicle_year"].apply(assign_cohort)

    group_col = "tla" if "tla" in fleet.columns else ("postcode" if "postcode" in fleet.columns else "geo_unit")
    if group_col == "geo_unit":
        fleet[group_col] = "National"

    # Raw cohort x geography template
    raw_cohort_geo = (
        fleet.groupby(["cohort", group_col], dropna=False)
        .size()
        .reset_index(name="raw_count")
    )

    raw_cohort_totals = (
        raw_cohort_geo.groupby("cohort", dropna=False)["raw_count"]
        .sum()
        .reset_index(name="raw_cohort_total")
    )

    raw_cohort_geo = raw_cohort_geo.merge(raw_cohort_totals, on="cohort", how="left")
    raw_cohort_geo["raw_geo_share"] = raw_cohort_geo["raw_count"] / raw_cohort_geo["raw_cohort_total"]

    official_cohort_totals = (
        cohort_map[["cohort", "fleet"]]
        .drop_duplicates()
        .rename(columns={"fleet": "official_active_licensed_cohort_total"})
        .copy()
    )
    official_cohort_totals["official_active_licensed_cohort_total"] = pd.to_numeric(
        official_cohort_totals["official_active_licensed_cohort_total"], errors="coerce"
    )

    raw_cohort_geo = raw_cohort_geo.merge(official_cohort_totals, on="cohort", how="left")
    raw_cohort_geo["active_licensed_count_geo_cohort"] = (
        raw_cohort_geo["raw_geo_share"] * raw_cohort_geo["official_active_licensed_cohort_total"]
    )

    cohort_tier_shares = cohort_map[["cohort", "tier", "share"]].copy()
    cohort_tier_shares["share"] = pd.to_numeric(cohort_tier_shares["share"], errors="coerce")

    fleet_tier_geo = raw_cohort_geo.merge(cohort_tier_shares, on="cohort", how="left")
    fleet_tier_geo = fleet_tier_geo.rename(
        columns={"tier": "tier_assigned", "share": "tier_share_within_cohort"}
    )

    fleet_tier_geo["weighted_tractor_count"] = (
        fleet_tier_geo["active_licensed_count_geo_cohort"] * fleet_tier_geo["tier_share_within_cohort"]
    )

    write_parquet(fleet_tier_geo, "data/marts/fleet_with_tiers.parquet")

    national_counts = (
        fleet_tier_geo.groupby("tier_assigned", dropna=False)["weighted_tractor_count"]
        .sum()
        .reset_index()
        .sort_values("weighted_tractor_count", ascending=False)
    )

    cohort_counts = (
        fleet_tier_geo.groupby(["cohort", "tier_assigned"], dropna=False)["weighted_tractor_count"]
        .sum()
        .reset_index()
        .sort_values(["cohort", "weighted_tractor_count"], ascending=[True, False])
    )

    # FIX: regional active licensed count must come from raw_cohort_geo before tier expansion
    regional_active = (
        raw_cohort_geo.groupby(group_col, dropna=False)["active_licensed_count_geo_cohort"]
        .sum()
        .reset_index()
        .sort_values("active_licensed_count_geo_cohort", ascending=False)
    )

    write_csv(national_counts, "outputs/tables/tier_counts_assigned_weighted.csv")
    write_csv(cohort_counts, "outputs/tables/cohort_tier_counts_weighted.csv")
    write_csv(regional_active, "outputs/tables/regional_active_licensed_template.csv")

    official_total = official_cohort_totals["official_active_licensed_cohort_total"].sum()
    modeled_total = national_counts["weighted_tractor_count"].sum()
    regional_active_total = regional_active["active_licensed_count_geo_cohort"].sum()

    print(f"Raw diesel tractor rows used as template: {len(fleet):,}")
    print(f"Geographic template grouping column: {group_col}")
    print(f"Official active licensed total imposed: {official_total:,.2f}")
    print(f"Weighted national total after cohort-tier allocation: {modeled_total:,.2f}")
    print(f"Regional active licensed total: {regional_active_total:,.2f}")
    print("\\nWeighted national tier counts:")
    print(national_counts.to_string(index=False))

if __name__ == "__main__":
    main()
