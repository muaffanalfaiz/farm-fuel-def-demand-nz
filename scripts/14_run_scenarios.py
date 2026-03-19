from __future__ import annotations
import pandas as pd
from pathlib import Path
from scripts.common import root_path, write_csv

TIERS = ["Unregulated", "Tier 1", "Tier 2", "Tier 3", "Tier 4i", "Tier 4f", "Stage V"]
SCR_TIERS = {"Tier 4f", "Stage V"}

SCENARIOS = {
    "baseline_current_structure": {
        "Unregulated": {"Unregulated": 1.00},
        "Tier 1": {"Tier 1": 1.00},
        "Tier 2": {"Tier 2": 1.00},
        "Tier 3": {"Tier 3": 1.00},
        "Tier 4i": {"Tier 4i": 1.00},
        "Tier 4f": {"Tier 4f": 1.00},
        "Stage V": {"Stage V": 1.00},
    },
    "moderate_modernization": {
        "Unregulated": {"Unregulated": 0.85, "Tier 1": 0.15},
        "Tier 1": {"Tier 1": 0.80, "Tier 2": 0.20},
        "Tier 2": {"Tier 2": 0.75, "Tier 3": 0.25},
        "Tier 3": {"Tier 3": 0.80, "Tier 4i": 0.15, "Tier 4f": 0.05},
        "Tier 4i": {"Tier 4i": 0.80, "Tier 4f": 0.20},
        "Tier 4f": {"Tier 4f": 0.85, "Stage V": 0.15},
        "Stage V": {"Stage V": 1.00},
    },
    "accelerated_modernization": {
        "Unregulated": {"Unregulated": 0.70, "Tier 1": 0.30},
        "Tier 1": {"Tier 1": 0.60, "Tier 2": 0.40},
        "Tier 2": {"Tier 2": 0.60, "Tier 3": 0.40},
        "Tier 3": {"Tier 3": 0.65, "Tier 4i": 0.25, "Tier 4f": 0.10},
        "Tier 4i": {"Tier 4i": 0.60, "Tier 4f": 0.40},
        "Tier 4f": {"Tier 4f": 0.70, "Stage V": 0.30},
        "Stage V": {"Stage V": 1.00},
    },
    "scr_push": {
        "Unregulated": {"Unregulated": 0.95, "Tier 1": 0.05},
        "Tier 1": {"Tier 1": 0.90, "Tier 2": 0.10},
        "Tier 2": {"Tier 2": 0.85, "Tier 3": 0.15},
        "Tier 3": {"Tier 3": 0.85, "Tier 4i": 0.10, "Tier 4f": 0.05},
        "Tier 4i": {"Tier 4i": 0.50, "Tier 4f": 0.50},
        "Tier 4f": {"Tier 4f": 0.60, "Stage V": 0.40},
        "Stage V": {"Stage V": 1.00},
    },
    "delayed_replacement": {
        "Unregulated": {"Unregulated": 0.95, "Tier 1": 0.05},
        "Tier 1": {"Tier 1": 0.90, "Tier 2": 0.10},
        "Tier 2": {"Tier 2": 0.85, "Tier 3": 0.15},
        "Tier 3": {"Tier 3": 0.95, "Tier 4i": 0.05},
        "Tier 4i": {"Tier 4i": 0.90, "Tier 4f": 0.10},
        "Tier 4f": {"Tier 4f": 0.95, "Stage V": 0.05},
        "Stage V": {"Stage V": 1.00},
    },
}

def validate_transition_dict() -> None:
    for scen_name, scen in SCENARIOS.items():
        missing = set(TIERS) - set(scen.keys())
        if missing:
            raise ValueError(f"{scen_name} missing source tiers: {missing}")
        for src, mapping in scen.items():
            total = sum(mapping.values())
            if abs(total - 1.0) > 1e-9:
                raise ValueError(f"{scen_name} source tier {src} does not sum to 1.0 (got {total})")
            bad = set(mapping.keys()) - set(TIERS)
            if bad:
                raise ValueError(f"{scen_name} source tier {src} has invalid destination tiers: {bad}")

def build_transition_long(scenario_name: str) -> pd.DataFrame:
    rows = []
    for src, mapping in SCENARIOS[scenario_name].items():
        for dst, share in mapping.items():
            rows.append({
                "source_tier": src,
                "dest_tier": dst,
                "transition_share": share
            })
    return pd.DataFrame(rows)

def main() -> None:
    validate_transition_dict()

    fleet = pd.read_parquet(root_path("data/marts/fleet_with_tiers.parquet")).copy()
    internal = pd.read_csv(root_path("data/staging/internal_tier_summary.csv")).copy()

    fleet.columns = [c.strip().lower() for c in fleet.columns]
    internal.columns = [c.strip().lower() for c in internal.columns]

    group_col = "tla" if "tla" in fleet.columns else ("postcode" if "postcode" in fleet.columns else "geo_unit")
    if group_col == "geo_unit":
        fleet[group_col] = "National"

    baseline = (
        fleet.groupby([group_col, "tier_assigned"], dropna=False)["weighted_tractor_count"]
        .sum()
        .reset_index()
        .rename(columns={"tier_assigned": "source_tier"})
    )

    internal["count"] = pd.to_numeric(internal["count"], errors="coerce")
    internal["fuel_ml"] = pd.to_numeric(internal["fuel_ml"], errors="coerce")
    internal["litres_per_tractor"] = (internal["fuel_ml"] * 1_000_000) / internal["count"]
    tier_lpt = internal[["tier", "litres_per_tractor"]].rename(columns={"tier": "tier_assigned"})

    scenario_regional_frames = []
    scenario_national_frames = []
    scenario_national_tier_frames = []

    for scenario_name in SCENARIOS:
        trans = build_transition_long(scenario_name)

        scen = baseline.merge(trans, on="source_tier", how="left")
        scen["scenario_weighted_tractor_count"] = scen["weighted_tractor_count"] * scen["transition_share"]

        scen = (
            scen.groupby([group_col, "dest_tier"], dropna=False)["scenario_weighted_tractor_count"]
            .sum()
            .reset_index()
            .rename(columns={"dest_tier": "tier_assigned"})
        )

        scen = scen.merge(tier_lpt, on="tier_assigned", how="left")
        scen["annual_diesel_litres"] = scen["scenario_weighted_tractor_count"] * scen["litres_per_tractor"]
        scen["scenario_name"] = scenario_name
        scen["def_required_flag"] = scen["tier_assigned"].isin(SCR_TIERS).astype(int)

        regional = (
            scen.groupby([group_col], dropna=False)
            .agg(
                weighted_tractor_count=("scenario_weighted_tractor_count", "sum"),
                annual_diesel_litres=("annual_diesel_litres", "sum")
            )
            .reset_index()
        )

        regional_scr = (
            scen.loc[scen["def_required_flag"] == 1]
            .groupby([group_col], dropna=False)
            .agg(
                weighted_scr_tractor_count=("scenario_weighted_tractor_count", "sum"),
                scr_diesel_litres=("annual_diesel_litres", "sum")
            )
            .reset_index()
        )

        regional = regional.merge(regional_scr, on=group_col, how="left")
        regional["weighted_scr_tractor_count"] = regional["weighted_scr_tractor_count"].fillna(0)
        regional["scr_diesel_litres"] = regional["scr_diesel_litres"].fillna(0)

        regional["regional_diesel_ml"] = regional["annual_diesel_litres"] / 1_000_000
        regional["regional_scr_diesel_ml"] = regional["scr_diesel_litres"] / 1_000_000
        regional["def_low_ml"] = (regional["scr_diesel_litres"] * 0.03) / 1_000_000
        regional["def_central_ml"] = (regional["scr_diesel_litres"] * 0.04) / 1_000_000
        regional["def_high_ml"] = (regional["scr_diesel_litres"] * 0.05) / 1_000_000
        regional["scenario_name"] = scenario_name

        national_total = float(regional["weighted_tractor_count"].sum())
        national_diesel_ml = float(regional["regional_diesel_ml"].sum())
        national_scr_count = float(regional["weighted_scr_tractor_count"].sum())
        national_scr_diesel_ml = float(regional["regional_scr_diesel_ml"].sum())

        national_by_tier = (
            scen.groupby("tier_assigned", dropna=False)
            .agg(
                weighted_tractor_count=("scenario_weighted_tractor_count", "sum"),
                annual_diesel_litres=("annual_diesel_litres", "sum")
            )
            .reset_index()
        )
        national_by_tier["annual_diesel_ml"] = national_by_tier["annual_diesel_litres"] / 1_000_000
        national_by_tier["scenario_name"] = scenario_name

        stagev_count = float(national_by_tier.loc[national_by_tier["tier_assigned"] == "Stage V", "weighted_tractor_count"].sum())
        tier4f_count = float(national_by_tier.loc[national_by_tier["tier_assigned"] == "Tier 4f", "weighted_tractor_count"].sum())
        modern_count = float(national_by_tier.loc[national_by_tier["tier_assigned"].isin(["Tier 4i", "Tier 4f", "Stage V"]), "weighted_tractor_count"].sum())

        national_summary = pd.DataFrame([{
            "scenario_name": scenario_name,
            "national_weighted_fleet": national_total,
            "national_diesel_ml": national_diesel_ml,
            "national_scr_tractor_count": national_scr_count,
            "national_scr_diesel_ml": national_scr_diesel_ml,
            "def_low_ml": national_scr_diesel_ml * 0.03,
            "def_central_ml": national_scr_diesel_ml * 0.04,
            "def_high_ml": national_scr_diesel_ml * 0.05,
            "tier4f_count": tier4f_count,
            "stagev_count": stagev_count,
            "modern_tiers_count": modern_count,
            "modern_tiers_share_pct": (modern_count / national_total) * 100 if national_total else 0,
            "scr_share_pct": (national_scr_count / national_total) * 100 if national_total else 0,
        }])

        scenario_regional_frames.append(regional)
        scenario_national_frames.append(national_summary)
        scenario_national_tier_frames.append(national_by_tier)

    regional_all = pd.concat(scenario_regional_frames, ignore_index=True)
    national_all = pd.concat(scenario_national_frames, ignore_index=True)
    national_tier_all = pd.concat(scenario_national_tier_frames, ignore_index=True)

    out_dir = root_path("outputs/scenarios")
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(regional_all, "outputs/scenarios/scenario_regional_summary.csv")
    write_csv(national_all, "outputs/scenarios/scenario_national_summary.csv")
    write_csv(national_tier_all, "outputs/scenarios/scenario_national_by_tier.csv")

    print("Scenario national summary:")
    print(national_all.to_string(index=False))

if __name__ == "__main__":
    main()
