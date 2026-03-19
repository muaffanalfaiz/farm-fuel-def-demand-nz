from __future__ import annotations
import pandas as pd
from scripts.common import root_path, write_csv

def main() -> None:
    regional_active = pd.read_csv(root_path("outputs/tables/regional_active_licensed_template.csv")).copy()
    regional_total = pd.read_csv(root_path("outputs/tables/regional_diesel_total.csv")).copy()
    regional_by_tier = pd.read_csv(root_path("outputs/tables/regional_diesel_by_tier.csv")).copy()
    regional_def = pd.read_csv(root_path("outputs/tables/regional_def_estimates.csv")).copy()
    project_summary = pd.read_csv(root_path("outputs/tables/project_summary.csv")).copy()

    regional_active.columns = [c.strip().lower() for c in regional_active.columns]
    regional_total.columns = [c.strip().lower() for c in regional_total.columns]
    regional_by_tier.columns = [c.strip().lower() for c in regional_by_tier.columns]
    regional_def.columns = [c.strip().lower() for c in regional_def.columns]
    project_summary.columns = [c.strip().lower() for c in project_summary.columns]

    # detect regional key
    region_key_candidates = ["tla", "postcode", "geo_unit"]
    region_key = None
    for c in region_key_candidates:
        if c in regional_total.columns:
            region_key = c
            break
    if region_key is None:
        raise KeyError("No regional key found in regional_total table")

    regional_active = regional_active.rename(columns={region_key: "region_key"}) if region_key in regional_active.columns else regional_active
    regional_total = regional_total.rename(columns={region_key: "region_key"})
    regional_def = regional_def.rename(columns={region_key: "region_key"}) if region_key in regional_def.columns else regional_def
    regional_by_tier = regional_by_tier.rename(columns={region_key: "region_key"}) if region_key in regional_by_tier.columns else regional_by_tier

    # pivot diesel by tier wide
    tier_wide = (
        regional_by_tier.pivot_table(
            index="region_key",
            columns="tier_assigned",
            values="annual_diesel_litres",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )
    tier_wide.columns = [
        "region_key" if c == "region_key" else f"diesel_litres_{str(c).lower().replace(' ', '_').replace('/', '_')}"
        for c in tier_wide.columns
    ]

    master = regional_total.merge(regional_active, on="region_key", how="left")
    master = master.merge(regional_def, on="region_key", how="left")
    master = master.merge(tier_wide, on="region_key", how="left")

    national_diesel_ml = float(project_summary.loc[0, "project_national_diesel_ml"])
    national_diesel_l = national_diesel_ml * 1_000_000
    national_fleet = float(project_summary.loc[0, "project_active_licensed_weighted_fleet"])
    national_def_central_ml = float(project_summary.loc[0, "def_central_ml"])
    national_def_central_l = national_def_central_ml * 1_000_000

    master["regional_active_licensed_count"] = pd.to_numeric(master["active_licensed_count_geo_cohort"], errors="coerce")
    master["regional_diesel_litres"] = pd.to_numeric(master["annual_diesel_litres"], errors="coerce")
    master["regional_diesel_ml"] = master["regional_diesel_litres"] / 1_000_000
    master["regional_scr_diesel_litres"] = pd.to_numeric(master["scr_diesel_litres"], errors="coerce")
    master["regional_scr_diesel_ml"] = master["regional_scr_diesel_litres"] / 1_000_000
    master["regional_def_central_ml"] = pd.to_numeric(master["def_central_litres"], errors="coerce") / 1_000_000

    master["share_of_national_fleet"] = master["regional_active_licensed_count"] / national_fleet
    master["share_of_national_diesel"] = master["regional_diesel_litres"] / national_diesel_l
    master["share_of_national_def_central"] = pd.to_numeric(master["def_central_litres"], errors="coerce") / national_def_central_l

    master = master.sort_values("regional_diesel_litres", ascending=False)

    write_csv(master, "outputs/tables/regional_master_table.csv")

    print("Regional master table created.")
    print(master.head(15).to_string(index=False))

if __name__ == "__main__":
    main()
