from __future__ import annotations
from pathlib import Path
import pandas as pd
from scripts.common import root_path, write_csv

START_YEAR = 2026
END_YEAR = 2030
TIERS = ["Unregulated", "Tier 1", "Tier 2", "Tier 3", "Tier 4i", "Tier 4f", "Stage V"]
SCR_TIERS = {"Tier 4f", "Stage V"}

def main() -> None:
    baseline_tier = pd.read_csv(root_path("outputs/tables/national_diesel_by_tier.csv")).copy()
    scenario_tier = pd.read_csv(root_path("outputs/scenarios/scenario_national_by_tier.csv")).copy()
    internal = pd.read_csv(root_path("data/staging/internal_tier_summary.csv")).copy()

    regional_base = pd.read_csv(root_path("outputs/tables/regional_master_table.csv")).copy()
    regional_scen = pd.read_csv(root_path("outputs/scenarios/scenario_regional_summary.csv")).copy()

    baseline_tier.columns = [c.strip().lower() for c in baseline_tier.columns]
    scenario_tier.columns = [c.strip().lower() for c in scenario_tier.columns]
    internal.columns = [c.strip().lower() for c in internal.columns]
    regional_base.columns = [c.strip().lower() for c in regional_base.columns]
    regional_scen.columns = [c.strip().lower() for c in regional_scen.columns]

    internal["count"] = pd.to_numeric(internal["count"], errors="coerce")
    internal["fuel_ml"] = pd.to_numeric(internal["fuel_ml"], errors="coerce")
    internal["litres_per_tractor"] = (internal["fuel_ml"] * 1_000_000) / internal["count"]

    lpt = (
        internal[["tier", "litres_per_tractor"]]
        .rename(columns={"tier": "tier_assigned"})
        .set_index("tier_assigned")
        .reindex(TIERS)
    )

    baseline_counts = (
        baseline_tier[["tier_assigned", "weighted_tractor_count"]]
        .copy()
        .set_index("tier_assigned")
        .reindex(TIERS)
        .fillna(0)
    )
    baseline_counts["weighted_tractor_count"] = pd.to_numeric(baseline_counts["weighted_tractor_count"], errors="coerce").fillna(0)

    if "annual_diesel_ml" not in baseline_tier.columns:
        baseline_tier["annual_diesel_ml"] = pd.to_numeric(baseline_tier["annual_diesel_litres"], errors="coerce") / 1_000_000

    # Regional baseline
    baseline_reg = regional_base[[
        "region_key",
        "regional_active_licensed_count",
        "regional_diesel_ml",
        "regional_scr_diesel_ml",
        "regional_def_central_ml"
    ]].copy()

    # Detect regional key in scenario table
    region_key_candidates = ["tla", "postcode", "geo_unit", "region_key"]
    scen_region_key = None
    for c in region_key_candidates:
        if c in regional_scen.columns:
            scen_region_key = c
            break
    if scen_region_key is None:
        raise KeyError("No region key found in outputs/scenarios/scenario_regional_summary.csv")

    if scen_region_key != "region_key":
        regional_scen = regional_scen.rename(columns={scen_region_key: "region_key"})

    national_rows = []
    national_tier_rows = []
    regional_rows = []

    scenario_names = scenario_tier["scenario_name"].dropna().unique().tolist()

    for scenario_name in scenario_names:
        target_counts = (
            scenario_tier.loc[scenario_tier["scenario_name"] == scenario_name, ["tier_assigned", "weighted_tractor_count"]]
            .copy()
            .set_index("tier_assigned")
            .reindex(TIERS)
            .fillna(0)
        )
        target_counts["weighted_tractor_count"] = pd.to_numeric(target_counts["weighted_tractor_count"], errors="coerce").fillna(0)

        target_reg = regional_scen.loc[regional_scen["scenario_name"] == scenario_name].copy()

        # ensure required ml columns exist
        if "regional_diesel_ml" not in target_reg.columns:
            target_reg["regional_diesel_ml"] = pd.to_numeric(target_reg["annual_diesel_litres"], errors="coerce") / 1_000_000
        if "regional_scr_diesel_ml" not in target_reg.columns:
            target_reg["regional_scr_diesel_ml"] = pd.to_numeric(target_reg["scr_diesel_litres"], errors="coerce") / 1_000_000
        if "def_central_ml" not in target_reg.columns:
            target_reg["def_central_ml"] = (pd.to_numeric(target_reg["scr_diesel_litres"], errors="coerce") * 0.04) / 1_000_000

        target_reg = target_reg[[
            "region_key",
            "weighted_tractor_count",
            "regional_diesel_ml",
            "regional_scr_diesel_ml",
            "def_central_ml"
        ]].copy().rename(columns={
            "weighted_tractor_count": "regional_active_licensed_count"
        })

        reg_merge = baseline_reg.merge(
            target_reg,
            on="region_key",
            how="outer",
            suffixes=("_base", "_target")
        )

        for col in [
            "regional_active_licensed_count_base",
            "regional_diesel_ml_base",
            "regional_scr_diesel_ml_base",
            "regional_def_central_ml_base",
            "regional_active_licensed_count_target",
            "regional_diesel_ml_target",
            "regional_scr_diesel_ml_target",
            "def_central_ml_target"
        ]:
            if col in reg_merge.columns:
                reg_merge[col] = pd.to_numeric(reg_merge[col], errors="coerce").fillna(0)

        years = list(range(START_YEAR, END_YEAR + 1))
        for year in years:
            alpha = 0 if END_YEAR == START_YEAR else (year - START_YEAR) / (END_YEAR - START_YEAR)

            # National tier interpolation
            tier_counts = baseline_counts["weighted_tractor_count"] + alpha * (
                target_counts["weighted_tractor_count"] - baseline_counts["weighted_tractor_count"]
            )

            tier_diesel_l = tier_counts * lpt["litres_per_tractor"]

            national_total = float(tier_counts.sum())
            national_diesel_ml = float(tier_diesel_l.sum() / 1_000_000)

            scr_mask = [t in SCR_TIERS for t in TIERS]
            national_scr_count = float(tier_counts.loc[scr_mask].sum())
            national_scr_diesel_ml = float(tier_diesel_l.loc[scr_mask].sum() / 1_000_000)

            national_rows.append({
                "scenario_name": scenario_name,
                "year": year,
                "national_weighted_fleet": national_total,
                "national_diesel_ml": national_diesel_ml,
                "national_scr_tractor_count": national_scr_count,
                "national_scr_diesel_ml": national_scr_diesel_ml,
                "def_low_ml": national_scr_diesel_ml * 0.03,
                "def_central_ml": national_scr_diesel_ml * 0.04,
                "def_high_ml": national_scr_diesel_ml * 0.05
            })

            for tier in TIERS:
                national_tier_rows.append({
                    "scenario_name": scenario_name,
                    "year": year,
                    "tier_assigned": tier,
                    "weighted_tractor_count": float(tier_counts.loc[tier]),
                    "annual_diesel_ml": float(tier_diesel_l.loc[tier] / 1_000_000)
                })

            # Regional interpolation
            reg_tmp = reg_merge.copy()
            reg_tmp["regional_active_licensed_count"] = reg_tmp["regional_active_licensed_count_base"] + alpha * (
                reg_tmp["regional_active_licensed_count_target"] - reg_tmp["regional_active_licensed_count_base"]
            )
            reg_tmp["regional_diesel_ml"] = reg_tmp["regional_diesel_ml_base"] + alpha * (
                reg_tmp["regional_diesel_ml_target"] - reg_tmp["regional_diesel_ml_base"]
            )
            reg_tmp["regional_scr_diesel_ml"] = reg_tmp["regional_scr_diesel_ml_base"] + alpha * (
                reg_tmp["regional_scr_diesel_ml_target"] - reg_tmp["regional_scr_diesel_ml_base"]
            )
            reg_tmp["regional_def_central_ml"] = reg_tmp["regional_def_central_ml_base"] + alpha * (
                reg_tmp["def_central_ml_target"] - reg_tmp["regional_def_central_ml_base"]
            )
            reg_tmp["scenario_name"] = scenario_name
            reg_tmp["year"] = year

            keep = reg_tmp[[
                "region_key",
                "scenario_name",
                "year",
                "regional_active_licensed_count",
                "regional_diesel_ml",
                "regional_scr_diesel_ml",
                "regional_def_central_ml"
            ]].copy()

            keep["def_low_ml"] = keep["regional_scr_diesel_ml"] * 0.03
            keep["def_high_ml"] = keep["regional_scr_diesel_ml"] * 0.05

            regional_rows.append(keep)

    national_annual = pd.DataFrame(national_rows)
    national_by_tier_annual = pd.DataFrame(national_tier_rows)
    regional_annual = pd.concat(regional_rows, ignore_index=True)

    out_dir = root_path("outputs/forecast")
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(national_annual, "outputs/forecast/forecast_national_annual.csv")
    write_csv(national_by_tier_annual, "outputs/forecast/forecast_national_by_tier_annual.csv")
    write_csv(regional_annual, "outputs/forecast/forecast_regional_annual.csv")

    forecast_2030 = regional_annual.loc[regional_annual["year"] == END_YEAR].copy()
    top_def_2030 = (
        forecast_2030.sort_values(["scenario_name", "regional_def_central_ml"], ascending=[True, False])
        .groupby("scenario_name")
        .head(15)
        .copy()
    )
    write_csv(top_def_2030, "outputs/forecast/forecast_top15_regional_def_2030.csv")

    endpoint_summary = national_annual.loc[national_annual["year"] == END_YEAR].copy()
    print("Forecast national annual endpoints:")
    print(endpoint_summary.to_string(index=False))

if __name__ == "__main__":
    main()
