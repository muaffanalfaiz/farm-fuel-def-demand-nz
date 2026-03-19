from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

def p(rel: str) -> Path:
    return ROOT / rel

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_barh(df, label_col, value_col, title, xlabel, outpath, top_n=None):
    data = df.copy()
    if top_n is not None:
        data = data.head(top_n).copy()
    data = data.sort_values(value_col, ascending=True)

    plt.figure(figsize=(10, max(5, 0.38 * len(data))))
    plt.barh(data[label_col].astype(str), data[value_col])
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()

def save_bar(df, label_col, value_col, title, ylabel, outpath):
    data = df.copy()
    plt.figure(figsize=(10, 6))
    plt.bar(data[label_col].astype(str), data[value_col])
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()

def main() -> None:
    fig_dir = p("outputs/figures")
    ensure_dir(fig_dir)

    project = pd.read_csv(p("outputs/tables/project_summary.csv"))
    tiers = pd.read_csv(p("outputs/tables/national_diesel_by_tier.csv"))
    tier_counts = pd.read_csv(p("outputs/tables/tier_counts_assigned_weighted.csv"))
    regional = pd.read_csv(p("outputs/tables/regional_master_table.csv"))
    scen_nat = pd.read_csv(p("outputs/scenarios/scenario_national_summary.csv"))
    scen_cmp = pd.read_csv(p("outputs/scenarios/scenario_national_compare.csv"))
    scen_reg = pd.read_csv(p("outputs/scenarios/scenario_regional_compare.csv"))

    tiers.columns = [c.strip().lower() for c in tiers.columns]
    tier_counts.columns = [c.strip().lower() for c in tier_counts.columns]
    regional.columns = [c.strip().lower() for c in regional.columns]
    scen_nat.columns = [c.strip().lower() for c in scen_nat.columns]
    scen_cmp.columns = [c.strip().lower() for c in scen_cmp.columns]
    scen_reg.columns = [c.strip().lower() for c in scen_reg.columns]

    if "annual_diesel_ml" not in tiers.columns:
        tiers["annual_diesel_ml"] = pd.to_numeric(tiers["annual_diesel_litres"], errors="coerce") / 1_000_000

    figure_rows = []

    # 1 baseline diesel by tier
    out = fig_dir / "01_baseline_diesel_by_tier.png"
    save_barh(
        tiers.sort_values("annual_diesel_ml", ascending=False),
        "tier_assigned",
        "annual_diesel_ml",
        "Baseline National Diesel by Tier",
        "Diesel demand (ML)",
        out,
    )
    figure_rows.append({"figure_file": out.name, "description": "Baseline national diesel demand by emission tier"})

    # 2 baseline weighted fleet by tier
    out = fig_dir / "02_baseline_weighted_fleet_by_tier.png"
    save_barh(
        tier_counts.sort_values("weighted_tractor_count", ascending=False),
        "tier_assigned",
        "weighted_tractor_count",
        "Baseline Weighted Fleet by Tier",
        "Weighted tractor count",
        out,
    )
    figure_rows.append({"figure_file": out.name, "description": "Baseline weighted active licensed fleet by tier"})

    # 3 scenario diesel comparison
    out = fig_dir / "03_scenario_national_diesel_ml.png"
    save_bar(
        scen_nat.sort_values("national_diesel_ml", ascending=False),
        "scenario_name",
        "national_diesel_ml",
        "Scenario Comparison: National Diesel",
        "National diesel (ML)",
        out,
    )
    figure_rows.append({"figure_file": out.name, "description": "Scenario comparison of national diesel demand"})

    # 4 scenario DEF comparison
    out = fig_dir / "04_scenario_def_central_ml.png"
    save_bar(
        scen_nat.sort_values("def_central_ml", ascending=False),
        "scenario_name",
        "def_central_ml",
        "Scenario Comparison: Central DEF Demand",
        "Central DEF demand (ML)",
        out,
    )
    figure_rows.append({"figure_file": out.name, "description": "Scenario comparison of central DEF demand"})

    # 5 scenario SCR share
    out = fig_dir / "05_scenario_scr_share_pct.png"
    save_bar(
        scen_nat.sort_values("scr_share_pct", ascending=False),
        "scenario_name",
        "scr_share_pct",
        "Scenario Comparison: SCR Share of Fleet",
        "SCR share (%)",
        out,
    )
    figure_rows.append({"figure_file": out.name, "description": "Scenario comparison of SCR fleet share"})

    # 6 top regional diesel
    out = fig_dir / "06_top15_regional_diesel_ml.png"
    save_barh(
        regional.sort_values("regional_diesel_ml", ascending=False),
        "region_key",
        "regional_diesel_ml",
        "Top 15 Regions by Baseline Diesel Demand",
        "Regional diesel demand (ML)",
        out,
        top_n=15,
    )
    figure_rows.append({"figure_file": out.name, "description": "Top 15 regions by baseline diesel demand"})

    # 7 top regional DEF
    out = fig_dir / "07_top15_regional_def_central_ml.png"
    save_barh(
        regional.sort_values("regional_def_central_ml", ascending=False),
        "region_key",
        "regional_def_central_ml",
        "Top 15 Regions by Baseline Central DEF Demand",
        "Regional central DEF demand (ML)",
        out,
        top_n=15,
    )
    figure_rows.append({"figure_file": out.name, "description": "Top 15 regions by baseline central DEF demand"})

    # 8 top regional DEF gains - SCR push
    scr_push = (
        scen_reg.loc[scen_reg["scenario_name"] == "scr_push"]
        .sort_values("delta_def_central_ml_vs_baseline", ascending=False)
        .copy()
    )
    region_key = "tla" if "tla" in scr_push.columns else ("postcode" if "postcode" in scr_push.columns else "geo_unit")
    out = fig_dir / "08_top15_def_gains_scr_push.png"
    save_barh(
        scr_push,
        region_key,
        "delta_def_central_ml_vs_baseline",
        "Top 15 Regional DEF Gains vs Baseline: SCR Push",
        "Increase in central DEF demand (ML)",
        out,
        top_n=15,
    )
    figure_rows.append({"figure_file": out.name, "description": "Top 15 regional DEF gains under SCR push scenario"})

    # 9 top regional DEF gains - accelerated modernization
    accel = (
        scen_reg.loc[scen_reg["scenario_name"] == "accelerated_modernization"]
        .sort_values("delta_def_central_ml_vs_baseline", ascending=False)
        .copy()
    )
    out = fig_dir / "09_top15_def_gains_accelerated_modernization.png"
    save_barh(
        accel,
        region_key,
        "delta_def_central_ml_vs_baseline",
        "Top 15 Regional DEF Gains vs Baseline: Accelerated Modernization",
        "Increase in central DEF demand (ML)",
        out,
        top_n=15,
    )
    figure_rows.append({"figure_file": out.name, "description": "Top 15 regional DEF gains under accelerated modernization"})

    pd.DataFrame(figure_rows).to_csv(p("outputs/figures/figure_manifest.csv"), index=False)

    print("Figures created:")
    for row in figure_rows:
        print(f"- {row['figure_file']}: {row['description']}")

if __name__ == "__main__":
    main()
