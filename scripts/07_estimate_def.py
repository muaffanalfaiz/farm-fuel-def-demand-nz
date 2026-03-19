from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_csv

def main() -> None:
    fleet = pd.read_parquet(root_path("data/marts/fleet_diesel_estimates.parquet")).copy()
    fleet.columns = [c.strip().lower() for c in fleet.columns]

    scr_tiers = {"Tier 4f", "Stage V"}
    fleet["def_required_flag"] = fleet["tier_assigned"].isin(scr_tiers).astype(int)

    scr = fleet.loc[fleet["def_required_flag"] == 1].copy()

    group_col = "tla" if "tla" in scr.columns else ("postcode" if "postcode" in scr.columns else "geo_unit")
    if group_col == "geo_unit":
        scr[group_col] = "National"

    total_scr_tractors = scr["weighted_tractor_count"].sum()
    total_scr_diesel_l = scr["annual_diesel_litres"].sum()

    summary = pd.DataFrame([{
        "weighted_scr_tractor_count": total_scr_tractors,
        "scr_diesel_litres": total_scr_diesel_l,
        "scr_diesel_ml": total_scr_diesel_l / 1_000_000,
        "def_low_ml": (total_scr_diesel_l * 0.03) / 1_000_000,
        "def_central_ml": (total_scr_diesel_l * 0.04) / 1_000_000,
        "def_high_ml": (total_scr_diesel_l * 0.05) / 1_000_000
    }])

    regional = (
        scr.groupby(group_col, dropna=False)["annual_diesel_litres"]
        .sum()
        .reset_index()
        .rename(columns={"annual_diesel_litres": "scr_diesel_litres"})
        .sort_values("scr_diesel_litres", ascending=False)
    )
    regional["def_low_litres"] = regional["scr_diesel_litres"] * 0.03
    regional["def_central_litres"] = regional["scr_diesel_litres"] * 0.04
    regional["def_high_litres"] = regional["scr_diesel_litres"] * 0.05

    write_csv(summary, "outputs/tables/def_summary.csv")
    write_csv(regional, "outputs/tables/regional_def_estimates.csv")

    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
